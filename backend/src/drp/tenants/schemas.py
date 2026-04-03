import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """创建租户请求体。"""

    name: str = Field(..., min_length=1, max_length=200, description="租户名称")
    slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9\-]+$",
        description="唯一标识符（小写字母、数字、连字符）",
    )


class TenantResponse(BaseModel):
    """租户响应体。"""

    id: uuid.UUID
    name: str
    slug: str
    status: str
    graph_iri: str
    created_at: datetime

    model_config = {"from_attributes": True}
