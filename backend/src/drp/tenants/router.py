import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from drp.db.session import get_session
from drp.tenants.schemas import TenantCreate, TenantResponse
from drp.tenants.service import TenantNotFoundError, TenantService

router = APIRouter(prefix="/tenants", tags=["租户管理"])


def _get_service(session: AsyncSession = Depends(get_session)) -> TenantService:
    return TenantService(session=session)


@router.post("", status_code=HTTPStatus.CREATED, response_model=TenantResponse)
async def create_tenant(
    data: TenantCreate,
    service: TenantService = Depends(_get_service),
) -> TenantResponse:
    """创建新租户，同步创建 GraphDB Named Graph。"""
    try:
        return await service.create_tenant(data)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    service: TenantService = Depends(_get_service),
) -> TenantResponse:
    """查询租户详情。"""
    try:
        return await service.get_tenant(tenant_id)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{tenant_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_tenant(
    tenant_id: uuid.UUID,
    service: TenantService = Depends(_get_service),
) -> None:
    """删除租户及其 GraphDB Named Graph。"""
    try:
        await service.delete_tenant(tenant_id)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
