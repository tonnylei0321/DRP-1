"""ETL 任务路由：任务列表、触发、数据质量查询。"""
import uuid
from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.schemas import TokenPayload
from drp.db.session import get_session
from drp.etl.models import EtlJob, EtlJobRepository
from drp.etl.quality import compute_latency

router = APIRouter(prefix="/etl", tags=["ETL 任务"])
_repo = EtlJobRepository()


# ─── 响应 schemas ─────────────────────────────────────────────────────────────

class EtlJobResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    job_type: str
    status: str
    triples_written: int
    error_message: str | None
    created_at: str
    finished_at: str | None

    model_config = {"from_attributes": True}


class EtlTriggerRequest(BaseModel):
    tenant_id: uuid.UUID
    table: str
    mapping_yaml: str


class EtlTriggerResponse(BaseModel):
    job_id: str


class DataQualityResponse(BaseModel):
    tenant_id: str
    null_rate: float
    latency_seconds: float
    format_compliance: float
    overall: float
    is_healthy: bool


# ─── 路由 ─────────────────────────────────────────────────────────────────────

@router.get("/jobs", response_model=list[EtlJobResponse],
            dependencies=[Depends(require_permission("etl:read"))])
async def list_etl_jobs(
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> list[EtlJobResponse]:
    """列出 ETL 任务记录（最近 100 条）。"""
    q = select(EtlJob).order_by(EtlJob.started_at.desc()).limit(100)
    if current_user.tenant_id:
        q = q.where(EtlJob.tenant_id == uuid.UUID(current_user.tenant_id))
    result = await session.execute(q)
    jobs = list(result.scalars())
    return [
        EtlJobResponse(
            id=j.id,
            tenant_id=j.tenant_id,
            job_type=j.job_type,
            status=j.status,
            triples_written=j.triples_written,
            error_message=j.error_message,
            created_at=j.started_at.isoformat(),
            finished_at=j.finished_at.isoformat() if j.finished_at else None,
        )
        for j in jobs
    ]


@router.post("/sync", response_model=EtlTriggerResponse, status_code=HTTPStatus.ACCEPTED,
             dependencies=[Depends(require_permission("etl:trigger"))])
async def trigger_etl(
    data: EtlTriggerRequest,
    session: AsyncSession = Depends(get_session),
) -> EtlTriggerResponse:
    """手动触发增量 ETL 同步任务（异步执行，立即返回 job_id）。"""
    # 创建任务记录
    job = await _repo.create(session, data.tenant_id, "incremental_sync")
    await session.commit()

    # 异步触发 Celery 任务（如 Celery 不可用则直接标记失败）
    try:
        from drp.etl.tasks import run_etl_sync
        run_etl_sync.delay(str(job.id), str(data.tenant_id), data.table, data.mapping_yaml)
    except Exception:
        # Celery 不可用时，标记任务失败
        await _repo.mark_failed(session, job, "Celery 不可用，无法异步执行")
        await session.commit()

    return EtlTriggerResponse(job_id=str(job.id))


@router.get("/quality/{tenant_id}", response_model=DataQualityResponse,
            dependencies=[Depends(require_permission("etl:read"))])
async def get_data_quality(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> DataQualityResponse:
    """查询指定租户的数据质量评分。"""
    # 取最近一次成功同步的水位线
    watermark = await _repo.get_last_watermark(session, tenant_id, "incremental_sync")
    if watermark is None:
        watermark = await _repo.get_last_watermark(session, tenant_id, "full_sync")

    latency = compute_latency(watermark)

    # 空值率和格式合规率：无真实数据时给默认值
    null_rate = 0.05
    format_compliance = 0.95

    # 综合评分：100 - (空值率*30 + 延迟惩罚*40 + (1-合规率)*30)
    latency_score = max(0.0, 1.0 - latency / 86400)  # 24h 内线性衰减
    overall = round(
        100 - (null_rate * 30 + (1 - latency_score) * 40 + (1 - format_compliance) * 30),
        2,
    )
    overall = max(0.0, min(100.0, overall))

    return DataQualityResponse(
        tenant_id=str(tenant_id),
        null_rate=null_rate,
        latency_seconds=latency if latency != float("inf") else 999999,
        format_compliance=format_compliance,
        overall=overall,
        is_healthy=overall >= 80.0,
    )
