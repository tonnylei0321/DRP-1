"""
Tests for Code Processor Module
"""

import pytest
from pathlib import Path
import tempfile
import os

from code_processor import (
    ParserFactory, LanguageType, ElementType,
    CodeElement, CodeRelation, ProjectInfo
)
from code_processor.python_parser import PythonParser


class TestPythonParser:
    """Tests for Python parser"""

    def test_parse_simple_class(self):
        """Test parsing a simple Python class"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test_module.py"
            test_file.write_text('''
class MyClass:
    """A simple class"""

    def __init__(self, name):
        self.name = name

    def greet(self):
        """Return greeting"""
        return f"Hello, {self.name}"
''')

            parser = PythonParser(tmpdir)
            elements = parser.parse_file(test_file)

            # Should find class and methods
            class_elements = [e for e in elements if e.element_type == ElementType.CLASS]
            method_elements = [e for e in elements if e.element_type == ElementType.METHOD]

            assert len(class_elements) >= 1
            assert class_elements[0].name == "MyClass"

    def test_parse_function(self):
        """Test parsing a standalone function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "functions.py"
            test_file.write_text('''
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

async def fetch_data(url: str) -> dict:
    """Fetch data from URL"""
    pass
''')

            parser = PythonParser(tmpdir)
            elements = parser.parse_file(test_file)

            func_elements = [e for e in elements if e.element_type == ElementType.FUNCTION]
            assert len(func_elements) >= 2

    def test_parse_imports(self):
        """Test parsing import statements"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "imports.py"
            test_file.write_text('''
import os
from pathlib import Path
from typing import List, Dict
''')

            parser = PythonParser(tmpdir)
            elements = parser.parse_file(test_file)

            import_elements = [e for e in elements if e.element_type == ElementType.IMPORT]
            assert len(import_elements) >= 3


class TestParserFactory:
    """Tests for parser factory"""

    def test_detect_python_project(self):
        """Test detecting Python project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Python project indicators
            (Path(tmpdir) / "requirements.txt").write_text("pytest\n")
            (Path(tmpdir) / "main.py").write_text("print('hello')\n")

            language = ParserFactory.detect_project_language(tmpdir)
            assert language == LanguageType.PYTHON

    def test_create_parser(self):
        """Test creating parser"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "main.py").write_text("x = 1\n")

            parser = ParserFactory.create_parser(tmpdir, LanguageType.PYTHON)
            assert parser is not None
            assert parser.get_language_type() == LanguageType.PYTHON


class TestCodeElement:
    """Tests for CodeElement"""

    def test_to_dict(self):
        """Test converting element to dict"""
        element = CodeElement(
            element_type=ElementType.CLASS,
            name="TestClass",
            full_name="module.TestClass",
            file_path="/path/to/file.py",
            line_number=10,
            package="module"
        )

        d = element.to_dict()
        assert d['type'] == 'class'
        assert d['name'] == 'TestClass'
        assert d['full_name'] == 'module.TestClass'
        assert d['line_number'] == 10

    def test_add_child(self):
        """Test adding child elements"""
        parent = CodeElement(ElementType.CLASS, "Parent")
        child = CodeElement(ElementType.METHOD, "method")

        parent.add_child(child)
        assert len(parent.children) == 1
        assert parent.children[0].name == "method"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
