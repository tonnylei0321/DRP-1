"""
Java Code Parser

Parses Java source code using javalang library to extract classes, interfaces,
methods, fields, and their relationships.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

from .base_parser import (
    BaseCodeParser, LanguageType, ElementType, RelationType,
    CodeElement, CodeRelation, ProjectInfo
)

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling set, datetime and other non-serializable objects"""
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


class JavaParser(BaseCodeParser):
    """Java code parser for extracting Java project structure"""

    def __init__(self, project_path: str):
        if not JAVALANG_AVAILABLE:
            raise ImportError("javalang library is required for Java parsing. Install with: pip install javalang")
        super().__init__(project_path)

    def get_language_type(self) -> LanguageType:
        return LanguageType.JAVA

    def get_file_extensions(self) -> Set[str]:
        return {'.java'}

    def parse_file(self, file_path: Path) -> List[CodeElement]:
        """Parse a single Java file"""
        try:
            file_elements_dict = self._parse_java_file(file_path)
            code_elements = []
            for element_dict in file_elements_dict:
                element = CodeElement(
                    element_type=self._map_element_type(element_dict['type']),
                    name=element_dict['name'],
                    full_name=element_dict.get('full_name', element_dict['name']),
                    file_path=str(file_path),
                    line_number=element_dict.get('line_number', 0),
                    package=element_dict.get('package', ''),
                    modifiers=element_dict.get('modifiers', [])
                )
                element.extra_attributes.update(element_dict)
                code_elements.append(element)
            return code_elements
        except Exception as e:
            logger.error(f"Failed to parse file: {file_path} - {e}")
            return []

    def extract_relations(self, elements: List[CodeElement]) -> List[CodeRelation]:
        """Extract relations between code elements"""
        relations = []

        for element in elements:
            metadata = element.extra_attributes

            # Inheritance relation
            if metadata.get('extends'):
                relation = CodeRelation(
                    relation_type=RelationType.EXTENDS,
                    source=element.name,
                    target=metadata['extends'],
                    source_type=element.element_type,
                    context=f"{element.name} extends {metadata['extends']}"
                )
                relations.append(relation)

            # Implementation relation
            for interface in metadata.get('implements', []):
                relation = CodeRelation(
                    relation_type=RelationType.IMPLEMENTS,
                    source=element.name,
                    target=interface,
                    source_type=element.element_type,
                    context=f"{element.name} implements interface {interface}"
                )
                relations.append(relation)

            # Import relation
            for import_path in metadata.get('imports', []):
                relation = CodeRelation(
                    relation_type=RelationType.IMPORTS,
                    source=element.name,
                    target=import_path,
                    source_type=element.element_type,
                    context=f"{element.name} imports {import_path}"
                )
                relations.append(relation)

        return relations

    def _map_element_type(self, java_type: str) -> ElementType:
        """Map Java type to generic element type"""
        type_mapping = {
            'class': ElementType.CLASS,
            'interface': ElementType.INTERFACE,
            'enum': ElementType.ENUM,
            'method': ElementType.METHOD,
            'field': ElementType.FIELD,
            'package': ElementType.PACKAGE
        }
        return type_mapping.get(java_type, ElementType.CLASS)

    def _parse_java_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Java file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return []

        try:
            tree = javalang.parse.parse(content)
        except Exception as e:
            logger.warning(f"AST parsing failed {file_path}: {e}, trying basic extraction")
            return self._extract_basic_info(file_path, content)

        elements = []
        relative_path = file_path.relative_to(self.project_path)

        # Extract package info
        package_name = tree.package.name if tree.package else "default"

        # Extract imports
        imports = []
        if tree.imports:
            for imp in tree.imports:
                imports.append(imp.path)

        # Extract classes
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            class_info = self._extract_class_info(node, package_name, relative_path, imports)
            elements.append(class_info)

        # Extract interfaces
        for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
            interface_info = self._extract_interface_info(node, package_name, relative_path, imports)
            elements.append(interface_info)

        # Extract enums
        for path, node in tree.filter(javalang.tree.EnumDeclaration):
            enum_info = self._extract_enum_info(node, package_name, relative_path, imports)
            elements.append(enum_info)

        return elements

    def _extract_class_info(self, node, package_name: str, relative_path: Path, imports: List[str]) -> Dict[str, Any]:
        """Extract class information"""
        class_info = {
            'type': 'class',
            'name': node.name,
            'full_name': f"{package_name}.{node.name}",
            'package': package_name,
            'file_path': str(relative_path),
            'modifiers': node.modifiers if node.modifiers else [],
            'extends': node.extends.name if node.extends else None,
            'implements': [impl.name for impl in node.implements] if node.implements else [],
            'javadoc': node.documentation,
            'imports': imports,
            'methods': [],
            'fields': [],
            'inner_classes': [],
            'constructors': [],
            'annotations': []
        }

        # Extract annotations
        if hasattr(node, 'annotations') and node.annotations:
            class_info['annotations'] = [ann.name for ann in node.annotations]

        # Extract methods
        for method_path, method_node in node.filter(javalang.tree.MethodDeclaration):
            method_info = self._extract_method_info(method_node)
            class_info['methods'].append(method_info)

        # Extract constructors
        for constructor_path, constructor_node in node.filter(javalang.tree.ConstructorDeclaration):
            constructor_info = self._extract_constructor_info(constructor_node)
            class_info['constructors'].append(constructor_info)

        # Extract fields
        for field_path, field_node in node.filter(javalang.tree.FieldDeclaration):
            for declarator in field_node.declarators:
                field_info = self._extract_field_info(field_node, declarator)
                class_info['fields'].append(field_info)

        # Extract inner classes
        for inner_path, inner_node in node.filter(javalang.tree.ClassDeclaration):
            if inner_node != node:
                inner_class_info = {
                    'name': inner_node.name,
                    'type': 'inner_class',
                    'modifiers': inner_node.modifiers if inner_node.modifiers else []
                }
                class_info['inner_classes'].append(inner_class_info)

        return class_info

    def _extract_interface_info(self, node, package_name: str, relative_path: Path, imports: List[str]) -> Dict[str, Any]:
        """Extract interface information"""
        interface_info = {
            'type': 'interface',
            'name': node.name,
            'full_name': f"{package_name}.{node.name}",
            'package': package_name,
            'file_path': str(relative_path),
            'modifiers': node.modifiers if node.modifiers else [],
            'extends': [ext.name for ext in node.extends] if node.extends else [],
            'javadoc': node.documentation,
            'imports': imports,
            'methods': [],
            'annotations': []
        }

        if hasattr(node, 'annotations') and node.annotations:
            interface_info['annotations'] = [ann.name for ann in node.annotations]

        for method_path, method_node in node.filter(javalang.tree.MethodDeclaration):
            method_info = self._extract_method_info(method_node)
            interface_info['methods'].append(method_info)

        return interface_info

    def _extract_enum_info(self, node, package_name: str, relative_path: Path, imports: List[str]) -> Dict[str, Any]:
        """Extract enum information"""
        enum_info = {
            'type': 'enum',
            'name': node.name,
            'full_name': f"{package_name}.{node.name}",
            'package': package_name,
            'file_path': str(relative_path),
            'modifiers': node.modifiers if node.modifiers else [],
            'javadoc': node.documentation,
            'imports': imports,
            'constants': [],
            'methods': [],
            'annotations': []
        }

        for constant_path, constant_node in node.filter(javalang.tree.EnumConstantDeclaration):
            enum_info['constants'].append(constant_node.name)

        for method_path, method_node in node.filter(javalang.tree.MethodDeclaration):
            method_info = self._extract_method_info(method_node)
            enum_info['methods'].append(method_info)

        return enum_info

    def _extract_method_info(self, method_node) -> Dict[str, Any]:
        """Extract method information"""
        method_info = {
            'name': method_node.name,
            'return_type': str(method_node.return_type) if method_node.return_type else 'void',
            'parameters': [],
            'modifiers': method_node.modifiers if method_node.modifiers else [],
            'javadoc': method_node.documentation,
            'throws': [str(throw) for throw in method_node.throws] if method_node.throws else [],
            'annotations': []
        }

        if method_node.parameters:
            for param in method_node.parameters:
                param_info = {
                    'name': param.name,
                    'type': str(param.type),
                    'modifiers': param.modifiers if param.modifiers else []
                }
                method_info['parameters'].append(param_info)

        if hasattr(method_node, 'annotations') and method_node.annotations:
            method_info['annotations'] = [ann.name for ann in method_node.annotations]

        return method_info

    def _extract_constructor_info(self, constructor_node) -> Dict[str, Any]:
        """Extract constructor information"""
        constructor_info = {
            'name': constructor_node.name,
            'parameters': [],
            'modifiers': constructor_node.modifiers if constructor_node.modifiers else [],
            'javadoc': constructor_node.documentation,
            'throws': [str(throw) for throw in constructor_node.throws] if constructor_node.throws else [],
            'annotations': []
        }

        if constructor_node.parameters:
            for param in constructor_node.parameters:
                param_info = {
                    'name': param.name,
                    'type': str(param.type),
                    'modifiers': param.modifiers if param.modifiers else []
                }
                constructor_info['parameters'].append(param_info)

        return constructor_info

    def _extract_field_info(self, field_node, declarator) -> Dict[str, Any]:
        """Extract field information"""
        field_info = {
            'name': declarator.name,
            'type': str(field_node.type),
            'modifiers': field_node.modifiers if field_node.modifiers else [],
            'javadoc': field_node.documentation,
            'annotations': []
        }

        if hasattr(field_node, 'annotations') and field_node.annotations:
            field_info['annotations'] = [ann.name for ann in field_node.annotations]

        return field_info

    def _extract_basic_info(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Extract basic info when AST parsing fails"""
        elements = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            if self._is_class_declaration(line):
                class_name = self._extract_class_name(line)
                if class_name:
                    elements.append({
                        'type': 'class',
                        'name': class_name,
                        'file_path': str(file_path.relative_to(self.project_path)),
                        'line_number': i + 1,
                        'raw_content': line,
                        'package': 'unknown',
                        'methods': [],
                        'fields': []
                    })

            elif self._is_interface_declaration(line):
                interface_name = self._extract_interface_name(line)
                if interface_name:
                    elements.append({
                        'type': 'interface',
                        'name': interface_name,
                        'file_path': str(file_path.relative_to(self.project_path)),
                        'line_number': i + 1,
                        'raw_content': line,
                        'package': 'unknown',
                        'methods': []
                    })

        return elements

    def _is_class_declaration(self, line: str) -> bool:
        return ('class ' in line and
                not line.strip().startswith('//') and
                not line.strip().startswith('*') and
                ('{' in line or line.endswith('{')))

    def _is_interface_declaration(self, line: str) -> bool:
        return ('interface ' in line and
                not line.strip().startswith('//') and
                not line.strip().startswith('*'))

    def _extract_class_name(self, line: str) -> Optional[str]:
        try:
            parts = line.split()
            class_index = -1
            for i, part in enumerate(parts):
                if part == 'class':
                    class_index = i
                    break

            if class_index >= 0 and class_index + 1 < len(parts):
                class_name = parts[class_index + 1]
                if '<' in class_name:
                    class_name = class_name.split('<')[0]
                if '{' in class_name:
                    class_name = class_name.split('{')[0]
                return class_name.strip()
        except Exception:
            pass
        return None

    def _extract_interface_name(self, line: str) -> Optional[str]:
        try:
            parts = line.split()
            interface_index = -1
            for i, part in enumerate(parts):
                if part == 'interface':
                    interface_index = i
                    break

            if interface_index >= 0 and interface_index + 1 < len(parts):
                interface_name = parts[interface_index + 1]
                if '<' in interface_name:
                    interface_name = interface_name.split('<')[0]
                if '{' in interface_name:
                    interface_name = interface_name.split('{')[0]
                return interface_name.strip()
        except Exception:
            pass
        return None
