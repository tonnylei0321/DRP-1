"""
Pydantic 模型定义
"""
from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVELS = ("ERROR", "WARN", "INFO")
LogLevel = Literal["ERROR", "WARN", "INFO"]


class LogEntry(BaseModel):
    """单条日志记录"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    timestamp: datetime
    level: LogLevel
    service: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, value: object) -> datetime:
        """严格解析时间格式：YYYY-MM-DD HH:MM:SS"""
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            raise ValueError("timestamp 必须是字符串，格式为 YYYY-MM-DD HH:MM:SS")
        try:
            return datetime.strptime(value, LOG_TIME_FORMAT)
        except ValueError as exc:
            raise ValueError("timestamp 格式必须为 YYYY-MM-DD HH:MM:SS") from exc

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: object) -> str:
        """大小写标准化，Literal 负责枚举约束"""
        if not isinstance(value, str):
            raise ValueError("level 必须是字符串")
        return value.strip().upper()

    @field_validator("service")
    @classmethod
    def validate_service(cls, value: str) -> str:
        """验证 service 不含特殊字符"""
        if not value.isprintable():
            raise ValueError("service 不能包含不可打印字符")
        if '/' in value or '\\' in value or '\n' in value or '\r' in value:
            raise ValueError("service 不能包含 / \\ 换行符等特殊字符")
        return value


class LogBatchRequest(BaseModel):
    """批量日志请求"""

    model_config = ConfigDict(extra="forbid")

    logs: List[LogEntry]


class LogLevelStats(BaseModel):
    """固定的日志级别统计结构"""

    model_config = ConfigDict(extra="forbid")

    ERROR: int = Field(default=0, ge=0)
    WARN: int = Field(default=0, ge=0)
    INFO: int = Field(default=0, ge=0)


class LogStats(BaseModel):
    """日志统计响应"""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    by_level: LogLevelStats = Field(default_factory=LogLevelStats)
    by_service: Dict[str, int] = Field(default_factory=dict)


class LogIngestResponse(BaseModel):
    """日志摄取响应"""

    model_config = ConfigDict(extra="forbid")

    accepted: int = Field(ge=0)
    alerts_triggered: int = Field(ge=0)
    alerts_failed: int = Field(ge=0, default=0)
