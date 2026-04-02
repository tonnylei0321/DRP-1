"""
Code Processor Module

Multi-language code analysis for building R&D ontology.
Supports Java, Python, JavaScript/TypeScript.
"""

__version__ = "1.3.0"
__author__ = "ontologyDevOS Team"

from .base_parser import (
    BaseCodeParser,
    LanguageType,
    ElementType,
    RelationType,
    CodeElement,
    CodeRelation,
    ProjectInfo
)
from .java_parser import JavaParser
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser, TypeScriptParser
from .parser_factory import ParserFactory, MultiLanguageProjectAnalyzer
from .document_generator import DocumentGenerator
from .nlp_generator import NLPGenerator
from .document_writer import Document, DocumentWriter, generate_element_id
from .incremental_processor import IncrementalProcessor

__all__ = [
    # 基础类型
    "BaseCodeParser",
    "LanguageType",
    "ElementType",
    "RelationType",
    "CodeElement",
    "CodeRelation",
    "ProjectInfo",
    # 解析器
    "JavaParser",
    "PythonParser",
    "JavaScriptParser",
    "TypeScriptParser",
    "ParserFactory",
    "MultiLanguageProjectAnalyzer",
    # 文档生成
    "DocumentGenerator",
    "NLPGenerator",
    "Document",
    "DocumentWriter",
    "generate_element_id",
    # 增量处理
    "IncrementalProcessor",
]
