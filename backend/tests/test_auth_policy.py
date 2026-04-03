"""密码策略单元测试。"""
import pytest
from datetime import datetime, timedelta, timezone

from drp.auth.password import hash_password, verify_password
from drp.auth.policy import (
    MAX_FAILED_ATTEMPTS,
    PASSWORD_MAX_AGE_DAYS,
    is_account_locked,
    is_password_expired,
    lockout_until,
    validate_password_complexity,
)


# ─── bcrypt 哈希 ─────────────────────────────────────────────────────────────


def test_hash_and_verify_密码正确():
    hashed = hash_password("Abcd1234!")
    assert verify_password("Abcd1234!", hashed) is True


def test_verify_密码错误():
    hashed = hash_password("Abcd1234!")
    assert verify_password("wrong", hashed) is False


# ─── 密码复杂度 ───────────���───────────────────────────────────────────────────


def test_复杂度校验_合法密码():
    assert validate_password_complexity("Abcd1234!") == []


def test_复杂度校验_太短():
    errors = validate_password_complexity("Ab1!")
    assert any("8 位" in e for e in errors)


def test_复杂度校验_无大写():
    errors = validate_password_complexity("abcd1234!")
    assert any("大写" in e for e in errors)


def test_复杂度校验_无数字():
    errors = validate_password_complexity("Abcdefgh!")
    assert any("数字" in e for e in errors)


def test_复杂度校验_无特殊字符():
    errors = validate_password_complexity("Abcd1234")
    assert any("特殊字符" in e for e in errors)


# ─── 密码过期 ─────────────────────────────────────────────────────────────────


def test_密码未过期():
    changed = datetime.now(timezone.utc) - timedelta(days=10)
    assert is_password_expired(changed) is False


def test_密码已过期():
    changed = datetime.now(timezone.utc) - timedelta(days=PASSWORD_MAX_AGE_DAYS + 1)
    assert is_password_expired(changed) is True


def test_密码从未修改视为过期():
    assert is_password_expired(None) is True


# ─── 账户锁定 ─────────────────────────────────────────────────────────────────


def test_账户未锁定():
    assert is_account_locked(None) is False


def test_账户锁定中():
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    assert is_account_locked(future) is True


def test_账户锁定已过期():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert is_account_locked(past) is False


def test_lockout_until_在未来():
    until = lockout_until()
    assert until > datetime.now(timezone.utc)
