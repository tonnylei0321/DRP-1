"""映射 API 请求/响应 schemas。"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenerateMappingRequest(BaseModel):
    """生成映射建议请求。"""
    ddl: str = Field(..., min_length=10, description="数据库 DDL SQL 内容")
    table_name: str | None = Field(None, description="仅处理指定表（留空则处理所有表）")


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
