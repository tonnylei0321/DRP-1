"""权限中间件单元测试。"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drp.auth.jwt import create_access_token
from drp.auth.middleware import get_current_user, require_permission
from drp.auth.schemas import TokenPayload


def _make_token(permissions: list[str] = None) -> str:
    uid = str(uuid.uuid4())
    tid = str(uuid.uuid4())
    token, _ = create_access_token(uid, tid, "test@example.com", permissions or [])
    return token


# ─── 最小 FastAPI 测试 App ─────────────────────────────────────────────────────

_app = FastAPI()


@_app.get("/me")
async def me(user: TokenPayload = __import__("fastapi").Depends(get_current_user)):
    return {"email": user.email}


@_app.get("/admin")
async def admin(
    user: TokenPayload = __import__("fastapi").Depends(
        require_permission("tenant:write")
    )
):
    return {"ok": True}


_client = TestClient(_app, raise_server_exceptions=True)


def test_无token返回401():
    resp = _client.get("/me")
    assert resp.status_code == 401


def test_有效token返回用户信息():
    token = _make_token(["tenant:read"])
    resp = _client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_有权限访问受保护端点():
    token = _make_token(["tenant:write"])
    resp = _client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_无权限返回403():
    token = _make_token([])  # 无任何权限
    resp = _client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_无效token返回401():
    resp = _client.get("/me", headers={"Authorization": "Bearer invalid.token"})
    assert resp.status_code == 401
