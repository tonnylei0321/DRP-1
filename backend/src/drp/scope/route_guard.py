"""路由安全扫描：检查查询了已注册业务表但未使用 require_data_scope 依赖的路由。

核心接口：
- scan_unguarded_routes(app, registry) -> list[str]
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)


def _has_require_data_scope(dependencies: list[Any]) -> bool:
    """检查依赖链中是否包含 require_data_scope。"""
    for dep in dependencies:
        dep_callable = getattr(dep, "dependency", dep)
        if dep_callable is None:
            continue
        qual_name = getattr(dep_callable, "__qualname__", "")
        if "require_data_scope" in qual_name:
            return True
    return False


def scan_unguarded_routes(
    app: FastAPI,
    registry: dict[str, Any],
) -> list[str]:
    """扫描所有路由，输出未使用 require_data_scope 依赖的 WARNING 日志。

    简单启发式：遍历 APIRoute，检查 dependencies 列表。
    仅检查路由级别的显式依赖声明，不分析函数内部查询逻辑。

    Args:
        app: FastAPI 应用实例
        registry: 已注册业务表元数据字典

    Returns:
        未保护的路由路径列表（仅用于日志和监控）
    """
    if not registry:
        return []

    unguarded: list[str] = []

    # 需要排除的管理类路由前缀（不直接查询业务数据表）
    skip_prefixes = (
        "/auth", "/health", "/data-scope", "/departments",
        "/tenants", "/api/docs", "/openapi.json",
    )

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        path = route.path
        if any(path.startswith(p) for p in skip_prefixes):
            continue

        # 仅检查 GET 路由（查询类）
        methods = route.methods or set()
        if "GET" not in methods:
            continue

        if not _has_require_data_scope(route.dependencies):
            unguarded.append(path)
            logger.warning(
                "路由 %s 未使用 require_data_scope 依赖，"
                "可能存在未保护的业务数据查询",
                path,
            )

    return unguarded
