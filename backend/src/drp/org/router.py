"""组织架构 API — 组织架构树查询与实体关系查询。"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.org.schemas import OrgNodeResponse, RelationResponse
from drp.sparql.proxy import sparql_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/org", tags=["组织架构"])

# root_id 合法字符：字母、数字、下划线、连字符
_ROOT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@router.get("/tree", summary="获取组织架构树", description="返回当前租户的组织架构树，支持分层加载和子树查询。")
async def get_org_tree(
    max_depth: int = Query(default=2, ge=1, le=6, description="从根节点向下展开的最大层数"),
    root_id: str | None = Query(default=None, pattern=r"^[a-zA-Z0-9_-]+$", description="指定子树根节点 ID（用于穿透钻取）"),
    current_user: TokenPayload = Depends(get_current_user),
) -> OrgNodeResponse:
    """返回组织架构树，支持分层加载。

    - max_depth: 从根节点向下展开的最大层数（默认2，范围1-6）
    - root_id: 指定子树根节点ID（用于穿透钻取），为空则从集团根节点开始
    - 安全约束：root_id 仅允许字母数字下划线和连字符，防止 SPARQL 注入
    - 性能约束：SPARQL 查询超时 30 秒，结果集上限 1000 条
    """
    # 构建 SPARQL 查询：获取扁平实体列表
    root_filter = ""
    if root_id:
        root_filter = f'FILTER(?entity = <urn:entity:{root_id}> || EXISTS {{ ?entity ctio:isSubsidiaryOf+ <urn:entity:{root_id}> }})'

    sparql = f"""
PREFIX ctio: <https://drp.example.com/ontology/ctio/>
PREFIX fibo: <https://spec.edmcouncil.org/fibo/ontology/BE/LegalEntities/LegalPersons/>

SELECT ?entity ?name ?level ?type ?city ?parent
       ?cash ?debt ?asset ?guarantee ?compliance ?risk ?hasChildren
WHERE {{
  ?entity a fibo:LegalEntity .
  ?entity ctio:entityName ?name .
  ?entity ctio:orgLevel ?level .
  OPTIONAL {{ ?entity ctio:entityType ?type . }}
  OPTIONAL {{ ?entity ctio:city ?city . }}
  OPTIONAL {{ ?entity ctio:isSubsidiaryOf ?parent . }}
  OPTIONAL {{ ?entity ctio:cashBalance ?cash . }}
  OPTIONAL {{ ?entity ctio:totalDebt ?debt . }}
  OPTIONAL {{ ?entity ctio:totalAsset ?asset . }}
  OPTIONAL {{ ?entity ctio:guaranteeBalance ?guarantee . }}
  OPTIONAL {{ ?entity ctio:complianceScore ?compliance . }}
  OPTIONAL {{ ?entity ctio:riskLevel ?risk . }}
  BIND(EXISTS {{ ?child ctio:isSubsidiaryOf ?entity }} AS ?hasChildren)
  FILTER(?level <= {max_depth})
  {root_filter}
}}
LIMIT 1000
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error("组织架构查询失败: root_id=%s max_depth=%s err=%s", root_id, max_depth, exc)
        raise HTTPException(status_code=500, detail="数据查询失败，请稍后重试") from exc

    # 将扁平结果构建为树形结构
    tree = _build_tree(rows, root_id, max_depth)
    if tree is None:
        # 无数据时返回空根节点
        return OrgNodeResponse(id=root_id or "root", name="未知", level=0)
    return tree


def _extract_id(iri: str | None) -> str:
    """从 IRI 中提取最后一段作为实体 ID。

    支持 urn:entity:xxx、http://.../xxx、prefix:xxx 等格式。
    """
    if not iri:
        return ""
    for sep in (":", "/", "#"):
        if sep in iri:
            return iri.rsplit(sep, 1)[-1]
    return iri


