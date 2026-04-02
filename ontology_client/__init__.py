"""
Ontology Client Module

用于与 ontology 项目集成的客户端模块。
"""

from .config import OntologyConfig, get_config, DEFAULT_CONFIG_PATH
from .client import OntologyClient, BuildResult

__all__ = [
    "OntologyConfig",
    "OntologyClient",
    "BuildResult",
    "get_config",
    "DEFAULT_CONFIG_PATH",
]
