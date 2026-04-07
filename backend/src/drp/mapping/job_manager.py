"""映射生成任务管理器：异步处理大文件，Redis 存储进度。

流程：
1. 前端提交 DDL/CSV → 后端立即返回 job_id
2. 后台 asyncio.Task 解析 + 分批调用 LLM
3. 进度写入 Redis（ds:mapping_job:{job_id}）
4. 前端轮询 GET /mappings/jobs/{job_id} 获取进度
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from drp.config import settings

logger = logging.getLogger(__name__)

JOB_KEY_PREFIX = "ds:mapping_job"
JOB_TTL = 3600  # 任务状态保留 1 小时


@dataclass
class MappingJobStatus:
    """映射任务状态。"""
    job_id: str
    status: str = "pending"  # pending / parsing / generating / completed / failed
    total_tables: int = 0
    processed_tables: int = 0
    total_fields: int = 0
    processed_fields: int = 0
    current_table: str = ""
    error: str | None = None
    result_count: int = 0
    started_at: str = ""
    finished_at: str | None = None

    @property
    def progress(self) -> float:
        if self.total_tables == 0:
            return 0.0
        return round(self.processed_tables / self.total_tables * 100, 1)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "total_tables": self.total_tables,
            "processed_tables": self.processed_tables,
            "total_fields": self.total_fields,
            "processed_fields": self.processed_fields,
            "current_table": self.current_table,
            "error": self.error,
            "result_count": self.result_count,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


async def _get_redis():
    import redis.asyncio as aioredis
    return aioredis.from_url(settings.redis_url)


async def save_job_status(job_id: str, status: MappingJobStatus) -> None:
    """保存任务状态到 Redis。"""
    try:
        r = await _get_redis()
        try:
            key = f"{JOB_KEY_PREFIX}:{job_id}"
            await r.set(key, json.dumps(status.to_dict()), ex=JOB_TTL)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("保存任务状态失败: %s", job_id, exc_info=True)


async def get_job_status(job_id: str) -> dict | None:
    """从 Redis 获取任务状态。"""
    try:
        r = await _get_redis()
        try:
            key = f"{JOB_KEY_PREFIX}:{job_id}"
            raw = await r.get(key)
            if raw:
                return json.loads(raw)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("获取任务状态失败: %s", job_id, exc_info=True)
    return None


async def run_mapping_job(
    job_id: str,
    content: str,
    fmt: str,
    tenant_id: str,
    user_id: str,
    table_name_filter: str | None = None,
) -> None:
    """后台执行映射生成任务。

    解析 DDL/CSV → 分批调用 LLM → 持久化结果 → 更新进度。
    """
    from drp.mapping.ddl_parser import parse_ddl
    from drp.mapping.csv_parser import parse_csv
    from drp.mapping.llm_service import generate_mapping_suggestions
    from drp.mapping.models import MappingRepository, compute_ddl_hash
    from drp.db.session import _session_factory

    status = MappingJobStatus(
        job_id=job_id,
        status="parsing",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    await save_job_status(job_id, status)

    try:
        # 1. 解析
        if fmt == "csv":
            tables = parse_csv(content)
        else:
            tables = parse_ddl(content)

        if not tables:
            status.status = "failed"
            status.error = "解析失败，未找到有效表定义"
            await save_job_status(job_id, status)
            return

        if table_name_filter:
            tables = [t for t in tables if t.name.lower() == table_name_filter.lower()]
            if not tables:
                status.status = "failed"
                status.error = f"未找到表: {table_name_filter}"
                await save_job_status(job_id, status)
                return

        status.total_tables = len(tables)
        status.total_fields = sum(len(t.columns) for t in tables)
        status.status = "generating"
        await save_job_status(job_id, status)

        # 2. 分批调用 LLM
        ddl_hash = compute_ddl_hash(content)
        repo = MappingRepository()
        all_saved = []

        async with _session_factory() as session:
            history = await repo.get_approved_for_history(session, uuid.UUID(tenant_id))

            for i, table in enumerate(tables):
                status.current_table = table.name
                status.processed_tables = i
                await save_job_status(job_id, status)

                try:
                    suggestions = await generate_mapping_suggestions(table, history=history)
                except Exception as exc:
                    logger.error("LLM 调用失败: 表=%s, 错误=%s", table.name, exc)
                    # 单表失败不中断整个任务，跳过继续
                    status.processed_fields += len(table.columns)
                    continue

                # 持久化
                suggestion_dicts = [
                    {
                        "source_table": s.source_table,
                        "source_field": s.source_field,
                        "target_property": s.target_property,
                        "transform_rule": s.transform_rule,
                        "confidence": s.confidence,
                        "auto_approved": s.auto_approved,
                    }
                    for s in suggestions
                ]
                saved = await repo.upsert_mappings(
                    session, uuid.UUID(tenant_id), ddl_hash, suggestion_dicts
                )
                all_saved.extend(saved)
                status.processed_fields += len(table.columns)
                await session.commit()

            status.processed_tables = len(tables)
            status.result_count = len(all_saved)

        # 3. 完成
        status.status = "completed"
        status.finished_at = datetime.now(timezone.utc).isoformat()
        await save_job_status(job_id, status)
        logger.info(
            "[映射任务完成] job=%s 表数=%d 映射数=%d",
            job_id, len(tables), len(all_saved),
        )

    except Exception as exc:
        status.status = "failed"
        status.error = str(exc)
        status.finished_at = datetime.now(timezone.utc).isoformat()
        await save_job_status(job_id, status)
        logger.error("[映射任务失败] job=%s 错误=%s", job_id, exc, exc_info=True)
