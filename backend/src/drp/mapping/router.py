"""映射 API 路由。"""
import uuid
from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.schemas import TokenPayload
from drp.db.session import get_session
from drp.mapping.ddl_parser import parse_ddl
from drp.mapping.llm_service import generate_mapping_suggestions
from drp.mapping.models import MappingRepository, compute_ddl_hash
from drp.mapping.schemas import (
    GenerateMappingRequest,
    GenerateMappingResponse,
    MappingItemResponse,
)

router = APIRouter(prefix="/mappings", tags=["语义映射"])
_repo = MappingRepository()


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
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="需要租户上下文")

    tenant_id = uuid.UUID(current_user.tenant_id)
    ddl_hash = compute_ddl_hash(data.ddl)

    # 解析 DDL
    tables = parse_ddl(data.ddl)
    if not tables:
        raise HTTPException(status_code=422, detail="DDL 解析失败，未找到有效表定义")

    if data.table_name:
        tables = [t for t in tables if t.name.lower() == data.table_name.lower()]
        if not tables:
            raise HTTPException(status_code=404, detail=f"未找到表: {data.table_name}")

    # 获取历史映射（置信度计算参考）
    history = await _repo.get_approved_for_history(session, tenant_id)

    # 调用 LLM 生成建议
    all_suggestions = []
    for table in tables:
        suggestions = await generate_mapping_suggestions(table, history=history)
        all_suggestions.extend(suggestions)

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
    await session.commit()
    await session.refresh(mapping)
    return MappingItemResponse.model_validate(mapping)
