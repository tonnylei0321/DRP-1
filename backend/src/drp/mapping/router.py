"""映射 API 路由。"""
import asyncio
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.schemas import TokenPayload
from drp.db.session import get_session
from drp.mapping.ddl_parser import parse_ddl
from drp.mapping.csv_parser import parse_csv
from drp.mapping.llm_service import generate_mapping_suggestions
from drp.mapping.models import MappingRepository, compute_ddl_hash
from drp.mapping.schemas import (
    BatchApproveRequest,
    BatchApproveResponse,
    GenerateMappingRequest,
    GenerateMappingResponse,
    MappingItemResponse,
    RejectMappingRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mappings", tags=["语义映射"])
_repo = MappingRepository()

# DDL 注入防护：表名/列名白名单
_SAFE_NAME_RE = re.compile(r'^[a-zA-Z0-9_]+$')


@router.get(
    "",
    response_model=list[MappingItemResponse],
    dependencies=[Depends(require_permission("mapping:read"))],
)
async def list_mappings(
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> list[MappingItemResponse]:
    """列出当前租户的所有映射规范。"""
    from sqlalchemy import select as sa_select
    from drp.mapping.models import MappingSpec as MappingSpecModel
    q = sa_select(MappingSpecModel).order_by(MappingSpecModel.created_at.desc())
    if current_user.tenant_id:
        q = q.where(MappingSpecModel.tenant_id == uuid.UUID(current_user.tenant_id))
    result = await session.execute(q)
    return [MappingItemResponse.model_validate(m) for m in result.scalars()]


@router.post(
    "/generate",
    response_model=GenerateMappingResponse,
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(require_permission("mapping:read"))],
)
async def generate_mapping(
    data: GenerateMappingRequest,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> GenerateMappingResponse:
    """解析 DDL，调用 LLM 生成字段映射建议并持久化。"""
    # 获取租户 ID，无 tenant_id 时使用默认租户
    tenant_id_str = current_user.tenant_id
    if not tenant_id_str:
        from sqlalchemy import text as sa_text
        result = await session.execute(sa_text("SELECT id FROM tenant LIMIT 1"))
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="系统中无可用租户")
        tenant_id_str = str(row[0])

    # 内容大小限制：DDL 最大 5MB，CSV 最大 200MB
    content_size = len(data.ddl.encode("utf-8"))
    if data.format == "csv":
        if content_size > 209_715_200:
            raise HTTPException(status_code=422, detail="CSV 内容超过 200MB 限制")
    else:
        if content_size > 5_242_880:
            raise HTTPException(status_code=422, detail="DDL 内容超过 5MB 限制")

    tenant_id = uuid.UUID(tenant_id_str)
    ddl_hash = compute_ddl_hash(data.ddl)

    # 解析 DDL 或 CSV
    if data.format == "csv":
        try:
            tables = parse_csv(data.ddl)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    else:
        tables = parse_ddl(data.ddl)
    if not tables:
        raise HTTPException(status_code=422, detail="解析失败，未找到有效表定义")

    if data.table_name:
        tables = [t for t in tables if t.name.lower() == data.table_name.lower()]
        if not tables:
            raise HTTPException(status_code=404, detail=f"未找到表: {data.table_name}")

    # 表名/列名白名单校验
    for table in tables:
        if not _SAFE_NAME_RE.match(table.name):
            raise HTTPException(status_code=422, detail=f"表名包含非法字符: {table.name}")
        for col in table.columns:
            if not _SAFE_NAME_RE.match(col.name):
                raise HTTPException(status_code=422, detail=f"列名包含非法字符: {table.name}.{col.name}")

    # 获取历史映射（置信度计算参考）
    history = await _repo.get_approved_for_history(session, tenant_id)

    # LLM 审计日志
    start_time = time.time()
    logger.info(
        "[LLM映射] 开始: 操作人=%s 租户=%s 表数=%d",
        current_user.sub, current_user.tenant_id, len(tables),
    )

    # 调用 LLM 生成建议
    all_suggestions = []
    for table in tables:
        suggestions = await generate_mapping_suggestions(table, history=history)
        all_suggestions.extend(suggestions)

    elapsed = time.time() - start_time
    logger.info(
        "[LLM映射] 完成: 操作人=%s 租户=%s 表数=%d 字段数=%d 映射数=%d 耗时=%.1fs",
        current_user.sub, current_user.tenant_id, len(tables),
        sum(len(t.columns) for t in tables), len(all_suggestions), elapsed,
    )

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
        for s in all_suggestions
    ]
    saved = await _repo.upsert_mappings(session, tenant_id, ddl_hash, suggestion_dicts)
    await session.commit()

    items = [MappingItemResponse.model_validate(m) for m in saved]
    return GenerateMappingResponse(
        ddl_hash=ddl_hash,
        total=len(items),
        auto_approved=sum(1 for i in items if i.auto_approved),
        mappings=items,
    )


