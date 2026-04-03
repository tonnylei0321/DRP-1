"""AuthService：认证流程协调，含审计日志写入。"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drp.auth.jwt import create_access_token
from drp.auth.models import AuditLog, User
from drp.auth.password import verify_password
from drp.auth.policy import (
    MAX_FAILED_ATTEMPTS,
    is_account_locked,
    lockout_until,
)
from drp.auth.schemas import TokenResponse

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """认证失败（统一错误，不暴露具体原因）。"""


class AuthService:
    """本地账号认证服务。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """本地账号登录，返回 JWT 令牌。

        失败时记录审计日志并更新失败计数；
        连续失败达上限时锁定账户。
        """
        user = await self._get_user_by_email(email)

        if user is None:
            # 用户不存在时也写审计日志（防止枚举）
            await self._write_audit(
                user_id=None,
                tenant_id=None,
                action="user.login_failed",
                detail={"reason": "user_not_found", "email": email},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthError("邮箱或密码不正确")

        # 检查锁定状态
        if is_account_locked(user.locked_until):
            await self._write_audit(
                user_id=user.id,
                tenant_id=user.tenant_id,
                action="user.login_blocked",
                detail={"reason": "account_locked"},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthError("账户已被锁定，请稍后再试")

        # 验��密码
        if not user.password_hash or not verify_password(password, user.password_hash):
            await self._handle_failed_login(user, ip_address, user_agent)
            raise AuthError("邮箱或密码不正确")

        # 登录成功：重置失败计数
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await self._session.commit()

        # 收集用户权限
        permissions = self._collect_permissions(user)

        # 写审计日志
        await self._write_audit(
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="user.login",
            detail={"method": "local"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        token, expires_in = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            email=user.email,
            permissions=permissions,
        )
        return TokenResponse(access_token=token, expires_in=expires_in)

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email, User.status != "deleted")
        )
        return result.scalar_one_or_none()

    async def _handle_failed_login(
        self, user: User, ip_address: str | None, user_agent: str | None
    ) -> None:
        user.failed_login_count += 1
        locked = False
        if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
            user.locked_until = lockout_until()
            locked = True
            logger.warning("账户因连续失败登录被锁定: %s", user.email)

        await self._write_audit(
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="user.login_failed",
            detail={
                "reason": "bad_password",
                "failed_count": user.failed_login_count,
                "locked": locked,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self._session.commit()

    @staticmethod
    def _collect_permissions(user: User) -> list[str]:
        perms: set[str] = set()
        for role in user.roles:
            for perm in role.permissions:
                perms.add(perm.resource)
        return sorted(perms)

    async def _write_audit(
        self,
        *,
        user_id: uuid.UUID | None,
        tenant_id: uuid.UUID | None,
        action: str,
        detail: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        log = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            action=action,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(log)
        # 不单独 commit，由调用方决定事务边界
