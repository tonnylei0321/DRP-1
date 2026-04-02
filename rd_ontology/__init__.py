# -*- coding: utf-8 -*-
"""
R&D Ontology Module

提供 R&D 本体的模式定义。

注意：TTL 生成逻辑已移至 ontology 项目的 CodeOntologyBuilder。
本模块仅保留 rd-core.ttl 作为模式参考。

使用方式：
1. 使用 ontology_client.OntologyClient.build_code_ontology() 构建代码本体
2. 使用 ontology_client.OntologyClient.build_sdd_ontology() 构建 SDD 本体
3. rd-core.ttl 可作为 schema_ttl 参数传递给上述方法
"""

from pathlib import Path

# 模式文件路径
SCHEMA_PATH = Path(__file__).parent / "rd-core.ttl"


def get_schema_ttl() -> str:
    """
    获取 R&D 本体模式 TTL 内容

    Returns:
        rd-core.ttl 的内容
    """
    if SCHEMA_PATH.exists():
        return SCHEMA_PATH.read_text(encoding='utf-8')
    return ""


__all__ = [
    "SCHEMA_PATH",
    "get_schema_ttl",
]
