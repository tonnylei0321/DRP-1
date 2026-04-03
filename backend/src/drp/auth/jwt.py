"""JWT 令牌创建与验证。"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from drp.auth.schemas import TokenPayload
from drp.config import settings


def create_access_token(
    user_id: str,
    tenant_id: str | None,
    email: str,
    permissions: list[str],
) -> tuple[str, int]:
    """创建 JWT 访问令牌，返回 (token, expires_in_seconds)。"""
    expires_in = settings.jwt_expire_minutes * 60
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "permissions": permissions,
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> TokenPayload:
    """解码并验�� JWT，抛出 JWTError 如令牌非法或过期。"""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return TokenPayload(**payload)
