"""穿透溯源 API — 三级下钻查询与图谱路径分析。

API 层次：
  1 级: GET /drill/{indicator_id}/entities  — 指标 → 拉低指标的法人列表
  2 级: GET /drill/{entity_id}/accounts      — 法人 → 下属账户网络
  3 级: GET /drill/{account_id}/properties   — 账户 → 完整 FIBO+CTIO 属性
  路径: GET /drill/path/{indicator_id}       — 指标到根因账户的完整链路
  报告: GET /drill/report/{indicator_id}     — 下载 PDF 溯源报告
"""
from __future__ import annotations

import io
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from drp.auth.middleware import get_current_user
from drp.auth.schemas import TokenPayload
from drp.sparql.proxy import sparql_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drill", tags=["穿透溯源"])


# ─── 一级穿透：指标 → 法人列表 ─────────────────────────────────────────────────

@router.get("/{indicator_id}/entities")
async def get_entities_by_indicator(
    indicator_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """第一级穿透：返回拉低指标的法人列表。

    查询该指标对应的法人（LegalEntity），按贡献度降序排列。
    tenant_id 从 JWT 上下文中自动注入到 SPARQL。
    """
    sparql = f"""
PREFIX ctio: <https://drp.example.com/ontology/ctio/>
PREFIX fibo-be-le-lp: <https://spec.edmcouncil.org/fibo/ontology/BE/LegalEntities/LegalPersons/>
SELECT ?entity ?entityName ?value WHERE {{
  ?ind a ctio:RegulatoryIndicator ;
       ctio:indicatorId "{indicator_id}" .
  ?entity a fibo-be-le-lp:LegalEntity ;
          ctio:affectsIndicator ?ind ;
          ctio:contributionValue ?value .
  OPTIONAL {{ ?entity ctio:entityName ?entityName . }}
}}
ORDER BY ASC(?value)
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error("一级穿透查询失败: indicator=%s err=%s", indicator_id, exc)
        raise HTTPException(status_code=500, detail=f"SPARQL 查询失败: {exc}") from exc

    return [
        {
            "entity_iri": r.get("entity"),
            "entity_name": r.get("entityName") or r.get("entity", "").split(":")[-1],
            "contribution_value": _safe_float(r.get("value")),
        }
        for r in rows
    ]


# ─── 二级穿透：法人 → 账户网络 ─────────────────────────────────────────────────

@router.get("/{entity_id}/accounts")
async def get_accounts_by_entity(
    entity_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """第二级穿透：返回法人下的账户网络。

    entity_id 为法人的 IRI 最后一段（URL 编码的实体标识符）。
    """
    entity_iri = f"urn:entity:{entity_id}"
    sparql = f"""
PREFIX ctio: <https://drp.example.com/ontology/ctio/>
PREFIX fibo-fbc-pas-caa: <https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/ClientsAndAccounts/>
SELECT ?acct ?acctNo ?balance ?status ?isDirectLinked WHERE {{
  <{entity_iri}> ctio:ownsAccount ?acct .
  OPTIONAL {{ ?acct ctio:accountNumber ?acctNo . }}
  OPTIONAL {{ ?acct ctio:balance ?balance . }}
  OPTIONAL {{ ?acct ctio:status ?status . }}
  OPTIONAL {{ ?acct ctio:isDirectLinked ?isDirectLinked . }}
}}
ORDER BY DESC(?balance)
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error("二级穿透查询失败: entity=%s err=%s", entity_id, exc)
        raise HTTPException(status_code=500, detail=f"SPARQL 查询失败: {exc}") from exc

    return [
        {
            "account_iri": r.get("acct"),
            "account_number": r.get("acctNo"),
            "balance": _safe_float(r.get("balance")),
            "status": r.get("status"),
            "is_direct_linked": r.get("isDirectLinked") == "true",
        }
        for r in rows
    ]


# ─── 三级穿透：账户 → 完整属性 ─────────────────────────────────────────────────

@router.get("/{account_id}/properties")
async def get_account_properties(
    account_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """第三级穿透：返回账户完整 FIBO+CTIO 属性。"""
    account_iri = f"urn:entity:{account_id}"
    sparql = f"""
PREFIX ctio: <https://drp.example.com/ontology/ctio/>
SELECT ?predicate ?object WHERE {{
  <{account_iri}> ?predicate ?object .
}}
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error("三级穿透查询失败: account=%s err=%s", account_id, exc)
        raise HTTPException(status_code=500, detail=f"SPARQL 查询失败: {exc}") from exc

    if not rows:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在")

    properties: dict[str, list] = {}
    for r in rows:
        pred = r.get("predicate", "")
        # 取 URI 最后一段作为属性名（支持 # / : 分隔符）
        for sep in ("#", "/", ":"):
            if sep in pred:
                short_pred = pred.split(sep)[-1]
                break
        else:
            short_pred = pred
        val = r.get("object")
        if short_pred not in properties:
            properties[short_pred] = []
        properties[short_pred].append(val)

    # 单值属性解包为标量
    return {
        k: v[0] if len(v) == 1 else v
        for k, v in properties.items()
    }


# ─── 图谱路径查询：指标 → 根因账户链路 ────────────────────────────────────────

@router.get("/path/{indicator_id}")
async def get_drill_path(
    indicator_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """图谱路径查询：从指标到根因账户的完整链路。

    使用 SPARQL 属性路径（/+）进行深度遍历。
    """
    sparql = f"""
PREFIX ctio: <https://drp.example.com/ontology/ctio/>
SELECT ?step ?node ?nodeType ?nodeLabel WHERE {{
  VALUES ?indicatorId {{ "{indicator_id}" }}
  ?ind a ctio:RegulatoryIndicator ;
       ctio:indicatorId ?indicatorId .
  {{
    BIND(1 AS ?step)
    BIND(?ind AS ?node)
    BIND("RegulatoryIndicator" AS ?nodeType)
    OPTIONAL {{ ?ind ctio:indicatorId ?nodeLabel . }}
  }} UNION {{
    BIND(2 AS ?step)
    ?ind ctio:affectedBy ?entity .
    BIND(?entity AS ?node)
    BIND("LegalEntity" AS ?nodeType)
    OPTIONAL {{ ?entity ctio:entityName ?nodeLabel . }}
  }} UNION {{
    BIND(3 AS ?step)
    ?ind ctio:affectedBy ?entity .
    ?entity ctio:ownsAccount ?acct .
    BIND(?acct AS ?node)
    BIND("Account" AS ?nodeType)
    OPTIONAL {{ ?acct ctio:accountNumber ?nodeLabel . }}
  }}
}}
ORDER BY ?step
"""
    try:
        rows = await sparql_query(sparql, tenant_id=current_user.tenant_id)
    except Exception as exc:
        logger.error("路径查询失败: indicator=%s err=%s", indicator_id, exc)
        raise HTTPException(status_code=500, detail=f"SPARQL 查询失败: {exc}") from exc

    return [
        {
            "step": int(r.get("step", 0)),
            "node_iri": r.get("node"),
            "node_type": r.get("nodeType"),
            "node_label": r.get("nodeLabel"),
        }
        for r in rows
    ]


# ─── PDF 溯源报告 ──────────────────────────────────────────────────────────────

@router.get("/report/{indicator_id}")
async def download_drill_report(
    indicator_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> StreamingResponse:
    """下载穿透溯源 PDF 报告。

    报告包含：指标信息、拉低法人列表、账户路径、生成时间戳。
    使用 reportlab 生成 PDF（若未安装则返回 JSON）。
    """
    # 采集数据
    try:
        entities = await get_entities_by_indicator(indicator_id, current_user)
        path = await get_drill_path(indicator_id, current_user)
    except HTTPException:
        entities, path = [], []

    report_data = {
        "indicator_id": indicator_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": current_user.tenant_id,
        "entities": entities,
        "path": path,
    }

    pdf_bytes = _generate_pdf(indicator_id, report_data)
    if pdf_bytes:
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="drill_report_{indicator_id}.pdf"'
            },
        )

    # Fallback: JSON 报告
    json_content = json.dumps(report_data, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(json_content.encode("utf-8")),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="drill_report_{indicator_id}.json"'
        },
    )


def _generate_pdf(indicator_id: str, data: dict) -> bytes | None:
    """尝试用 reportlab 生成 PDF。若未安装 reportlab 则返回 None。"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
    except ImportError:
        logger.info("reportlab 未安装，将返回 JSON 报告")
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"穿透溯源报告 — 指标 {indicator_id}", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"生成时间: {data['generated_at']}", styles["Normal"]))
    story.append(Paragraph(f"租户: {data['tenant_id']}", styles["Normal"]))
    story.append(Spacer(1, 12))

    if data["entities"]:
        story.append(Paragraph("影响法人列表", styles["Heading2"]))
        table_data = [["法人 IRI", "法人名称", "贡献值"]]
        for e in data["entities"][:20]:  # 最多展示 20 条
            table_data.append([
                str(e.get("entity_iri", ""))[:50],
                str(e.get("entity_name", "")),
                str(e.get("contribution_value", "")),
            ])
        story.append(Table(table_data))
        story.append(Spacer(1, 12))

    if data["path"]:
        story.append(Paragraph("溯源路径", styles["Heading2"]))
        for node in data["path"]:
            story.append(Paragraph(
                f"步骤 {node['step']}: [{node['node_type']}] {node.get('node_label') or node.get('node_iri', '')}",
                styles["Normal"],
            ))

    doc.build(story)
    return buf.getvalue()


# ─── 工具函数 ──────────────────────────────────────────────────────────────────

def _safe_float(val) -> float | None:
    """安全地将字符串转换为 float。"""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
