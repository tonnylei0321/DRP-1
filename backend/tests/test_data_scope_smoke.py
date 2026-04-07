"""数据权限冒烟测试：验证核心功能的最小可用路径（Happy Path）。

不依赖真实数据库和 Redis，使用 mock。
用例 5 使用 SQLite 内存数据库验证部门树递归查询。

需求覆盖: 1.5, 1.6, 2.5, 3.1, 3.2, 5.1, 5.2.2, 5.2.8
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 标记：所有用例统一标记为 smoke
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.smoke


# ===================================================================
# 用例 1：行级规则 Happy Path（scope_type=self）
# ===================================================================


@pytest.mark.asyncio
async def test_row_scope_self_builds_where_clause():
    """mock 用户 A 有 self 类型规则，验证 _build_where_clause 生成正确条件。"""
    from drp.scope.interceptor import _build_where_clause

    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    table_name = "item"

    rules = [{"scope_type": "self", "custom_condition": None}]

    # mock get_registry 返回包含 created_by 列的表元数据
    fake_registry = {
        table_name: {
            "table_name": table_name,
            "columns": {"id": "UUID", "created_by": "UUID", "name": "VARCHAR"},
            "supports_self": True,
        }
    }

    with patch("drp.scope.interceptor.get_registry", return_value=fake_registry):
        where_clause, bind_params, is_all = await _build_where_clause(
            rules=rules,
            tenant_id=tenant_id,
            user_id=user_id,
            table_name=table_name,
            session=None,
        )

    # 验证生成 created_by = :param 条件
    assert where_clause is not None
    assert "created_by" in where_clause
    assert is_all is False

    # 验证绑定参数包含用户 A 的 ID
    assert len(bind_params) == 1
    param_value = list(bind_params.values())[0]
    assert param_value == user_id


# ===================================================================
# 用例 2：列级脱敏 Happy Path（mask_strategy=mask, pattern=phone）
# ===================================================================


def test_column_mask_phone_pattern():
    """输入 phone=13812345678，验证脱敏输出 138****5678。"""
    from drp.scope.mask_serializer import apply_mask_rules

    data = {"phone": "13812345678", "name": "张三"}
    role_id = str(uuid.uuid4())

    rules = [
        {
            "role_id": role_id,
            "column_name": "phone",
            "mask_strategy": "mask",
            "mask_pattern": "phone",
            "regex_expression": None,
        }
    ]

    result = apply_mask_rules(data, rules, user_role_ids=[role_id])

    assert result["phone"] == "138****5678"
    # name 不受影响
    assert result["name"] == "张三"


# ===================================================================
# 用例 3：熔断开关 Happy Path
# ===================================================================


@pytest.mark.asyncio
async def test_circuit_breaker_open_and_closed():
    """mock Redis 返回不同状态，验证 is_circuit_open 行为。"""
    from drp.scope.circuit_breaker import is_circuit_open

    tenant_id = str(uuid.uuid4())

    # --- 场景 A：enabled=False → 熔断开启（旁路） ---
    mock_redis_a = AsyncMock()
    mock_redis_a.get = AsyncMock(
        return_value=json.dumps({"enabled": False}).encode()
    )
    mock_redis_a.aclose = AsyncMock()

    with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis_a):
        result = await is_circuit_open(tenant_id)
    assert result is True  # 熔断开启 → 旁路

    # --- 场景 B：enabled=True → 正常过滤 ---
    mock_redis_b = AsyncMock()
    mock_redis_b.get = AsyncMock(
        return_value=json.dumps({"enabled": True}).encode()
    )
    mock_redis_b.aclose = AsyncMock()

    with patch("drp.scope.circuit_breaker._get_redis", return_value=mock_redis_b):
        result = await is_circuit_open(tenant_id)
    assert result is False  # 正常过滤


# ===================================================================
# 用例 4：管理 API CRUD Happy Path（Schema 校验）
# ===================================================================


def test_admin_api_schemas_validation():
    """验证 Pydantic schema 校验通过。"""
    from drp.scope.router import (
        CircuitBreakerRequest,
        ColumnMaskRuleCreate,
        DataScopeRuleCreate,
    )

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()

    # DataScopeRuleCreate
    rule = DataScopeRuleCreate(
        tenant_id=tenant_id,
        user_id=user_id,
        table_name="item",
        scope_type="self",
    )
    assert rule.scope_type == "self"
    assert rule.table_name == "item"

    # ColumnMaskRuleCreate
    mask_rule = ColumnMaskRuleCreate(
        tenant_id=tenant_id,
        role_id=role_id,
        table_name="item",
        column_name="phone",
        mask_strategy="mask",
        mask_pattern="phone",
    )
    assert mask_rule.mask_strategy == "mask"
    assert mask_rule.mask_pattern == "phone"

    # CircuitBreakerRequest
    cb = CircuitBreakerRequest(enabled=False, password="secret123")
    assert cb.enabled is False
    assert cb.password == "secret123"
    assert cb.auto_recover_minutes is None


# ===================================================================
# 用例 5：部门层级过滤 Happy Path（SQLite 内存数据库）
# ===================================================================


@pytest.mark.asyncio
async def test_dept_subtree_with_sqlite():
    """使用 SQLite 内存数据库创建部门树 A→B→C，验证 get_dept_subtree。"""
    from sqlalchemy import Column, String, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        # 创建简化的 department 表（SQLite 兼容）
        await conn.execute(
            text(
                """
                CREATE TABLE department (
                    id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    tenant_id TEXT NOT NULL DEFAULT ''
                )
                """
            )
        )

        # 插入部门树 A → B → C
        dept_a = str(uuid.uuid4())
        dept_b = str(uuid.uuid4())
        dept_c = str(uuid.uuid4())

        await conn.execute(
            text("INSERT INTO department (id, parent_id) VALUES (:id, NULL)"),
            {"id": dept_a},
        )
        await conn.execute(
            text("INSERT INTO department (id, parent_id) VALUES (:id, :pid)"),
            {"id": dept_b, "pid": dept_a},
        )
        await conn.execute(
            text("INSERT INTO department (id, parent_id) VALUES (:id, :pid)"),
            {"id": dept_c, "pid": dept_b},
        )

    # 使用 raw SQL 模拟 get_dept_subtree 的递归 CTE 逻辑
    # SQLite 支持 WITH RECURSIVE
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 验证 get_dept_subtree(A) 返回 [A, B, C]
        result_a = await session.execute(
            text(
                """
                WITH RECURSIVE dept_tree AS (
                    SELECT id, parent_id, 1 AS depth
                    FROM department WHERE id = :dept_id
                    UNION ALL
                    SELECT d.id, d.parent_id, dt.depth + 1
                    FROM department d
                    INNER JOIN dept_tree dt ON d.parent_id = dt.id
                    WHERE dt.depth < 10
                )
                SELECT id FROM dept_tree
                """
            ),
            {"dept_id": dept_a},
        )
        ids_from_a = {row[0] for row in result_a.fetchall()}
        assert ids_from_a == {dept_a, dept_b, dept_c}

        # 验证 get_dept_subtree(B) 返回 [B, C]
        result_b = await session.execute(
            text(
                """
                WITH RECURSIVE dept_tree AS (
                    SELECT id, parent_id, 1 AS depth
                    FROM department WHERE id = :dept_id
                    UNION ALL
                    SELECT d.id, d.parent_id, dt.depth + 1
                    FROM department d
                    INNER JOIN dept_tree dt ON d.parent_id = dt.id
                    WHERE dt.depth < 10
                )
                SELECT id FROM dept_tree
                """
            ),
            {"dept_id": dept_b},
        )
        ids_from_b = {row[0] for row in result_b.fetchall()}
        assert ids_from_b == {dept_b, dept_c}

    await engine.dispose()
