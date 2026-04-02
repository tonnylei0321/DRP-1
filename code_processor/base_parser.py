"""
Code Parser Base Module

Provides unified interface and abstract implementation for multi-language code parsing.
Supports Java, Python, JavaScript/TypeScript and other programming languages.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LanguageType(Enum):
    """Supported programming language types"""
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    UNKNOWN = "unknown"


class ElementType(Enum):
    """Code element types"""
    # Common types
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTION = "function"
    METHOD = "method"
    FIELD = "field"
    VARIABLE = "variable"
    MODULE = "module"
    PACKAGE = "package"

    # Java specific
    ENUM = "enum"
    ANNOTATION = "annotation"
    CONSTRUCTOR = "constructor"

    # Python specific
    DECORATOR = "decorator"
    PROPERTY = "property"

    # JavaScript/TypeScript specific
    COMPONENT = "component"
    HOOK = "hook"
    EXPORT = "export"
    IMPORT = "import"


class RelationType(Enum):
    """Relationship types"""
    # Inheritance and implementation
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"

    # Dependency and calling
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    USES = "uses"
    IMPORTS = "imports"

    # Containment and composition
    CONTAINS = "contains"
    COMPOSED_OF = "composed_of"

    # Access and modification
    ACCESSES = "accesses"
    MODIFIES = "modifies"

    # Special relationships
    OVERRIDES = "overrides"
    DECORATES = "decorates"
    THROWS = "throws"
    RETURNS = "returns"


class CodeElement:
    """Code element data structure"""

    def __init__(self,
                 element_type: ElementType,
                 name: str,
                 full_name: str = None,
                 file_path: str = None,
                 line_number: int = None,
                 package: str = None,
                 modifiers: List[str] = None,
                 annotations: List[str] = None,
                 docstring: str = None,
                 parameters: List[Dict[str, Any]] = None,
                 return_type: str = None,
                 **kwargs):
        self.element_type = element_type
        self.name = name
        self.full_name = full_name or name
        self.file_path = file_path
        self.line_number = line_number
        self.package = package
        self.modifiers = modifiers or []
        self.annotations = annotations or []
        self.docstring = docstring

        # Parameter info (for methods and functions)
        self.parameters: List[Dict[str, Any]] = parameters or []

        # Return type info
        self.return_type: Optional[str] = return_type

        # Store language-specific extra attributes
        self.extra_attributes = kwargs

        # Child elements (e.g., methods and fields of a class)
        self.children: List['CodeElement'] = []

    def add_child(self, child: 'CodeElement'):
        """Add child element"""
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'type': self.element_type.value,
            'name': self.name,
            'full_name': self.full_name,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'package': self.package,
            'modifiers': self.modifiers,
            'annotations': self.annotations,
            'docstring': self.docstring,
            'parameters': self.parameters,
            'return_type': self.return_type,
            'children': [child.to_dict() for child in self.children],
            **self.extra_attributes
        }


class CodeRelation:
    """Code relationship data structure"""

    def __init__(self,
                 relation_type: RelationType,
                 source: str,
                 target: str,
                 source_type: ElementType = None,
                 target_type: ElementType = None,
                 context: str = None,
                 **kwargs):
        self.relation_type = relation_type
        self.source = source
        self.target = target
        self.source_type = source_type
        self.target_type = target_type
        self.context = context
        self.extra_attributes = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'relation_type': self.relation_type.value,
            'source': self.source,
            'target': self.target,
            'source_type': self.source_type.value if self.source_type else None,
            'target_type': self.target_type.value if self.target_type else None,
            'context': self.context,
            **self.extra_attributes
        }


class ProjectInfo:
    """Project information data structure"""

    def __init__(self, project_path: str, language: LanguageType):
        self.project_path = project_path
        self.language = language
        self.elements: List[CodeElement] = []
        self.relations: List[CodeRelation] = []
        self.packages: Dict[str, Dict[str, Any]] = {}
        self.statistics: Dict[str, Any] = {}
        self.dependencies: List[str] = []

    def add_element(self, element: CodeElement):
        """Add code element"""
        self.elements.append(element)

    def add_relation(self, relation: CodeRelation):
        """Add code relation"""
        self.relations.append(relation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'project_path': self.project_path,
            'language': self.language.value,
            'elements': [element.to_dict() for element in self.elements],
            'relations': [relation.to_dict() for relation in self.relations],
            'packages': self.packages,
            'statistics': self.statistics,
            'dependencies': self.dependencies
        }


class BaseCodeParser(ABC):
    """Abstract base class for code parsers"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_info = ProjectInfo(str(project_path), self.get_language_type())

        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        logger.info(f"Initializing {self.get_language_type().value} code parser: {project_path}")

    @abstractmethod
    def get_language_type(self) -> LanguageType:
        """Get the language type supported by this parser"""
        pass

    @abstractmethod
    def get_file_extensions(self) -> Set[str]:
        """Get supported file extensions"""
        pass

    @abstractmethod
    def parse_file(self, file_path: Path) -> List[CodeElement]:
        """Parse a single file and return list of code elements"""
        pass

    @abstractmethod
    def extract_relations(self, elements: List[CodeElement]) -> List[CodeRelation]:
        """Extract relations from code elements"""
        pass

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported type"""
        return file_path.suffix.lower() in self.get_file_extensions()

    def find_source_files(self) -> List[Path]:
        """Find source code files in the project"""
        source_files = []
        extensions = self.get_file_extensions()

        for ext in extensions:
            source_files.extend(self.project_path.rglob(f"*{ext}"))

        # Filter out unwanted directories
        excluded_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache',
                        'target', 'build', 'dist', '.idea', '.vscode', 'venv',
                        '.venv', 'env', '.env', 'virtualenv', 'workspaces'}

        filtered_files = []
        for file_path in source_files:
            if not any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                filtered_files.append(file_path)

        logger.info(f"Found {len(filtered_files)} {self.get_language_type().value} source files")
        return filtered_files

    def parse_project(self) -> ProjectInfo:
        """Parse the entire project"""
        logger.info(f"Starting to parse {self.get_language_type().value} project: {self.project_path}")

        # Find source files
        source_files = self.find_source_files()

        # Parse each file
        all_elements = []
        for file_path in source_files:
            try:
                elements = self.parse_file(file_path)
                all_elements.extend(elements)
                for element in elements:
                    self.project_info.add_element(element)
                logger.debug(f"Parsed file: {file_path}, extracted {len(elements)} elements")
            except Exception as e:
                logger.warning(f"Failed to parse file {file_path}: {e}")

        # Extract relations
        try:
            relations = self.extract_relations(all_elements)
            for relation in relations:
                self.project_info.add_relation(relation)
            logger.info(f"Extracted {len(relations)} relations")
        except Exception as e:
            logger.warning(f"Failed to extract relations: {e}")

        # Analyze package structure
        self.analyze_package_structure()

        # Generate statistics
        self.generate_statistics()

        logger.info(f"Project parsing complete: {len(all_elements)} elements, {len(self.project_info.relations)} relations")
        return self.project_info

    def analyze_package_structure(self):
        """Analyze package structure"""
        package_stats = {}

        for element in self.project_info.elements:
            if element.package:
                if element.package not in package_stats:
                    package_stats[element.package] = {
                        'classes': 0,
                        'interfaces': 0,
                        'functions': 0,
                        'total_elements': 0
                    }

                package_stats[element.package]['total_elements'] += 1

                if element.element_type == ElementType.CLASS:
                    package_stats[element.package]['classes'] += 1
                elif element.element_type == ElementType.INTERFACE:
                    package_stats[element.package]['interfaces'] += 1
                elif element.element_type in [ElementType.FUNCTION, ElementType.METHOD]:
                    package_stats[element.package]['functions'] += 1

        self.project_info.packages = package_stats

    def generate_statistics(self):
        """Generate project statistics"""
        stats = {
            'total_files': len(self.find_source_files()),
            'total_elements': len(self.project_info.elements),
            'total_relations': len(self.project_info.relations),
            'element_types': {},
            'relation_types': {},
            'packages_count': len(self.project_info.packages)
        }

        # Count element types
        for element in self.project_info.elements:
            element_type = element.element_type.value
            stats['element_types'][element_type] = stats['element_types'].get(element_type, 0) + 1

        # Count relation types
        for relation in self.project_info.relations:
            relation_type = relation.relation_type.value
            stats['relation_types'][relation_type] = stats['relation_types'].get(relation_type, 0) + 1

        self.project_info.statistics = stats

    def save_analysis_result(self, output_path: str = None):
        """Save analysis result"""
        if output_path is None:
            output_path = self.project_path / f"{self.get_language_type().value}_analysis_result.json"

        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.project_info.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Analysis result saved to: {output_path}")
