"""LLM 映射服务：调用 OpenAI 兼容 API（DeepSeek/GPT/Claude），生成字段映射建议。

支持 DeepSeek、OpenAI、任何 OpenAI 兼容 API。
通过 LLM_API_BASE + LLM_API_KEY + LLM_MODEL 环境变量配置。
"""
import json
import logging
from dataclasses import dataclass

import httpx

from drp.config import settings
from drp.mapping.confidence import compute_confidence, should_auto_approve
from drp.mapping.ddl_parser import ColumnInfo, TableInfo

logger = logging.getLogger(__name__)

# CTIO 属性列表（关键语义锚点，供 LLM 参考）
_CTIO_PROPERTIES = [
    "ctio:accountNumber",
    "ctio:balance",
    "ctio:currency",
    "ctio:bankCode",
    "ctio:entityId",
    "ctio:isRestricted",
    "ctio:isDirectLinked",
    "ctio:cashPoolId",
    "ctio:repaymentDate",
    "ctio:riskLevel",
    "ctio:status6311",
    "ctio:hasUKeyStatus",
    "fibo-fbc-fi-fi:hasMonetaryAmount",
    "fibo-be-le-lp:LegalEntity",
    "fibo-fbc-pas-caa:BankAccount",
]

_SYSTEM_PROMPT = """\
你是企业资金监管数据本体映射专家。用户会给你一张数据库表的字段列表（含类型和注释），
以及 CTIO/FIBO 本体的属性列表。请为每个字段推荐最匹配的目标属性。

输出格式：JSON 数组，每项包含：
- source_field: 源字段名
- target_property: 目标属性（从给定列表中选，如无匹配输出 null）
- transform_rule: 值转换规则描述（简短，如无则留空字符串）
- reasoning: 推荐理由（一句话）
"""


@dataclass
class MappingSuggestion:
    """单字段映射建议。"""
    source_table: str
    source_field: str
    data_type: str
    target_property: str | None
    transform_rule: str
    confidence: float
    auto_approved: bool
    reasoning: str = ""


def _get_api_config() -> tuple[str, str, str]:
    """获取 LLM API 配置，优先使用 llm_* 配置，回退到 claude/anthropic。"""
    api_key = settings.llm_api_key
    api_base = settings.llm_api_base
    model = settings.llm_model

    # 回退到旧配置
    if not api_key:
        api_key = settings.claude_api_key or settings.anthropic_api_key
    if not api_key:
        raise RuntimeError("未配置 LLM_API_KEY（或 CLAUDE_API_KEY）")

    return api_key, api_base, model


async def _call_llm(prompt: str, client: httpx.AsyncClient) -> str:
    """调用 OpenAI 兼容 API（DeepSeek/GPT 等），返回文本响应。"""
    api_key, api_base, model = _get_api_config()

    # 统一使用 OpenAI 兼容的 /chat/completions 端点
    url = f"{api_base.rstrip('/')}/chat/completions"

    resp = await client.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _build_prompt(table: TableInfo) -> str:
    lines = [f"表名：{table.name}"]
    if table.comment:
        lines.append(f"表注释：{table.comment}")
    lines.append("\n字段列表：")
    for col in table.columns:
        note = f"（注释：{col.comment}）" if col.comment else ""
        null_str = "允许NULL" if col.nullable else "NOT NULL"
        lines.append(f"  - {col.name}: {col.data_type} {null_str} {note}")

    lines.append("\n可用目标属性：")
    lines.extend(f"  - {p}" for p in _CTIO_PROPERTIES)
    lines.append("\n请输出 JSON 数组。")
    return "\n".join(lines)


def _parse_llm_response(raw: str) -> list[dict]:
    """从 LLM 响应中提取 JSON 数组。"""
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start == -1 or end == 0:
        logger.warning("LLM 响应中未找到 JSON 数组: %s", raw[:200])
        return []
    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError as exc:
        logger.warning("LLM 响应 JSON 解析失败: %s", exc)
        return []


async def generate_mapping_suggestions(
    table: TableInfo,
    history: list[dict] | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[MappingSuggestion]:
    """调用 LLM 生成映射建议，附加置信度计算。"""
    prompt = _build_prompt(table)

    should_close = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=120.0)

    try:
        raw = await _call_llm(prompt, client)
    finally:
        if should_close:
            await client.aclose()

    llm_items = _parse_llm_response(raw)
    llm_map = {item["source_field"]: item for item in llm_items if "source_field" in item}

    suggestions: list[MappingSuggestion] = []
    for col in table.columns:
        llm = llm_map.get(col.name, {})
        target = llm.get("target_property")
        transform = llm.get("transform_rule", "")
        reasoning = llm.get("reasoning", "")

        conf = compute_confidence(
            field_name=col.name,
            data_type=col.data_type,
            comment=col.comment,
            target_property=target or "",
            source_table=table.name,
            history=history,
        ) if target else 0.0

        suggestions.append(MappingSuggestion(
            source_table=table.name,
            source_field=col.name,
            data_type=col.data_type,
            target_property=target,
            transform_rule=transform,
            confidence=conf,
            auto_approved=should_auto_approve(conf),
            reasoning=reasoning,
        ))

    return suggestions
