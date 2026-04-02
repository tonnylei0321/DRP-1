"""
Python Code Parser

Parses Python source code using AST to extract classes, functions, variables,
and their relationships. Supports Python-specific features like decorators,
properties, and generators.
"""

import ast
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import logging

from .base_parser import (
    BaseCodeParser, LanguageType, ElementType, RelationType,
    CodeElement, CodeRelation, ProjectInfo
)

logger = logging.getLogger(__name__)


class PythonParser(BaseCodeParser):
    """Python code parser"""

    def __init__(self, project_path: str):
        super().__init__(project_path)
        self.current_file_path = None
        self.current_module = None
        self.imports = {}

    def get_language_type(self) -> LanguageType:
        return LanguageType.PYTHON

    def get_file_extensions(self) -> Set[str]:
        return {'.py', '.pyw'}

    def parse_file(self, file_path: Path) -> List[CodeElement]:
        """Parse Python file"""
        self.current_file_path = str(file_path)
        self.current_module = self._get_module_name(file_path)
        self.imports = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            elements = []
            visitor = PythonASTVisitor(self)
            visitor.visit(tree)
            elements.extend(visitor.elements)

            logger.debug(f"Parsed Python file {file_path}: {len(elements)} elements")
            return elements

        except SyntaxError as e:
            logger.warning(f"Python syntax error {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse Python file {file_path}: {e}")
            return []

    def extract_relations(self, elements: List[CodeElement]) -> List[CodeRelation]:
        """Extract Python code relations"""
        relations = []

        element_index = {elem.full_name: elem for elem in elements}

        for element in elements:
            # Inheritance relation
            if element.element_type == ElementType.CLASS:
                base_classes = element.extra_attributes.get('base_classes', [])
                for base_class in base_classes:
                    if base_class in element_index:
                        relations.append(CodeRelation(
                            RelationType.INHERITS,
                            element.full_name,
                            base_class,
                            ElementType.CLASS,
                            ElementType.CLASS,
                            f"{element.name} inherits from {base_class}"
                        ))

            # Decorator relation
            decorators = element.extra_attributes.get('decorators', [])
            for decorator in decorators:
                relations.append(CodeRelation(
                    RelationType.DECORATES,
                    decorator,
                    element.full_name,
                    context=f"Decorator {decorator} applied to {element.name}"
                ))

            # Method override relation
            if element.element_type == ElementType.METHOD:
                parent_class = element.extra_attributes.get('parent_class')
                if parent_class and parent_class in element_index:
                    parent_element = element_index[parent_class]
                    base_classes = parent_element.extra_attributes.get('base_classes', [])
                    for base_class in base_classes:
                        base_method_name = f"{base_class}.{element.name}"
                        if base_method_name in element_index:
                            relations.append(CodeRelation(
                                RelationType.OVERRIDES,
                                element.full_name,
                                base_method_name,
                                ElementType.METHOD,
                                ElementType.METHOD,
                                f"{element.name} overrides parent method"
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

            # Import relation
            imports = element.extra_attributes.get('imports', [])
            for import_name in imports:
                relations.append(CodeRelation(
                    RelationType.IMPORTS,
                    element.full_name,
                    import_name,
                    context=f"{element.name} imports {import_name}"
                ))

        logger.info(f"Extracted Python relations: {len(relations)}")
        return relations

    def _get_module_name(self, file_path: Path) -> str:
        """Get module name"""
        try:
            relative_path = file_path.relative_to(self.project_path)
            module_parts = list(relative_path.parts[:-1])
            if relative_path.stem != '__init__':
                module_parts.append(relative_path.stem)
            return '.'.join(module_parts) if module_parts else '__main__'
        except ValueError:
            return file_path.stem


class PythonASTVisitor(ast.NodeVisitor):
    """Python AST visitor"""

    def __init__(self, parser: PythonParser):
        self.parser = parser
        self.elements = []
        self.current_class = None
        self.current_function = None
        self.scope_stack = []

    def visit_Import(self, node: ast.Import):
        """Handle import statement"""
        for alias in node.names:
            import_name = alias.asname if alias.asname else alias.name
            self.parser.imports[import_name] = alias.name

            element = CodeElement(
                ElementType.IMPORT,
                import_name,
                f"{self.parser.current_module}.{import_name}",
                self.parser.current_file_path,
                node.lineno,
                self.parser.current_module,
                imported_module=alias.name
            )
            self.elements.append(element)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from...import statement"""
        module = node.module or ''
        for alias in node.names:
            import_name = alias.asname if alias.asname else alias.name
            full_import = f"{module}.{alias.name}" if module else alias.name
            self.parser.imports[import_name] = full_import

            element = CodeElement(
                ElementType.IMPORT,
                import_name,
                f"{self.parser.current_module}.{import_name}",
                self.parser.current_file_path,
                node.lineno,
                self.parser.current_module,
                imported_module=full_import,
                from_module=module
            )
            self.elements.append(element)

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definition"""
        class_name = node.name
        full_name = f"{self.parser.current_module}.{class_name}"

        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(self._get_attribute_name(base))

        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        # Extract docstring
        docstring = ast.get_docstring(node)

        element = CodeElement(
            ElementType.CLASS,
            class_name,
            full_name,
            self.parser.current_file_path,
            node.lineno,
            self.parser.current_module,
            decorators=decorators,
            docstring=docstring,
            base_classes=base_classes,
            is_abstract=any('ABC' in base or 'abstract' in base.lower() for base in base_classes)
        )

        self.elements.append(element)

        # Enter class scope
        old_class = self.current_class
        self.current_class = element
        self.scope_stack.append(('class', class_name))

        self.generic_visit(node)

        # Restore scope
        self.current_class = old_class
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definition"""
        self._visit_function(node, ElementType.FUNCTION)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definition"""
        self._visit_function(node, ElementType.FUNCTION)

    def _visit_function(self, node, element_type: ElementType):
        """Common logic for function/method definition"""
        func_name = node.name

        if self.current_class:
            element_type = ElementType.METHOD
            full_name = f"{self.current_class.full_name}.{func_name}"
            parent_class = self.current_class.full_name
        else:
            full_name = f"{self.parser.current_module}.{func_name}"
            parent_class = None

        parameters = self._extract_parameters(node.args)
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        return_type = None
        if node.returns:
            return_type = self._get_type_annotation(node.returns)

        docstring = ast.get_docstring(node)

        is_property = any('property' in dec for dec in decorators)
        is_staticmethod = any('staticmethod' in dec for dec in decorators)
        is_classmethod = any('classmethod' in dec for dec in decorators)
        is_constructor = func_name == '__init__'
        is_async = isinstance(node, ast.AsyncFunctionDef)

        element = CodeElement(
            ElementType.PROPERTY if is_property else element_type,
            func_name,
            full_name,
            self.parser.current_file_path,
            node.lineno,
            self.parser.current_module,
            decorators=decorators,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            parent_class=parent_class,
            is_property=is_property,
            is_staticmethod=is_staticmethod,
            is_classmethod=is_classmethod,
            is_constructor=is_constructor,
            is_async=is_async
        )

        self.elements.append(element)

        if self.current_class:
            self.current_class.add_child(element)

        old_function = self.current_function
        self.current_function = element
        self.scope_stack.append(('function', func_name))

        self._analyze_function_calls(node, element)
        self.generic_visit(node)

        self.current_function = old_function
        self.scope_stack.pop()

    def visit_Assign(self, node: ast.Assign):
        """Handle assignment statement"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id

                if self.current_class and not self.current_function:
                    element_type = ElementType.FIELD
                    full_name = f"{self.current_class.full_name}.{var_name}"
                    parent_class = self.current_class.full_name
                elif self.current_function:
                    if var_name.startswith('self.'):
                        element_type = ElementType.FIELD
                        full_name = f"{self.current_class.full_name}.{var_name[5:]}"
                        parent_class = self.current_class.full_name
                    else:
                        element_type = ElementType.VARIABLE
                        full_name = f"{self.current_function.full_name}.{var_name}"
                        parent_class = None
                else:
                    element_type = ElementType.VARIABLE
                    full_name = f"{self.parser.current_module}.{var_name}"
                    parent_class = None

                type_annotation = None
                if hasattr(node, 'type_comment') and node.type_comment:
                    type_annotation = node.type_comment

                element = CodeElement(
                    element_type,
                    var_name,
                    full_name,
                    self.parser.current_file_path,
                    node.lineno,
                    self.parser.current_module,
                    parent_class=parent_class,
                    type_annotation=type_annotation,
                    is_class_variable=self.current_class and not self.current_function
                )

                self.elements.append(element)

                if self.current_class and element_type == ElementType.FIELD:
                    self.current_class.add_child(element)

        self.generic_visit(node)

    def _extract_parameters(self, args: ast.arguments) -> List[Dict[str, Any]]:
        """Extract function parameters"""
        parameters = []

        for i, arg in enumerate(args.args):
            param_info = {
                'name': arg.arg,
                'type': self._get_type_annotation(arg.annotation) if arg.annotation else None,
                'default': None,
                'kind': 'positional'
            }

            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default_index = i - defaults_offset
                param_info['default'] = self._get_default_value(args.defaults[default_index])

            parameters.append(param_info)

        if args.vararg:
            parameters.append({
                'name': args.vararg.arg,
                'type': self._get_type_annotation(args.vararg.annotation) if args.vararg.annotation else None,
                'kind': 'var_positional'
            })

        if args.kwarg:
            parameters.append({
                'name': args.kwarg.arg,
                'type': self._get_type_annotation(args.kwarg.annotation) if args.kwarg.annotation else None,
                'kind': 'var_keyword'
            })

        return parameters

    def _get_type_annotation(self, annotation) -> str:
        """Get type annotation string"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_name(annotation)
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_type_annotation(annotation.value)}[{self._get_type_annotation(annotation.slice)}]"
        else:
            return str(annotation)

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute access name"""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attribute_name(decorator)
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return str(decorator)

    def _get_default_value(self, node) -> str:
        """Get default value string representation"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        else:
            return str(node)

    def _analyze_function_calls(self, node: ast.FunctionDef, element: CodeElement):
        """Analyze function calls in function body"""
        called_functions = []

        class CallVisitor(ast.NodeVisitor):
            def __init__(self, parent_visitor):
                self.parent_visitor = parent_visitor

            def visit_Call(self, call_node):
                if isinstance(call_node.func, ast.Name):
                    called_functions.append(call_node.func.id)
                elif isinstance(call_node.func, ast.Attribute):
                    called_functions.append(self.parent_visitor._get_attribute_name(call_node.func))
                self.generic_visit(call_node)

        call_visitor = CallVisitor(self)
        call_visitor.visit(node)

        element.extra_attributes['called_functions'] = called_functions
