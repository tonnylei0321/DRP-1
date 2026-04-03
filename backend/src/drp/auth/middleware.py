"""权限中间件：JWT 解析、租户上下文注入、API 级别鉴权。"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from drp.auth.jwt import decode_access_token
from drp.auth.schemas import TokenPayload
from drp.sparql.proxy import set_tenant_context

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenPayload:
    """从 Authorization: Bearer <token> 解析当前用户。

    自动将 tenant_id 写入 SPARQL ContextVar，
    使同一请求内的所有 SPARQL 调用自动隔离。
    """
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.tenant_id:
        set_tenant_context(payload.tenant_id)

    return payload


def require_permission(resource: str):
    """FastAPI 依赖工厂：要求当前用户拥有指定权限。

    用法::

        @router.get("/foo", dependencies=[Depends(require_permission("mapping:approve"))])
        async def foo(): ...
    """

    async def _check(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if resource not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 {resource}",
            )
        return user

    return _check
