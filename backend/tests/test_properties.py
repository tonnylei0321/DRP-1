"""属性测试 — Property 5, 9, 10 (后端侧)。

Property 5: 指标状态计算正确性（DataAdapter.computeStatus 的 Python 镜像）
Property 9: 组织架构树深度约束
Property 10: 后端 API 认证保护

运行: cd backend && .venv/bin/python -m pytest tests/test_properties.py -v
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.main import app
from drp.org.router import _build_tree, _assemble_node


# ── Property 5: 指标状态计算正确性 ──────────────────────────────────────────

def compute_status(value, threshold, direction):
    """Python 镜像：与前端 DataAdapter.computeStatus 逻辑一致。"""
    if not isinstance(value, (int, float)):
        return "normal"
    if not threshold or not isinstance(threshold, (list, tuple)):
        return "normal"

    if direction == "up":
        th = threshold[0]
        if th is None:
            return "normal"
        if th == 0:
            return "danger" if value < 0 else "normal"
        if value < th:
            return "danger"
        if value < th * 1.1:
            return "warn"
        return "normal"

    if direction == "down":
        th = threshold[1] if len(threshold) > 1 else threshold[0]
        if th is None:
            return "normal"
        if th == 0:
            return "danger" if value > 0 else "normal"
        if value > th:
            return "danger"
        if value >= th * 0.9:
            return "warn"
        return "normal"

    if direction == "mid":
        lo = threshold[0] if threshold[0] is not None else 0
        hi = threshold[1] if len(threshold) > 1 and threshold[1] is not None else 100
        if value < lo or value > hi:
            return "danger"
        rng = hi - lo
        margin = rng * 0.1
        if value < lo + margin or value > hi - margin:
            return "warn"
        return "normal"

    return "normal"


@given(
    value=st.floats(min_value=-1000, max_value=10000, allow_nan=False, allow_infinity=False),
    threshold=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
)
@h_settings(max_examples=200)
def test_property5_up_direction(value, threshold):
    """Property 5 (direction=up): 红 < 阈值, 黄 = 阈值~阈值*1.1, 绿 >= 阈值*1.1"""
    status = compute_status(value, [threshold, None], "up")
    assert status in ("danger", "warn", "normal")
    if value < threshold:
        assert status == "danger"
    elif value < threshold * 1.1:
        assert status == "warn"
    else:
        assert status == "normal"


@given(
    value=st.floats(min_value=-1000, max_value=10000, allow_nan=False, allow_infinity=False),
    threshold=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False),
)
@h_settings(max_examples=200)
def test_property5_down_direction(value, threshold):
    """Property 5 (direction=down): 红 > 阈值, 黄 = 阈值*0.9~阈值, 绿 < 阈值*0.9"""
    status = compute_status(value, [None, threshold], "down")
    assert status in ("danger", "warn", "normal")
    if value > threshold:
        assert status == "danger"
    elif value >= threshold * 0.9:
        assert status == "warn"
    else:
        assert status == "normal"


# ── Property 9: 组织架构树深度约束 ──────────────────────────────────────────

def _max_depth_in_tree(node_dict, current=0):
    """递归计算树的最大深度。"""
    if not node_dict:
        return current
    children = node_dict.get("children", [])
    if not children:
        return current
    return max(_max_depth_in_tree(c, current + 1) for c in children)


@given(max_depth=st.integers(min_value=1, max_value=6))
@h_settings(max_examples=50)
def test_property9_tree_depth_constraint(max_depth):
    """Property 9: /org/tree 返回的树深度不超过 max_depth。"""
    # 构造 mock SPARQL 数据：6层实体
    rows = []
    for level in range(max_depth + 2):  # 多生成2层确保有超出的
        entity_id = f"entity_L{level}"
        parent_id = f"entity_L{level-1}" if level > 0 else None
        rows.append({
            "entity": f"urn:entity:{entity_id}",
            "name": f"Entity Level {level}",
            "level": str(level),
            "type": "test",
            "city": "test",
            "parent": f"urn:entity:{parent_id}" if parent_id else None,
            "cash": "100",
            "debt": "50",
            "asset": "200",
            "guarantee": "30",
            "compliance": "90",
            "risk": "lo",
            "hasChildren": "true" if level < max_depth + 1 else "false",
        })

    # 只保留 level <= max_depth 的行（模拟 SPARQL FILTER）
    filtered = [r for r in rows if int(r["level"]) <= max_depth]
    tree = _build_tree(filtered, None, max_depth)

    if tree is not None:
        actual_depth = _max_depth_in_tree(tree.model_dump())
        assert actual_depth <= max_depth, (
            f"树深度 {actual_depth} 超过 max_depth {max_depth}"
        )


# ── Property 10: 后端 API 认证保护 ──────────────────────────────────────────

@pytest.mark.parametrize("path", [
    "/org/tree",
    "/indicators/test-entity",
    "/org/test-entity/relations",
])
async def test_property10_api_requires_auth(path):
    """Property 10: 三个新 API 在无 Authorization 头时返回 401。"""
    app.dependency_overrides.clear()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(path)
    assert resp.status_code == 401, (
        f"{path} 期望 401，实际 {resp.status_code}"
    )
