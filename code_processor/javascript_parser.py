"""
JavaScript/TypeScript Code Parser

Parses JS/TS source code using regex-based parsing to extract classes, functions,
components, interfaces, and their relationships. Supports ES6+ syntax and
TypeScript features.
"""

import re
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import logging

from .base_parser import (
    BaseCodeParser, LanguageType, ElementType, RelationType,
    CodeElement, CodeRelation, ProjectInfo
)

logger = logging.getLogger(__name__)


class JavaScriptParser(BaseCodeParser):
    """JavaScript code parser"""

    def __init__(self, project_path: str):
        super().__init__(project_path)
        self.current_file_path = None
        self.current_module = None
        self.imports = {}
        self.exports = {}

    def get_language_type(self) -> LanguageType:
        return LanguageType.JAVASCRIPT

    def get_file_extensions(self) -> Set[str]:
        return {'.js', '.jsx', '.mjs'}

    def parse_file(self, file_path: Path) -> List[CodeElement]:
        """Parse JavaScript file"""
        self.current_file_path = str(file_path)
        self.current_module = self._get_module_name(file_path)
        self.imports = {}
        self.exports = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            elements = []

            elements.extend(self._parse_imports(content))
            elements.extend(self._parse_exports(content))
            elements.extend(self._parse_functions(content))
            elements.extend(self._parse_classes(content))
            elements.extend(self._parse_react_components(content))
            elements.extend(self._parse_variables(content))

            logger.debug(f"Parsed JavaScript file {file_path}: {len(elements)} elements")
            return elements

        except Exception as e:
            logger.error(f"Failed to parse JavaScript file {file_path}: {e}")
            return []

    def extract_relations(self, elements: List[CodeElement]) -> List[CodeRelation]:
        """Extract JavaScript code relations"""
        relations = []

        element_index = {elem.full_name: elem for elem in elements}

        for element in elements:
            # Inheritance relation
            if element.element_type == ElementType.CLASS:
                extends_class = element.extra_attributes.get('extends')
                if extends_class and extends_class in element_index:
                    relations.append(CodeRelation(
                        RelationType.EXTENDS,
                        element.full_name,
                        extends_class,
                        ElementType.CLASS,
                        ElementType.CLASS,
                        f"{element.name} extends {extends_class}"
                    ))

            # Import relation
            if element.element_type == ElementType.IMPORT:
                imported_module = element.extra_attributes.get('imported_module')
                if imported_module:
                    relations.append(CodeRelation(
                        RelationType.IMPORTS,
                        element.full_name,
                        imported_module,
                        context=f"imports {imported_module}"
                    ))

            # Function call relation
            called_functions = element.extra_attributes.get('called_functions', [])
            for called_func in called_functions:
                if called_func in element_index:
                    relations.append(CodeRelation(
                        RelationType.CALLS,
                        element.full_name,
                        called_func,
                        context=f"{element.name} calls {called_func}"
                    ))

            # React component relation
            if element.element_type == ElementType.COMPONENT:
                used_hooks = element.extra_attributes.get('used_hooks', [])
                for hook in used_hooks:
                    relations.append(CodeRelation(
                        RelationType.USES,
                        element.full_name,
                        hook,
                        ElementType.COMPONENT,
                        ElementType.HOOK,
                        f"{element.name} uses Hook {hook}"
                    ))

        logger.info(f"Extracted JavaScript relations: {len(relations)}")
        return relations

    def _get_module_name(self, file_path: Path) -> str:
        """Get module name"""
        try:
            relative_path = file_path.relative_to(self.project_path)
            return str(relative_path.with_suffix(''))
        except ValueError:
            return file_path.stem

    def _parse_imports(self, content: str) -> List[CodeElement]:
        """Parse import statements"""
        elements = []

        import_patterns = [
            r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+\{\s*([^}]+)\s*\}\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+\*\s+as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                if len(match.groups()) == 2:
                    imported_name = match.group(1)
                    module_path = match.group(2)
                elif len(match.groups()) == 1:
                    imported_name = match.group(1)
                    module_path = match.group(1)
                else:
                    continue

                line_number = content[:match.start()].count('\n') + 1

                element = CodeElement(
                    ElementType.IMPORT,
                    imported_name,
                    f"{self.current_module}.{imported_name}",
                    self.current_file_path,
                    line_number,
                    self.current_module,
                    imported_module=module_path,
                    import_type='es6'
                )
                elements.append(element)
                self.imports[imported_name] = module_path

        # CommonJS require
        require_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'
        for match in re.finditer(require_pattern, content, re.MULTILINE):
            imported_name = match.group(1)
            module_path = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            element = CodeElement(
                ElementType.IMPORT,
                imported_name,
                f"{self.current_module}.{imported_name}",
                self.current_file_path,
                line_number,
                self.current_module,
                imported_module=module_path,
                import_type='commonjs'
            )
            elements.append(element)
            self.imports[imported_name] = module_path

        return elements

    def _parse_exports(self, content: str) -> List[CodeElement]:
        """Parse export statements"""
        elements = []

        export_patterns = [
            r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)',
            r'export\s+\{\s*([^}]+)\s*\}',
            r'export\s+default\s+(\w+)',
        ]

        for pattern in export_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                exported_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1

                element = CodeElement(
                    ElementType.EXPORT,
                    exported_name,
                    f"{self.current_module}.{exported_name}",
                    self.current_file_path,
                    line_number,
                    self.current_module,
                    is_default='default' in match.group(0)
                )
                elements.append(element)
                self.exports[exported_name] = True

        return elements

    def _parse_functions(self, content: str) -> List[CodeElement]:
        """Parse function definitions"""
        elements = []

        function_patterns = [
            r'function\s+(\w+)\s*\(([^)]*)\)\s*\{',
            r'(?:const|let|var)\s+(\w+)\s*=\s*function\s*\(([^)]*)\)\s*\{',
            r'(?:const|let|var)\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>\s*\{',
            r'(?:const|let|var)\s+(\w+)\s*=\s*async\s*\(([^)]*)\)\s*=>\s*\{',
            r'async\s+function\s+(\w+)\s*\(([^)]*)\)\s*\{',
        ]

        for pattern in function_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                func_name = match.group(1)
                params_str = match.group(2) if len(match.groups()) > 1 else ''
                line_number = content[:match.start()].count('\n') + 1

                parameters = self._parse_parameters(params_str)
                is_async = 'async' in match.group(0)
                is_arrow = '=>' in match.group(0)

                element = CodeElement(
                    ElementType.FUNCTION,
                    func_name,
                    f"{self.current_module}.{func_name}",
                    self.current_file_path,
                    line_number,
                    self.current_module,
                    parameters=parameters,
                    is_async=is_async,
                    is_arrow_function=is_arrow
                )
                elements.append(element)

        return elements

    def _parse_classes(self, content: str) -> List[CodeElement]:
        """Parse class definitions"""
        elements = []

        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'

        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            extends_class = match.group(2) if match.group(2) else None
            line_number = content[:match.start()].count('\n') + 1

            element = CodeElement(
                ElementType.CLASS,
                class_name,
                f"{self.current_module}.{class_name}",
                self.current_file_path,
                line_number,
                self.current_module,
                extends=extends_class
            )
            elements.append(element)

            class_body_start = match.end()
            class_body = self._extract_class_body(content, class_body_start)
            if class_body:
                methods = self._parse_class_methods(class_body, element)
                elements.extend(methods)

        return elements

    def _parse_react_components(self, content: str) -> List[CodeElement]:
        """Parse React components"""
        elements = []

        component_patterns = [
            r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*return\s*\(',
            r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*return\s*\(',
            r'(?:const|let|var)\s+(\w+)\s*=\s*React\.forwardRef',
        ]

        for pattern in component_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                component_name = match.group(1)

                if not component_name[0].isupper():
                    continue

                line_number = content[:match.start()].count('\n') + 1

                component_body = match.group(0)
                used_hooks = self._extract_hooks(component_body)

                element = CodeElement(
                    ElementType.COMPONENT,
                    component_name,
                    f"{self.current_module}.{component_name}",
                    self.current_file_path,
                    line_number,
                    self.current_module,
                    used_hooks=used_hooks,
                    is_react_component=True
                )
                elements.append(element)

        return elements

    def _parse_variables(self, content: str) -> List[CodeElement]:
        """Parse variable declarations"""
        elements = []

        var_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*([^;,\n]+)'

        for match in re.finditer(var_pattern, content, re.MULTILINE):
            var_name = match.group(1)
            var_value = match.group(2).strip()
            line_number = content[:match.start()].count('\n') + 1

            if any(keyword in var_value for keyword in ['function', 'class', '=>', 'React.']):
                continue

            element = CodeElement(
                ElementType.VARIABLE,
                var_name,
                f"{self.current_module}.{var_name}",
                self.current_file_path,
                line_number,
                self.current_module,
                initial_value=var_value[:50]
            )
            elements.append(element)

        return elements

    def _parse_parameters(self, params_str: str) -> List[Dict[str, Any]]:
        """Parse function parameters"""
        if not params_str.strip():
            return []

        parameters = []
        param_parts = [p.strip() for p in params_str.split(',')]

        for param in param_parts:
            if not param:
                continue

            if '=' in param:
                name, default = param.split('=', 1)
                name = name.strip()
                default = default.strip()
            else:
                name = param
                default = None

            is_destructured = '{' in name or '[' in name

            param_info = {
                'name': name,
                'default': default,
                'is_destructured': is_destructured
            }
            parameters.append(param_info)

        return parameters

    def _extract_class_body(self, content: str, start_pos: int) -> str:
        """Extract class body content"""
        brace_count = 1
        pos = start_pos

        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1

        if brace_count == 0:
            return content[start_pos:pos-1]
        return ""

    def _parse_class_methods(self, class_body: str, class_element: CodeElement) -> List[CodeElement]:
        """Parse class methods"""
        elements = []

        method_patterns = [
            r'(\w+)\s*\([^)]*\)\s*\{',
            r'async\s+(\w+)\s*\([^)]*\)\s*\{',
            r'static\s+(\w+)\s*\([^)]*\)\s*\{',
        ]

        for pattern in method_patterns:
            for match in re.finditer(pattern, class_body, re.MULTILINE):
                method_name = match.group(1)

                if method_name == 'constructor':
                    continue

                is_async = 'async' in match.group(0)
                is_static = 'static' in match.group(0)

                element = CodeElement(
                    ElementType.METHOD,
                    method_name,
                    f"{class_element.full_name}.{method_name}",
                    self.current_file_path,
                    None,
                    self.current_module,
                    parent_class=class_element.full_name,
                    is_async=is_async,
                    is_static=is_static
                )
                elements.append(element)
                class_element.add_child(element)

        return elements

    def _extract_hooks(self, component_body: str) -> List[str]:
        """Extract React Hooks"""
        hooks = []

        hook_pattern = r'use\w+\s*\('

        for match in re.finditer(hook_pattern, component_body):
            hook_name = match.group(0).replace('(', '').strip()
            if hook_name not in hooks:
                hooks.append(hook_name)

        return hooks


class TypeScriptParser(JavaScriptParser):
    """TypeScript code parser"""

    def get_language_type(self) -> LanguageType:
        return LanguageType.TYPESCRIPT

    def get_file_extensions(self) -> Set[str]:
        return {'.ts', '.tsx'}

    def parse_file(self, file_path: Path) -> List[CodeElement]:
        """Parse TypeScript file"""
        elements = super().parse_file(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            elements.extend(self._parse_interfaces(content))
            elements.extend(self._parse_type_aliases(content))
            elements.extend(self._parse_enums(content))

            logger.debug(f"Parsed TypeScript file {file_path}: {len(elements)} elements")
            return elements

        except Exception as e:
            logger.error(f"Failed to parse TypeScript file {file_path}: {e}")
            return elements

    def _parse_interfaces(self, content: str) -> List[CodeElement]:
        """Parse TypeScript interfaces"""
        elements = []

        interface_pattern = r'interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{'

        for match in re.finditer(interface_pattern, content, re.MULTILINE):
            interface_name = match.group(1)
            extends_interfaces = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            extends_list = []
            if extends_interfaces:
                extends_list = [name.strip() for name in extends_interfaces.split(',')]

            element = CodeElement(
                ElementType.INTERFACE,
                interface_name,
                f"{self.current_module}.{interface_name}",
                self.current_file_path,
                line_number,
                self.current_module,
                extends_interfaces=extends_list
            )
            elements.append(element)

        return elements

    def _parse_type_aliases(self, content: str) -> List[CodeElement]:
        """Parse type aliases"""
        elements = []

        type_pattern = r'type\s+(\w+)\s*=\s*([^;]+);?'

        for match in re.finditer(type_pattern, content, re.MULTILINE):
            type_name = match.group(1)
            type_definition = match.group(2).strip()
            line_number = content[:match.start()].count('\n') + 1

            element = CodeElement(
                ElementType.VARIABLE,
                type_name,
                f"{self.current_module}.{type_name}",
                self.current_file_path,
                line_number,
                self.current_module,
                type_definition=type_definition,
                is_type_alias=True
            )
            elements.append(element)

        return elements

    def _parse_enums(self, content: str) -> List[CodeElement]:
        """Parse enums"""
        elements = []

        enum_pattern = r'enum\s+(\w+)\s*\{'

        for match in re.finditer(enum_pattern, content, re.MULTILINE):
            enum_name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            element = CodeElement(
                ElementType.ENUM,
                enum_name,
                f"{self.current_module}.{enum_name}",
                self.current_file_path,
                line_number,
                self.current_module
            )
            elements.append(element)

        return elements
