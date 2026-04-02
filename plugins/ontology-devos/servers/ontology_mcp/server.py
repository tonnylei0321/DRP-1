"""
ontology-devos MCP Server

提供代码本体检索能力，基于 ontology_sdk 实现。

工具：
- lookup_code_context: 混合检索代码上下文
- check_modification_impact: 修改影响分析
- link_spec_to_code: 需求-代码链接
"""

from __future__ import annotations

import atexit
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

logger = logging.getLogger("ontology-devos-mcp")
logging.basicConfig(
    level=os.environ.get("ONTOLOGY_DEVOS_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

mcp = FastMCP("ontology-devos")


# ============ 确保 SDK 可导入 ============

def _ensure_sdk_import():
    """确保 ontology_sdk 可导入"""
    ontology_path = os.environ.get("ONTOLOGY_PATH") or os.environ.get("ONTOLOGY_PROJECT_PATH")
    if ontology_path:
        # 添加 ontology 根目录
        if ontology_path not in sys.path:
            sys.path.insert(0, ontology_path)
        # 添加 SDK src 目录（新结构）
        sdk_src_path = os.path.join(ontology_path, "ontology_sdk", "src")
        if os.path.exists(sdk_src_path) and sdk_src_path not in sys.path:
            sys.path.insert(0, sdk_src_path)


_ensure_sdk_import()


# ============ 输入模型定义 ============

class LookupCodeContextInput(BaseModel):
    """代码上下文检索输入"""
    query: str = Field(..., description="自然语言查询")
    project_name: Optional[str] = Field(None, description="项目名称，用于选择对应的图库 ({project_name}_code)")
    top_k: int = Field(5, ge=1, le=200, description="返回结果数量")
    max_nodes: int = Field(30, ge=1, le=500, description="子图最大节点数")
    k_hops: int = Field(1, ge=1, le=5, description="图扩展跳数")
    enable_fulltext: bool = Field(True, description="启用全文检索")
    enable_semantic: bool = Field(True, description="启用语义检索")
    enable_structural: bool = Field(False, description="启用结构检索")
    context_format: str = Field("structured", description="上下文格式: structured|narrative|json")
    min_score: float = Field(0.01, ge=0.0, description="最小分数阈值")
    include_properties: bool = Field(True, description="包含节点属性")
    fulltext_index: Optional[str] = Field(None, description="全文索引名称")
    text_vector_index: Optional[str] = Field(None, description="向量索引名称")
    # 分层查询参数
    relation_layer: str = Field(
        "structure",
        description="关系层级: structure(代码结构关系,高精度)|semantic(语义关系,高召回)|all(全部关系)"
    )
    exclude_mentions: bool = Field(
        True,
        description="排除 MENTIONS 关系（减少噪音，提高查询精度）"
    )


class ImpactInput(BaseModel):
    """影响分析输入"""
    project_name: Optional[str] = Field(None, description="项目名称，用于选择对应的图库 ({project_name}_code)")
    file_paths: List[str] = Field(default_factory=list, description="文件路径列表")
    element_ids: List[str] = Field(default_factory=list, description="元素ID列表")
    depth: int = Field(2, ge=1, le=5, description="分析深度")


class RequirementItem(BaseModel):
    """需求项"""
    id: str = Field(..., description="需求ID")
    text: str = Field(..., description="需求文本")


class LinkSpecToCodeInput(BaseModel):
    """需求-代码链接输入"""
    requirements: List[RequirementItem] = Field(..., description="需求列表")
    project_name: Optional[str] = Field(None, description="项目名称，用于选择对应的图库 ({project_name}_code)")
    top_k: int = Field(5, ge=1, le=50, description="每个需求返回的匹配数")
    enable_fulltext: bool = Field(True, description="启用全文检索")
    enable_semantic: bool = Field(True, description="启用语义检索")
    min_score: float = Field(0.0, ge=0.0, description="最小分数阈值")
    filter_code_labels: bool = Field(True, description="仅返回代码相关节点")


class SwitchDatabaseInput(BaseModel):
    """切换数据库输入"""
    project_name: str = Field(..., description="项目名称，将使用 {project_name}_code 作为数据库名")
    create_if_not_exists: bool = Field(True, description="如果数据库不存在是否自动创建")


# ============ SDK 客户端管理 ============

_client = None
_current_database = None


def _get_client(project_name: Optional[str] = None):
    """获取 SDK 客户端（单例），支持按项目名切换数据库

    Args:
        project_name: 项目名称，如果提供则切换到对应的数据库 ({project_name}_code)
    """
    global _client, _current_database
    from ontology_sdk import ReasoningClient

    if _client is None:
        _client = ReasoningClient()
        _current_database = _client.config.neo4j_database
        logger.info(f"创建 ontology_sdk 客户端，当前数据库: {_current_database}")

    # 如果指定了项目名，切换到对应的数据库
    if project_name:
        target_database = ReasoningClient.get_database_name_for_project(project_name)
        if target_database != _current_database:
            if _client.switch_database(target_database, create_if_not_exists=True):
                _current_database = target_database
                logger.info(f"已切换到项目 {project_name} 的数据库: {target_database}")
            else:
                logger.error(f"切换到数据库 {target_database} 失败")

    return _client


def _cleanup():
    """清理资源"""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("ontology_sdk 客户端已关闭")


atexit.register(_cleanup)


# ============ MCP 工具实现 ============

@mcp.tool()
def lookup_code_context(input: LookupCodeContextInput) -> Dict[str, Any]:
    """
    混合检索代码上下文

    结合全文检索、语义检索和图结构扩展，返回与查询相关的代码上下文。
    可通过 project_name 参数指定项目，自动切换到对应的图库。

    分层查询说明：
    - structure: 仅使用代码结构关系（CALLS, DEPENDSON, IMPLEMENTS, IMPORTS, INHERITS, TESTSCODE）
                 适合精确的代码理解和依赖分析
    - semantic: 仅使用语义关系（CONTAINS, REALIZESDESIGN, IMPLEMENTSREQUIREMENT, DESCRIBES）
                适合需求追溯和设计理解
    - all: 使用全部关系（包括 MENTIONS），适合广泛探索
    """
    try:
        client = _get_client(input.project_name)

        # 根据 relation_layer 构建关系类型过滤
        relation_types = None
        if input.relation_layer == "structure":
            # L1 结构层：代码结构关系
            relation_types = [
                "CALLS", "DEPENDSON", "IMPLEMENTS", "IMPORTS", "INHERITS",
                "TESTSCODE", "USES", "DEFINES", "OVERRIDES", "EXTENDS"
            ]
        elif input.relation_layer == "semantic":
            # L2 语义层：语义/文档关系
            relation_types = [
                "CONTAINS", "REALIZESDESIGN", "IMPLEMENTSREQUIREMENT",
                "DESCRIBES", "AFFECTSFILE", "CONFIGURES", "EXTRACTS"
            ]
        # all: relation_types = None，不过滤

        # 如果 exclude_mentions=True 且 relation_layer=all，排除 MENTIONS
        exclude_relations = None
        if input.relation_layer == "all" and input.exclude_mentions:
            exclude_relations = ["MENTIONS"]

        result = client.lookup_context(
            query=input.query,
            top_k=input.top_k,
            max_nodes=input.max_nodes,
            k_hops=input.k_hops,
            enable_fulltext=input.enable_fulltext,
            enable_semantic=input.enable_semantic,
            enable_structural=input.enable_structural,
            context_format=input.context_format,
            min_score=input.min_score,
            include_properties=input.include_properties,
            relation_types=relation_types,
            exclude_relations=exclude_relations
        )
        return result.to_dict()
    except Exception as exc:
        logger.exception("lookup_code_context 失败")
        return {"error": str(exc)}


@mcp.tool()
def check_modification_impact(input: ImpactInput) -> Dict[str, Any]:
    """
    分析代码修改的影响范围

    返回受影响的代码、测试和需求。
    可通过 project_name 参数指定项目，自动切换到对应的图库。
    """
    try:
        client = _get_client(input.project_name)
        result = client.analyze_impact(
            files=input.file_paths,
            elements=input.element_ids,
            depth=input.depth
        )
        return result.to_dict()
    except Exception as exc:
        logger.exception("check_modification_impact 失败")
        return {"error": str(exc)}


@mcp.tool()
def link_spec_to_code(input: LinkSpecToCodeInput) -> Dict[str, Any]:
    """
    将需求链接到相关代码

    对每个需求进行混合检索，返回最相关的代码元素。
    可通过 project_name 参数指定项目，自动切换到对应的图库。
    """
    try:
        client = _get_client(input.project_name)
        # 转换输入格式
        requirements = [{"id": req.id, "text": req.text} for req in input.requirements]
        result = client.link_requirements(
            requirements=requirements,
            top_k=input.top_k,
            enable_fulltext=input.enable_fulltext,
            enable_semantic=input.enable_semantic,
            min_score=input.min_score,
            filter_code_labels=input.filter_code_labels
        )
        return result.to_dict()
    except Exception as exc:
        logger.exception("link_spec_to_code 失败")
        return {"error": str(exc)}


@mcp.tool()
def switch_database(input: SwitchDatabaseInput) -> Dict[str, Any]:
    """
    切换到指定项目的图库

    根据项目名切换到对应的数据库 ({project_name}_code)。
    如果数据库不存在且 create_if_not_exists=True，则自动创建。
    """
    try:
        from ontology_sdk import ReasoningClient
        client = _get_client()
        target_database = ReasoningClient.get_database_name_for_project(input.project_name)

        success = client.switch_database(target_database, create_if_not_exists=input.create_if_not_exists)

        global _current_database
        if success:
            _current_database = target_database

        return {
            "success": success,
            "project_name": input.project_name,
            "database": target_database,
            "message": f"已切换到数据库 {target_database}" if success else f"切换到数据库 {target_database} 失败"
        }
    except Exception as exc:
        logger.exception("switch_database 失败")
        return {"success": False, "error": str(exc)}


@mcp.tool()
def health_check() -> Dict[str, Any]:
    """
    检查连接健康状态

    返回 Neo4j 连接状态、版本信息和可用数据库列表。
    """
    try:
        client = _get_client()
        status = client.health_check()
        status["databases"] = client.list_databases()
        return status
    except Exception as exc:
        logger.exception("health_check 失败")
        return {"connected": False, "error": str(exc)}


if __name__ == "__main__":
    mcp.run()