def _safe_float(val: str | None, default: float = 0) -> float:
    """安全地将字符串转换为 float，失败时返回默认值。"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _build_tree(
    rows: list[dict],
    root_id: str | None,
    max_depth: int,
) -> OrgNodeResponse | None:
    """将扁平 SPARQL 结果构建为递归树。

    1. 将所有行解析为节点字典（以 entity ID 为键）
    2. 根据 parent 关系建立父子映射
    3. 递归组装树
    """
    if not rows:
        return None

    # 解析所有节点
    nodes: dict[str, dict] = {}
    children_map: dict[str, list[str]] = {}  # parent_id -> [child_id, ...]

    for row in rows:
        entity_iri = row.get("entity", "")
        entity_id = _extract_id(entity_iri)
        if not entity_id:
            continue

        parent_iri = row.get("parent")
        parent_id = _extract_id(parent_iri) if parent_iri else None

        level = int(_safe_float(row.get("level"), 0))
        has_children = row.get("hasChildren", "").lower() == "true"

        nodes[entity_id] = {
            "id": entity_id,
            "name": row.get("name", "未知"),
            "level": level,
            "type": row.get("type", "未知"),
            "city": row.get("city", ""),
            "cash": _safe_float(row.get("cash")),
            "debt": _safe_float(row.get("debt")),
            "asset": _safe_float(row.get("asset")),
            "guarantee": _safe_float(row.get("guarantee")),
            "compliance": _safe_float(row.get("compliance")),
            "risk": row.get("risk", "lo") or "lo",
            "has_children": has_children,
            "parent_id": parent_id,
        }

        if parent_id:
            children_map.setdefault(parent_id, []).append(entity_id)

    # 找到根节点
    if root_id and root_id in nodes:
        root_node_id = root_id
    else:
        # 找没有 parent 的节点，或 level 最小的节点
        root_candidates = [
            nid for nid, n in nodes.items() if n["parent_id"] is None
        ]
        if root_candidates:
            root_node_id = root_candidates[0]
        else:
            # 取 level 最小的节点
            root_node_id = min(nodes, key=lambda nid: nodes[nid]["level"])

    return _assemble_node(root_node_id, nodes, children_map)


def _assemble_node(
    node_id: str,
    nodes: dict[str, dict],
    children_map: dict[str, list[str]],
) -> OrgNodeResponse | None:
    """递归组装单个节点及其子节点。"""
    node_data = nodes.get(node_id)
    if node_data is None:
        return None

    child_ids = children_map.get(node_id, [])
    children = []
    for cid in child_ids:
        child_node = _assemble_node(cid, nodes, children_map)
        if child_node is not None:
            children.append(child_node)

    return OrgNodeResponse(
        id=node_data["id"],
        name=node_data["name"],
        level=node_data["level"],
        type=node_data["type"],
        city=node_data["city"],
        cash=node_data["cash"],
        debt=node_data["debt"],
        asset=node_data["asset"],
        guarantee=node_data["guarantee"],
        compliance=node_data["compliance"],
        risk=node_data["risk"],
        has_children=node_data["has_children"],
        children=children,
    )


# ---------------------------------------------------------------------------
# GET /org/{entity_id}/relations — 实体关系查询
# ---------------------------------------------------------------------------

# 合法关系类型白名单
_VALID_REL_TYPES = frozenset(
    {"hasSubsidiary", "fundFlow", "guarantee", "borrowing", "fxExposure"}
)


@router.get(
    "/{entity_id}/relations",
    summary="获取实体关系列表",
    description="返回指定实体与其同级实体之间的关系列表（控股、资金流、担保、借贷、外汇敞口）。",
    response_model=list[RelationResponse],
)
async def get_entity_relations(
    entity_id: str = Path(
        ...,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="实体唯一标识（仅允许字母数字下划线和连字符）",
    ),
    current_user: TokenPayload = Depends(get_current_user),
) -> list[RelationResponse]:
    """返回指定实体与其同级实体之间的关系列表。

    - entity_id: 实体唯一标识
    - 安全约束：entity_id 仅允许字母数字下划线和连字符，防止 SPARQL 注入
    - 性能约束：SPARQL 查询超时 30 秒，结果集上限 1000 条
    """
    sparql = f"""
PREFIX ctio: <https://drp.example.com/ontology/ctio/>
SELECT ?source ?target ?relType
WHERE {{
  {{
    <urn:entity:{entity_id}> ctio:isSubsidiaryOf ?parent .
    ?sibling ctio:isSubsidiaryOf ?parent .
    ?source ?rel ?target .
    FILTER(?source = ?sibling || ?target = ?sibling)
    BIND(
      IF(?rel = ctio:hasSubsidiary, "hasSubsidiary",
      IF(?rel = ctio:fundFlowTo, "fundFlow",
      IF(?rel = ctio:guarantees, "guarantee",
      IF(?rel = ctio:borrowsFrom, "borrowing",
      IF(?rel = ctio:fxExposureTo, "fxExposure", "unknown"))))) AS ?relType
    )
  }}
}}
LIMIT 1000
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error(
            "实体关系查询失败: entity_id=%s err=%s", entity_id, exc
        )
        raise HTTPException(
            status_code=500, detail="数据查询失败，请稍后重试"
        ) from exc

    results: list[RelationResponse] = []
    for row in rows:
        source_id = _extract_id(row.get("source"))
        target_id = _extract_id(row.get("target"))
        rel_type = row.get("relType", "unknown")

        # 过滤无效记录：source/target 不能为空，relType 必须在白名单内
        if not source_id or not target_id:
            continue
        if rel_type not in _VALID_REL_TYPES:
            continue

        results.append(
            RelationResponse(source=source_id, target=target_id, type=rel_type)
        )

    return results
