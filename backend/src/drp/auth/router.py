"""认证路由：本地登录 + SSO 占位端点。"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.schemas import LoginRequest, TokenResponse
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
    """SAML 2.0 SSO 回调（第4.2章实现，当前占位）。"""
    return {"detail": "SAML SSO 尚未实现，计划于第4.2章完成"}


@router.get("/oidc/callback", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def oidc_callback() -> dict:
    """OIDC 回调（第4.3章实现，当前占位）。"""
    return {"detail": "OIDC 尚未实现，计划于第4.3章完成"}
