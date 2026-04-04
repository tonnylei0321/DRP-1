"""指标 Pydantic 响应模型。"""

from pydantic import BaseModel, Field


class IndicatorResponse(BaseModel):
    """单个监管指标响应。"""

    id: str = Field(..., description="指标 ID")
    name: str = Field(..., description="指标名称")
    domain: str = Field(..., description="所属领域（fund/debt/guarantee/invest/derivative/finbiz/overseas）")
    unit: str = Field(default="", description="单位")
    value: float | str | None = Field(default=None, description="指标值")
    threshold: list[float | None] = Field(default=[None, None], description="阈值 [下限, 上限]")
    direction: str = Field(default="up", description="方向（up/down/mid）")