@router.get(
    "/export-yaml",
    dependencies=[Depends(require_permission("mapping:read"))],
)
async def export_mapping_yaml(
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
):
    """导出已审核通过的映射为 YAML。"""
    from drp.mapping.yaml_generator import generate_mapping_yaml_from_specs

    specs = await _repo.list_by_tenant(
        session, uuid.UUID(current_user.tenant_id), status="approved"
    )
    if not specs:
        raise HTTPException(status_code=404, detail="无已审核通过的映射记录")
    yaml_str = generate_mapping_yaml_from_specs(specs)
    return {"mapping_yaml": yaml_str}


@router.post(
    "/batch-approve",
    response_model=BatchApproveResponse,
    dependencies=[Depends(require_permission("mapping:approve"))],
)
async def batch_approve_mappings(
    data: BatchApproveRequest,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> BatchApproveResponse:
    """批量审核映射。"""
    pending = await _repo.list_by_tenant(
        session, uuid.UUID(current_user.tenant_id), status="pending"
    )
    total_pending = len(pending)

    approved_count = 0
    for m in pending:
        if approved_count >= data.max_count:
            break
        if data.mode == "all" or (
            data.mode == "threshold"
            and m.confidence is not None
            and m.confidence >= data.threshold
        ):
            m.status = "approved"
            m.approved_by = uuid.UUID(current_user.sub)
            m.approved_at = datetime.now(timezone.utc)
            approved_count += 1

    await session.commit()

    logger.info(
        "[批量审核] 操作人=%s 租户=%s 模式=%s 阈值=%s 审核数=%d 总待审=%d",
        current_user.sub, current_user.tenant_id, data.mode,
        data.threshold, approved_count, total_pending,
    )

    return BatchApproveResponse(
        approved_count=approved_count,
        skipped_count=total_pending - approved_count,
        total_pending=total_pending,
    )


@router.put(
    "/{mapping_id}/approve",
    response_model=MappingItemResponse,
    dependencies=[Depends(require_permission("mapping:approve"))],
)
async def approve_mapping(
    mapping_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> MappingItemResponse:
    """人工审批映射。"""
    mapping = await _repo.get_by_id(session, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="映射不存在")

    mapping.status = "approved"
    mapping.approved_by = uuid.UUID(current_user.sub)
    mapping.approved_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(mapping)
    return MappingItemResponse.model_validate(mapping)


@router.put(
    "/{mapping_id}/reject",
    response_model=MappingItemResponse,
    dependencies=[Depends(require_permission("mapping:approve"))],
)
async def reject_mapping(
    mapping_id: uuid.UUID,
    data: RejectMappingRequest,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> MappingItemResponse:
    """拒绝映射建议。"""
    mapping = await _repo.get_by_id(session, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="映射不存在")

    mapping.status = "rejected"
    mapping.approved_by = uuid.UUID(current_user.sub)
    mapping.approved_at = datetime.now(timezone.utc)

    # 持久化拒绝原因，过滤 HTML 标签防止存储型 XSS
    if data.reason:
        mapping.reject_reason = re.sub(r'<[^>]+>', '', data.reason)

    await session.commit()
    await session.refresh(mapping)
    return MappingItemResponse.model_validate(mapping)


# ─── 异步映射任务（大文件） ────────────────────────────────────────────────────


@router.post(
    "/generate-async",
    status_code=HTTPStatus.ACCEPTED,
    dependencies=[Depends(require_permission("mapping:read"))],
)
async def generate_mapping_async(
    data: GenerateMappingRequest,
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """异步生成映射建议（适用于大文件）。

    立即返回 job_id，后台异步处理。
    前端通过 GET /mappings/jobs/{job_id} 轮询进度。
    """
    from drp.mapping.job_manager import run_mapping_job

    # 获取租户 ID，无 tenant_id 时使用默认租户
    tenant_id_str = current_user.tenant_id
    if not tenant_id_str:
        from sqlalchemy import text as sa_text
        result = await session.execute(sa_text("SELECT id FROM tenant LIMIT 1"))
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="系统中无可用租户")
        tenant_id_str = str(row[0])

    # 内容大小限制
    content_size = len(data.ddl.encode("utf-8"))
    if data.format == "csv":
        if content_size > 209_715_200:
            raise HTTPException(status_code=422, detail="CSV 内容超过 200MB 限制")
    else:
        if content_size > 5_242_880:
            raise HTTPException(status_code=422, detail="DDL 内容超过 5MB 限制")

    job_id = str(uuid.uuid4())

    # 启动后台任务
    asyncio.create_task(run_mapping_job(
        job_id=job_id,
        content=data.ddl,
        fmt=data.format,
        tenant_id=tenant_id_str,
        user_id=current_user.sub,
        table_name_filter=data.table_name,
    ))

    return {"job_id": job_id, "status": "pending"}


@router.get(
    "/jobs/{job_id}",
    dependencies=[Depends(require_permission("mapping:read"))],
)
async def get_mapping_job_status(job_id: str) -> dict:
    """查询映射任务进度。"""
    from drp.mapping.job_manager import get_job_status

    status = await get_job_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return status
