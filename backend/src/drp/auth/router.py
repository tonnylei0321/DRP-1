"""认证路由：本地登录 + SSO 占位端点 + 用户/角色/审计日志管理。"""
import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.models import AuditLog, Permission, Role, RolePermission, User, UserRole
from drp.auth.password import hash_password
from drp.auth.schemas import LoginRequest, TokenPayload, TokenResponse, UserResponse
from drp.auth.service import AuthError, AuthService
from drp.db.session import get_session

router = APIRouter(prefix="/auth", tags=["认证"])


def _get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session=session)


@router.post("/login", response_model=TokenResponse)
async def local_login(
    request: Request,
    data: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """本地账号登录（bcrypt + JWT）。"""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    try:
        return await service.login(
            email=data.email,
            password=data.password,
            ip_address=ip,
            user_agent=ua,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post("/saml/callback", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def saml_callback() -> dict:
    """SAML 2.0 SSO 回调（占位）。"""
    return {"detail": "SAML SSO 尚未实现"}


@router.get("/oidc/callback", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def oidc_callback() -> dict:
    """OIDC 回调（占位）。"""
    return {"detail": "OIDC 尚未实现"}


# ─── 用户管理 ─────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    username: str | None = None
    full_name: str | None = None
    password: str = Field(..., min_length=6)
    tenant_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    status: str | None = None


@router.get("/users", response_model=list[UserResponse],
            dependencies=[Depends(require_permission("user:read"))])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserResponse]:
    """列出所有用户（排除已删除）。"""
    result = await session.execute(
        select(User).where(User.status != "deleted").order_by(User.created_at)
    )
    return [UserResponse.model_validate(u) for u in result.scalars()]


@router.get("/users/{user_id}", response_model=UserResponse,
            dependencies=[Depends(require_permission("user:read"))])
async def get_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> UserResponse:
    """查询单个用户。"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse.model_validate(user)


@router.post("/users", response_model=UserResponse, status_code=HTTPStatus.CREATED,
             dependencies=[Depends(require_permission("user:write"))])
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session)) -> UserResponse:
    """创建新用户。"""
    # 检查邮箱是否已存在
    exists = await session.execute(
        select(User).where(User.email == data.email, User.status != "deleted")
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="邮箱已被使用")
    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        tenant_id=data.tenant_id,
        status="active",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse,
            dependencies=[Depends(require_permission("user:write"))])
async def update_user(user_id: uuid.UUID, data: UserUpdate,
                      session: AsyncSession = Depends(get_session)) -> UserResponse:
    """更新用户信息。"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.username is not None:
        user.username = data.username
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.status is not None:
        user.status = data.status
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=HTTPStatus.NO_CONTENT,
               dependencies=[Depends(require_permission("user:delete"))])
async def delete_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    """软删除用户（status → deleted）。"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = "deleted"
    await session.commit()


# ─── 角色管理 ─────────────────────────────────────────────────────────────────

class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_system_role: bool
    permissions: list[str]
    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    permissions: list[str] = []
    tenant_id: uuid.UUID | None = None


class RoleUpdate(BaseModel):
    permissions: list[str]


@router.get("/roles", response_model=list[RoleResponse],
            dependencies=[Depends(require_permission("role:read"))])
async def list_roles(session: AsyncSession = Depends(get_session)) -> list[RoleResponse]:
    """列出所有角色及其权限。"""
    result = await session.execute(select(Role).order_by(Role.name))
    roles = list(result.scalars())
    return [
        RoleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            is_system_role=r.is_system_role,
            permissions=[p.resource for p in r.permissions],
        )
        for r in roles
    ]


@router.post("/roles", response_model=RoleResponse, status_code=HTTPStatus.CREATED,
             dependencies=[Depends(require_permission("role:write"))])
async def create_role(data: RoleCreate, session: AsyncSession = Depends(get_session)) -> RoleResponse:
    """创建��色并关联权限。"""
    role = Role(name=data.name, description=data.description, tenant_id=data.tenant_id)
    session.add(role)
    await session.flush()
    # 关联权限
    if data.permissions:
        perms_result = await session.execute(
            select(Permission).where(Permission.resource.in_(data.permissions))
        )
        for perm in perms_result.scalars():
            session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    await session.commit()
    await session.refresh(role)
    return RoleResponse(
        id=role.id, name=role.name, description=role.description,
        is_system_role=role.is_system_role,
        permissions=[p.resource for p in role.permissions],
    )


@router.put("/roles/{role_id}", response_model=RoleResponse,
            dependencies=[Depends(require_permission("role:write"))])
async def update_role(role_id: uuid.UUID, data: RoleUpdate,
                      session: AsyncSession = Depends(get_session)) -> RoleResponse:
    """更新角色权限列表（全量替换）。"""
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 删除旧权限关联
    old_rps = await session.execute(
        select(RolePermission).where(RolePermission.role_id == role_id)
    )
    for rp in old_rps.scalars():
        await session.delete(rp)
    await session.flush()
    # 添加新权限关联
    if data.permissions:
        perms_result = await session.execute(
            select(Permission).where(Permission.resource.in_(data.permissions))
        )
        for perm in perms_result.scalars():
            session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    await session.commit()
    await session.refresh(role)
    return RoleResponse(
        id=role.id, name=role.name, description=role.description,
        is_system_role=role.is_system_role,
        permissions=[p.resource for p in role.permissions],
    )


@router.delete("/roles/{role_id}", status_code=HTTPStatus.NO_CONTENT,
               dependencies=[Depends(require_permission("role:write"))])
async def delete_role(role_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> None:
    """删除角色（系统角色不可删除）。"""
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system_role:
        raise HTTPException(status_code=403, detail="系统角色不可删除")
    await session.delete(role)
    await session.commit()


# ─── 审计日志 ─────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    tenant_id: uuid.UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    detail: dict | None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/audit-logs", response_model=list[AuditLogResponse],
            dependencies=[Depends(require_permission("audit:read"))])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLogResponse]:
    """查询审计日志，支持按 action 精确过滤和分页。"""
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.where(AuditLog.action == action)
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(q)
    logs = list(result.scalars())
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            tenant_id=log.tenant_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=str(log.ip_address) if log.ip_address else None,
            detail=log.detail,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]
