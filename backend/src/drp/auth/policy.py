"""密码安全策略：复杂度校验、过期检测。

连续失败锁定逻辑在 AuthService 中管理。
"""
import re
from datetime import datetime, timedelta, timezone

# 密码最大有效期（天）
PASSWORD_MAX_AGE_DAYS = 90
# 最大连续失败次数（超过则锁定）
MAX_FAILED_ATTEMPTS = 5
# 锁定时长（分钟）
LOCKOUT_MINUTES = 30


_COMPLEXITY_RULES = [
    (r"[A-Z]", "必须包含大写字母"),
    (r"[a-z]", "必须包含小写字母"),
    (r"\d", "必须包含数字"),
    (r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", "必须包含特殊字符"),
]


def validate_password_complexity(password: str) -> list[str]:
    """校验密码复杂度，返回不满足的规则描述列表（空列表表示通过）。"""
    errors: list[str] = []
    if len(password) < 8:
        errors.append("密码长度不得少于 8 位")
    for pattern, msg in _COMPLEXITY_RULES:
        if not re.search(pattern, password):
            errors.append(msg)
    return errors


def is_password_expired(password_changed_at: datetime | None) -> bool:
    """判断密码是否已过期（超过 90 天未修改视为过期）。"""
    if password_changed_at is None:
        return True
    expiry = password_changed_at + timedelta(days=PASSWORD_MAX_AGE_DAYS)
    return datetime.now(timezone.utc) > expiry


def is_account_locked(locked_until: datetime | None) -> bool:
    """判断账户是否处于锁定状态。"""
    if locked_until is None:
        return False
    return datetime.now(timezone.utc) < locked_until


def lockout_until() -> datetime:
    """返回锁定截止时间（当前时间 + LOCKOUT_MINUTES）。"""
    return datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
