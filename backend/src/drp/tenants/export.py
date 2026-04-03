"""
13.7 租户数据导出接口 — 将单租户 Named Graph 导出为 TriG 文件
"""
import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response

from drp.auth.middleware import get_current_user, require_permission
from drp.auth.schemas import TokenPayload
from drp.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tenants", tags=["租户管理"])


@router.get("/{tenant_id}/export")
async def export_tenant_data(
    tenant_id: str,
    current_user: TokenPayload = Depends(require_permission("tenant:read")),
) -> Response:
    """
    将指定租户的 Named Graph 导出为 TriG 格式。

    Returns:
        TriG 文件下载响应（Content-Type: application/trig）
    """
    graph_iri = f"urn:tenant:{tenant_id}"
    base_url = f"{settings.graphdb_url}/repositories/{settings.graphdb_repository}"

    # 构建 CONSTRUCT 查询提取命名图全部三元组
    sparql = f"""
CONSTRUCT {{ ?s ?p ?o }}
WHERE {{
  GRAPH <{graph_iri}> {{ ?s ?p ?o }}
}}
"""
    try:
        async with httpx.AsyncClient(
            auth=(settings.graphdb_username, settings.graphdb_password),
            timeout=120.0,
        ) as client:
            resp = await client.post(
                base_url,
                content=sparql,
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/trig",
                },
            )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=500, detail=f"GraphDB 导出失败: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"导出失败: {exc}") from exc

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"tenant_{tenant_id}_{timestamp}.trig"

    return Response(
        content=resp.content,
        media_type="application/trig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
