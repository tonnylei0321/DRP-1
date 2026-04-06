"""MappingSpec YAML 生成器：将映射建议序列化为标准格式。"""
from __future__ import annotations

import yaml

from drp.mapping.llm_service import MappingSuggestion


def generate_mapping_yaml(suggestions: list[MappingSuggestion]) -> str:
    """将映射建议列表序列化为 MappingSpec YAML 字符串。

    格式::

        mappings:
          - source_table: account
            source_field: acct_no
            target_property: ctio:accountNumber
            transform_rule: ""
            confidence: 92.5
            auto_approved: true
    """
    items = []
    for s in suggestions:
        items.append({
            "source_table": s.source_table,
            "source_field": s.source_field,
            "data_type": s.data_type,
            "target_property": s.target_property,
            "transform_rule": s.transform_rule or "",
            "confidence": float(s.confidence),
            "auto_approved": s.auto_approved,
        })
    return yaml.dump({"mappings": items}, allow_unicode=True, sort_keys=False)


def parse_mapping_yaml(content: str) -> list[dict]:
    """解析 MappingSpec YAML，返回映射字典列表。"""
    data = yaml.safe_load(content)
    return data.get("mappings", [])


def generate_mapping_yaml_from_specs(specs) -> str:
    """从 MappingSpec ORM 对象列表序列化为 YAML。"""
    items = []
    for s in specs:
        items.append({
            "source_table": s.source_table,
            "source_field": s.source_field,
            "data_type": s.data_type or "",
            "target_property": s.target_property or "",
            "transform_rule": s.transform_rule or "",
            "confidence": float(s.confidence) if s.confidence else 0.0,
            "auto_approved": s.auto_approved,
        })
    return yaml.dump({"mappings": items}, allow_unicode=True, sort_keys=False)