"""组织架构与实体关系 Pydantic 响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrgNodeResponse(BaseModel):
    """组织架构树节点响应。"""

    id: str = Field(..., description="实体唯一标识")
    name: str = Field(..., description="实体名称")
    level: int = Field(..., description="层级（0=集团, 1=二级, 2=三级…）")
    type: str = Field(default="未知", description="实体类型")
    city: str = Field(default="", description="所在城市")
    cash: float = Field(default=0, description="现金余额（万元）")
    debt: float = Field(default=0, description="负债总额（万元）")
    asset: float = Field(default=0, description="资产总额（万元）")
    guarantee: float = Field(default=0, description="担保余额（万元）")
    compliance: float = Field(default=0, description="合规评分（0-100）")
    risk: str = Field(default="lo", description="风险等级（hi/md/lo）")
    has_children: bool = Field(default=False, description="是否有子节点")
    children: list[OrgNodeResponse] = Field(default_factory=list, description="子节点列表")


class RelationResponse(BaseModel):
    """实体关系响应。"""

    source: str = Field(..., description="源节点 ID")
    target: str = Field(..., description="目标节点 ID")
    type: str = Field(..., description="关系类型（hasSubsidiary/fundFlow/guarantee/borrowing/fxExposure）")
