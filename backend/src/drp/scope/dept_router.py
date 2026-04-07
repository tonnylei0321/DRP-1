"""部门管理路由：CRUD 接口 + 循环引用校验 + 用户关联校验。"""

import uuid
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.models import AuditLog, User
from drp.auth.schemas import TokenPayload
from drp.db.session import get_session
from drp.scope.dept_service import check_circular_reference
from drp.scope.models import Department

router = APIRouter(prefix="/departments", tags=["部门管理"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: uuid.UUID | None = None
    sort_order: int = 0
    status: str = "active"
    tenant_id: uuid.UUID | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int | None = None
    status: str | None = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime
    children: list["DepartmentResponse"] = []

    model_config = {"from_attributes": True}


def _dept_to_response(dept: Department) -> DepartmentResponse:
    """递归构建部门树响应。"""
    return DepartmentResponse(
        id=dept.id,
        tenant_id=dept.tenant_id,
        name=dept.name,
        parent_id=dept.parent_id,
        sort_order=dept.sort_order,
        status=dept.status,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
        children=[_dept_to_response(c) for c in (dept.children or [])],
    )


# ─── 路由 ─────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=list[DepartmentResponse],
    dependencies=[Depends(require_permission("department:read"))],
)
async def list_departments(
    session: AsyncSession = Depends(get_session),
) -> list[DepartmentResponse]:
    """查询部门树（返回根节点列表，子节点通过 children 嵌套）。"""
    result = await session.execute(
        select(Department)
        .where(Department.parent_id.is_(None))
        .order_by(Department.sort_order)
    )
    roots = list(result.scalars())
    return [_dept_to_response(d) for d in roots]


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(require_permission("department:write"))],
)
async def create_department(
    data: DepartmentCreate,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DepartmentResponse:
    """创建部门。"""
    # 如果指定了 parent_id，校验父部门存在
    if data.parent_id is not None:
        parent = await session.get(Department, data.parent_id)
        if parent is None:
            raise HTTPException(status_code=400, detail="父部门不存在")

    tenant_id = data.tenant_id or (uuid.UUID(user.tenant_id) if user.tenant_id else None)
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="缺少 tenant_id")

    dept = Department(
        name=data.name,
        parent_id=data.parent_id,
        sort_order=data.sort_order,
        status=data.status,
        tenant_id=tenant_id,
    )
    session.add(dept)

    # 审计日志
    session.add(AuditLog(
        tenant_id=tenant_id,
        user_id=uuid.UUID(user.sub),
        action="department.create",
        resource_type="department",
        detail={"name": data.name, "parent_id": str(data.parent_id) if data.parent_id else None},
    ))

    await session.commit()
    await session.refresh(dept)
    return _dept_to_response(dept)


@router.put(
    "/{dept_id}",
    response_model=DepartmentResponse,
    dependencies=[Depends(require_permission("department:write"))],
)
async def update_department(
    dept_id: uuid.UUID,
    data: DepartmentUpdate,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DepartmentResponse:
    """更新部门（含循环引用校验）。"""
    dept = await session.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 循环引用校验
    if data.parent_id is not None:
        if await check_circular_reference(session, dept_id, data.parent_id):
            raise HTTPException(status_code=400, detail="部门层级存在循环引用")
        dept.parent_id = data.parent_id

    if data.name is not None:
        dept.name = data.name
    if data.sort_order is not None:
        dept.sort_order = data.sort_order
    if data.status is not None:
        dept.status = data.status

    # 审计日志
    session.add(AuditLog(
        tenant_id=dept.tenant_id,
        user_id=uuid.UUID(user.sub),
        action="department.update",
        resource_type="department",
        resource_id=str(dept_id),
        detail=data.model_dump(exclude_none=True),
    ))

    await session.commit()
    await session.refresh(dept)
    return _dept_to_response(dept)


@router.delete(
    "/{dept_id}",
    status_code=HTTPStatus.NO_CONTENT,
    dependencies=[Depends(require_permission("department:write"))],
)
async def delete_department(
    dept_id: uuid.UUID,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """删除部门（校验用户关联）。"""
    dept = await session.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 校验是否有关联用户
    user_count_result = await session.execute(
        select(sa_func.count()).select_from(User).where(User.dept_id == dept_id)
    )
    user_count = user_count_result.scalar() or 0
    if user_count > 0:
        raise HTTPException(
            status_code=409,
            detail="该部门下仍有关联用户，请先迁移用户后再删除",
        )

    # 审计日志
    session.add(AuditLog(
        tenant_id=dept.tenant_id,
        user_id=uuid.UUID(user.sub),
        action="department.delete",
        resource_type="department",
        resource_id=str(dept_id),
        detail={"name": dept.name},
    ))

    await session.delete(dept)
    await session.commit()
