"""AuthService + JWT 单元测试（mock DB）。"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from drp.auth.models import AuditLog, Permission, Role, User
from drp.auth.policy import MAX_FAILED_ATTEMPTS
from drp.auth.service import AuthError, AuthService


def _make_user(email="test@example.com", password="Abcd1234!", locked=False, failed=0) -> User:
    from drp.auth.password import hash_password
    u = User()
    u.id = uuid.uuid4()
    u.tenant_id = uuid.uuid4()
    u.email = email
    u.password_hash = hash_password(password)
    u.status = "active"
    u.failed_login_count = failed
    u.locked_until = None
    u.last_login_at = None
    u.roles = []
    return u


@pytest.fixture
def mock_session():
    s = AsyncMock()
    s.commit = AsyncMock()
    s.add = MagicMock()
    return s


@pytest.fixture
def service(mock_session):
    return AuthService(session=mock_session)


# ─── 登录成功 ─────────────────────────────────────────────────────────────────


async def test_login_成功(service, mock_session):
    user = _make_user()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user)))

    result = await service.login(email="test@example.com", password="Abcd1234!")

    assert result.access_token
    assert result.token_type == "bearer"
    assert user.failed_login_count == 0
    assert user.last_login_at is not None


# ─── 登录失败 ─────────────────────────────────────────────────────────────────


async def test_login_用户不存在(service, mock_session):
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    with pytest.raises(AuthError):
        await service.login(email="ghost@example.com", password="Abcd1234!")


async def test_login_密码错误(service, mock_session):
    user = _make_user()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user)))

    with pytest.raises(AuthError):
        await service.login(email="test@example.com", password="WrongPass!")

    assert user.failed_login_count == 1


async def test_login_连续失败锁定账户(service, mock_session):
    user = _make_user(failed=MAX_FAILED_ATTEMPTS - 1)
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user)))

    with pytest.raises(AuthError):
        await service.login(email="test@example.com", password="WrongPass!")

    assert user.failed_login_count == MAX_FAILED_ATTEMPTS
    assert user.locked_until is not None


async def test_login_账户锁定中(service, mock_session):
    from datetime import timedelta
    user = _make_user()
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user)))

    with pytest.raises(AuthError, match="锁定"):
        await service.login(email="test@example.com", password="Abcd1234!")


# ─── JWT ─────────────────────────────────────────────────────────────────────


def test_jwt_创建和解码():
    from drp.auth.jwt import create_access_token, decode_access_token

    uid = str(uuid.uuid4())
    tid = str(uuid.uuid4())
    token, expires = create_access_token(uid, tid, "test@example.com", ["tenant:read"])

    payload = decode_access_token(token)
    assert payload.sub == uid
    assert payload.tenant_id == tid
    assert "tenant:read" in payload.permissions
    assert expires > 0


def test_jwt_无效令牌抛出错误():
    from jose import JWTError
    from drp.auth.jwt import decode_access_token

    with pytest.raises(JWTError):
        decode_access_token("invalid.token.here")
