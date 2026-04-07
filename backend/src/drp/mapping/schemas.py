"""映射 API 请求/响应 schemas。"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenerateMappingRequest(BaseModel):
    """生成映射建议请求。"""
    ddl: str = Field(..., min_length=10, max_length=209_715_200, description="DDL 或 CSV 内容")
    table_name: str | None = Field(None, description="仅处理指定表（留空则处理所有表）")
    format: str = Field(default="ddl", pattern=r"^(ddl|csv)$", description="输入格式：ddl 或 csv")


class MappingItemResponse(BaseModel):
    """单条映射规范响应。"""
    id: uuid.UUID
    source_table: str
    source_field: str
    target_property: str | None
    transform_rule: str | None
    confidence: float | None
    status: str
    auto_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateMappingResponse(BaseModel):
    """生成映射结果响应。"""
    ddl_hash: str
    total: int
    auto_approved: int
    mappings: list[MappingItemResponse]


class RejectMappingRequest(BaseModel):
    """拒绝映射请求。"""
    reason: str | None = Field(None, max_length=500, description="拒绝原因")


class BatchApproveRequest(BaseModel):
    """批量审核映射请求。"""
    mode: str = Field(default="all", pattern=r"^(all|threshold)$", description="审核模式：all 或 threshold")
    threshold: float = Field(default=80.0, description="置信度阈值（仅 threshold 模式生效）")
    max_count: int = Field(default=500, ge=1, le=5000, description="单次操作最大数量")


class BatchApproveResponse(BaseModel):
    """批量审核映射响应。"""
    approved_count: int
    skipped_count: int
    total_pending: int
