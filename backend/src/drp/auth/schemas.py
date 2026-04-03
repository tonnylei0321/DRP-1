"""认证相关 Pydantic schemas。"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """本地账号登录请求。"""
    email: str = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=1, description="密码")


class TokenResponse(BaseModel):
    """JWT 令牌响应。"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="过期秒数")


class TokenPayload(BaseModel):
    """JWT Payload 结构。"""
    sub: str          # user_id
    tenant_id: str | None
    email: str
    permissions: list[str]
    exp: int


class UserResponse(BaseModel):
    """用户信息响应（脱敏）。"""
    id: uuid.UUID
    email: str
    username: str | None
    full_name: str | None
    status: str
    tenant_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
