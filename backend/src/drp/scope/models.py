"""数据权限 ORM 模型：Department、DataScopeRule、ColumnMaskRule。

映射 PostgreSQL schema（004_data_scope.sql）。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drp.db.base import Base


class Department(Base):
    """部门表，支持自引用树形结构。"""

    __tablename__ = "department"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("department.id", ondelete="RESTRICT"),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "parent_id"),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_dept_status"),
    )

    # relationships
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
        lazy="selectin",
    )
    parent: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="children",
        remote_side=[id],
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="department",
        lazy="selectin",
    )


class DataScopeRule(Base):
    """数据范围规则表（行级过滤）。"""

    __tablename__ = "data_scope_rule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False)
    custom_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "table_name", "scope_type"),
        CheckConstraint(
            "scope_type IN ('all', 'dept', 'self', 'custom')",
            name="ck_dsr_scope_type",
        ),
        CheckConstraint(
            "scope_type != 'custom' OR custom_condition IS NOT NULL",
            name="ck_dsr_custom_condition_required",
        ),
        CheckConstraint(
            "custom_condition IS NULL OR length(custom_condition) <= 500",
            name="ck_dsr_custom_condition_length",
        ),
    )


class ColumnMaskRule(Base):
    """列级脱敏规则表。"""

    __tablename__ = "column_mask_rule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mask_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    mask_pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)
    regex_expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "role_id", "table_name", "column_name"),
        CheckConstraint(
            "mask_strategy IN ('mask', 'hide', 'none')",
            name="ck_cmr_mask_strategy",
        ),
        CheckConstraint(
            "mask_strategy != 'mask' OR mask_pattern IS NOT NULL",
            name="ck_cmr_mask_pattern_required",
        ),
        CheckConstraint(
            "mask_pattern IN ('phone', 'id_card', 'email', 'custom_regex')",
            name="ck_cmr_mask_pattern_values",
        ),
        CheckConstraint(
            "mask_pattern != 'custom_regex' OR regex_expression IS NOT NULL",
            name="ck_cmr_regex_required",
        ),
    )
