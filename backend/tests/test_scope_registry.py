"""业务表注册表（registry）单元测试。

验证 build_registry 能正确扫描 __data_scope__ = True 的模型，
以及 is_table_registered / is_column_valid 等查询接口的行为。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from drp.db.base import Base
from drp.scope.registry import (
    build_registry,
    get_registry,
    is_column_valid,
    is_table_registered,
)


# ---------------------------------------------------------------------------
# 测试用模型：标记了 __data_scope__ = True
# ---------------------------------------------------------------------------


class _ScopedItem(Base):
    """测试用：已注册的业务表，包含 created_by 列。"""

    __tablename__ = "test_scoped_item"
    __data_scope__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class _ScopedOrder(Base):
    """测试用：已注册的业务表，不包含 created_by 列。"""

    __tablename__ = "test_scoped_order"
    __data_scope__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    amount: Mapped[str] = mapped_column(String(50), nullable=False)


class _NonScopedLog(Base):
    """测试用：未标记 __data_scope__，不应被注册。"""

    __tablename__ = "test_non_scoped_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)


# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------


class TestBuildRegistry:
    """build_registry 构建逻辑测试。"""

    def setup_method(self) -> None:
        """每个测试前重新构建注册表。"""
        build_registry()

    def test_scoped_tables_registered(self) -> None:
        """标记了 __data_scope__ = True 的模型应被注册。"""
        registry = get_registry()
        assert "test_scoped_item" in registry
        assert "test_scoped_order" in registry

    def test_non_scoped_table_not_registered(self) -> None:
        """未标记 __data_scope__ 的模型不应被注册。"""
        registry = get_registry()
        assert "test_non_scoped_log" not in registry

    def test_columns_extracted(self) -> None:
        """注册表应正确提取列名和数据类型。"""
        registry = get_registry()
        item_meta = registry["test_scoped_item"]
        assert "id" in item_meta["columns"]
        assert "name" in item_meta["columns"]
        assert "created_by" in item_meta["columns"]
        assert "created_at" in item_meta["columns"]

    def test_supports_self_with_created_by(self) -> None:
        """包含 created_by 列的表 supports_self 应为 True。"""
        registry = get_registry()
        assert registry["test_scoped_item"]["supports_self"] is True

    def test_supports_self_without_created_by(self) -> None:
        """不包含 created_by 列的表 supports_self 应为 False。"""
        registry = get_registry()
        assert registry["test_scoped_order"]["supports_self"] is False


class TestIsTableRegistered:
    """is_table_registered 查询接口测试。"""

    def setup_method(self) -> None:
        build_registry()

    def test_registered_table(self) -> None:
        assert is_table_registered("test_scoped_item") is True

    def test_unregistered_table(self) -> None:
        assert is_table_registered("nonexistent_table") is False

    def test_non_scoped_table(self) -> None:
        assert is_table_registered("test_non_scoped_log") is False


class TestIsColumnValid:
    """is_column_valid 查询接口测试。"""

    def setup_method(self) -> None:
        build_registry()

    def test_valid_column(self) -> None:
        assert is_column_valid("test_scoped_item", "name") is True

    def test_invalid_column(self) -> None:
        assert is_column_valid("test_scoped_item", "nonexistent_col") is False

    def test_unregistered_table_column(self) -> None:
        """未注册表的列查询应返回 False。"""
        assert is_column_valid("nonexistent_table", "name") is False

    def test_non_scoped_table_column(self) -> None:
        """未标记 __data_scope__ 的表的列查询应返回 False。"""
        assert is_column_valid("test_non_scoped_log", "message") is False
