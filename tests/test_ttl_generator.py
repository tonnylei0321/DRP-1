"""
Tests for TTL Generator
"""

import pytest
from pathlib import Path

from code_processor import CodeElement, CodeRelation, ProjectInfo, ElementType, RelationType, LanguageType
from rd_ontology import TTLGenerator


class TestTTLGenerator:
    """Tests for TTL generator"""

    def test_generate_stable_id(self):
        """Test stable ID generation"""
        generator = TTLGenerator()

        element = CodeElement(
            element_type=ElementType.CLASS,
            name="TestClass",
            full_name="module.TestClass",
            file_path="/path/to/file.py",
            line_number=10
        )

        id1 = generator.generate_stable_id(element)
        id2 = generator.generate_stable_id(element)

        # Same element should produce same ID
        assert id1 == id2
        assert len(id1) == 16  # SHA1 truncated to 16 chars

    def test_element_to_ttl(self):
        """Test converting element to TTL"""
        generator = TTLGenerator()

        element = CodeElement(
            element_type=ElementType.CLASS,
            name="TestClass",
            full_name="module.TestClass",
            file_path="/path/to/file.py",
            line_number=10,
            package="module",
            modifiers=["public"],
            docstring="A test class"
        )

        ttl = generator.element_to_ttl(element, "python")

        assert "CodeClass" in ttl
        assert "TestClass" in ttl
        assert "module.TestClass" in ttl
        assert "python" in ttl

    def test_relation_to_ttl(self):
        """Test converting relation to TTL"""
        generator = TTLGenerator()

        # First generate element IRIs
        element1 = CodeElement(ElementType.CLASS, "Child", "module.Child")
        element2 = CodeElement(ElementType.CLASS, "Parent", "module.Parent")

        generator.generate_instance_iri(element1)
        generator.generate_instance_iri(element2)

        relation = CodeRelation(
            relation_type=RelationType.INHERITS,
            source="module.Child",
            target="module.Parent",
            source_type=ElementType.CLASS,
            target_type=ElementType.CLASS
        )

        ttl = generator.relation_to_ttl(relation)

        assert "inherits" in ttl
        assert "." in ttl  # Should end with period

    def test_project_to_ttl(self):
        """Test converting project to TTL"""
        generator = TTLGenerator()

        project = ProjectInfo("/test/project", LanguageType.PYTHON)

        element = CodeElement(
            element_type=ElementType.CLASS,
            name="TestClass",
            full_name="module.TestClass"
        )
        project.add_element(element)

        ttl = generator.project_to_ttl(project)

        assert "@prefix owl:" in ttl
        assert "@prefix rdfs:" in ttl
        assert "Code Elements" in ttl
        assert "TestClass" in ttl


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
