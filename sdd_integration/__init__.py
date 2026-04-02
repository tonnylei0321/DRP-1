"""
SDD Integration Module

Integrates code analysis with SDD (Specification-Driven Development) workflow.
"""

from .openspec_parser import OpenSpecParser, Requirement, Design, Task
from .linker import (
    CodeRequirementLinker,
    TestCodeLinker,
    Link,
    SemanticLinker,
    LinkValidator,
    TraceabilityQuery,
)

__all__ = [
    "OpenSpecParser",
    "Requirement",
    "Design",
    "Task",
    "CodeRequirementLinker",
    "TestCodeLinker",
    "Link",
    "SemanticLinker",
    "LinkValidator",
    "TraceabilityQuery",
]
