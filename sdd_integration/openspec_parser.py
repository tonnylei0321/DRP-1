"""
OpenSpec Parser

Parses OpenSpec documents (proposal.md, design.md, tasks.md) to extract
structured data for the R&D ontology.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Requirement:
    """Represents a requirement from proposal.md"""
    change_id: str
    title: str
    rationale: str = ""
    scope: str = ""
    impact: str = ""
    affected_specs: List[str] = field(default_factory=list)
    affected_code: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)


@dataclass
class Design:
    """Represents a design from design.md"""
    change_id: str
    title: str
    decisions: List[Dict[str, str]] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    data_flow: str = ""


@dataclass
class Task:
    """Represents a task from tasks.md"""
    change_id: str
    index: int
    text: str
    completed: bool = False
    file_paths: List[str] = field(default_factory=list)
    phase: str = ""


class OpenSpecParser:
    """Parser for OpenSpec documents"""

    def __init__(self, openspec_dir: str = "openspec"):
        self.openspec_dir = Path(openspec_dir)

    def parse_change(self, change_id: str) -> Dict[str, Any]:
        """Parse all documents for a change"""
        change_dir = self.openspec_dir / "changes" / change_id

        if not change_dir.exists():
            raise ValueError(f"Change directory not found: {change_dir}")

        result = {
            'change_id': change_id,
            'requirement': None,
            'design': None,
            'tasks': []
        }

        # Parse proposal.md
        proposal_path = change_dir / "proposal.md"
        if proposal_path.exists():
            result['requirement'] = self.parse_proposal(proposal_path, change_id)

        # Parse design.md
        design_path = change_dir / "design.md"
        if design_path.exists():
            result['design'] = self.parse_design(design_path, change_id)

        # Parse tasks.md
        tasks_path = change_dir / "tasks.md"
        if tasks_path.exists():
            result['tasks'] = self.parse_tasks(tasks_path, change_id)

        return result

    def parse_proposal(self, path: Path, change_id: str) -> Requirement:
        """Parse proposal.md into Requirement"""
        content = path.read_text(encoding='utf-8')

        # Extract title from first heading
        title_match = re.search(r'^#\s+(?:Change:\s*)?(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else change_id

        # Extract Why section
        rationale = self._extract_section(content, 'Why')

        # Extract What Changes section
        scope = self._extract_section(content, 'What Changes')

        # Extract Impact section
        impact = self._extract_section(content, 'Impact')

        # Extract affected specs from Impact
        affected_specs = []
        specs_match = re.search(r'Affected specs?:\s*(.+?)(?:\n|$)', impact, re.IGNORECASE)
        if specs_match:
            affected_specs = [s.strip() for s in specs_match.group(1).split(',')]

        # Extract affected code from Impact
        affected_code = []
        code_match = re.search(r'Affected code:\s*(.+?)(?:\n|$)', impact, re.IGNORECASE)
        if code_match:
            affected_code = [c.strip() for c in code_match.group(1).split(',')]

        # Extract breaking changes
        breaking_changes = re.findall(r'\*\*BREAKING\*\*[:\s]*(.+?)(?:\n|$)', content)

        return Requirement(
            change_id=change_id,
            title=title,
            rationale=rationale,
            scope=scope,
            impact=impact,
            affected_specs=affected_specs,
            affected_code=affected_code,
            breaking_changes=breaking_changes
        )

    def parse_design(self, path: Path, change_id: str) -> Design:
        """Parse design.md into Design"""
        content = path.read_text(encoding='utf-8')

        # Extract title
        title_match = re.search(r'^#\s+(?:Design:\s*)?(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f"Design for {change_id}"

        # Extract architecture decisions
        decisions = []
        ad_pattern = r'###\s+AD-\d+:\s*(.+?)\n\n\*\*Decision\*\*:\s*(.+?)(?=\n\n|\Z)'
        for match in re.finditer(ad_pattern, content, re.DOTALL):
            decisions.append({
                'title': match.group(1).strip(),
                'decision': match.group(2).strip()[:500]
            })

        # Extract component names from headers
        components = re.findall(r'###\s+(.+?)\s*(?:Module|Component|Class)', content)

        # Extract data flow section
        data_flow = self._extract_section(content, 'Data Flow')

        return Design(
            change_id=change_id,
            title=title,
            decisions=decisions,
            components=components,
            data_flow=data_flow
        )

    def parse_tasks(self, path: Path, change_id: str) -> List[Task]:
        """Parse tasks.md into Task list"""
        content = path.read_text(encoding='utf-8')
        tasks = []

        # Track current phase
        current_phase = ""
        task_index = 0

        for line in content.split('\n'):
            # Check for phase headers
            phase_match = re.match(r'^##\s+(?:Phase\s+\d+:\s*)?(.+)$', line)
            if phase_match:
                current_phase = phase_match.group(1).strip()
                continue

            # Check for task items
            task_match = re.match(r'^-\s+\[([ xX])\]\s+(.+)$', line)
            if task_match:
                completed = task_match.group(1).lower() == 'x'
                task_text = task_match.group(2).strip()

                # Extract file paths from task text
                file_paths = self._extract_file_paths(task_text)

                tasks.append(Task(
                    change_id=change_id,
                    index=task_index,
                    text=task_text,
                    completed=completed,
                    file_paths=file_paths,
                    phase=current_phase
                ))
                task_index += 1

        return tasks

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a markdown section"""
        # Match section header and content until next section or end
        pattern = rf'^##\s+{section_name}\s*\n(.*?)(?=^##\s+|\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_file_paths(self, text: str) -> List[str]:
        """Extract file paths from text"""
        paths = []

        # Match common file path patterns
        patterns = [
            r'`([^`]+\.[a-z]+)`',  # Backtick-quoted paths
            r'(\w+/[\w/]+\.\w+)',  # Unix-style paths
            r'(\w+\.\w+)',  # Simple filenames with extension
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                path = match.group(1)
                # Filter out common non-file patterns
                if not any(x in path.lower() for x in ['http', 'www', 'example']):
                    paths.append(path)

        return list(set(paths))

    def list_changes(self) -> List[str]:
        """List all change IDs"""
        changes_dir = self.openspec_dir / "changes"
        if not changes_dir.exists():
            return []

        return [
            d.name for d in changes_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.') and d.name != 'archive'
        ]

    def get_active_changes(self) -> List[Dict[str, Any]]:
        """Get all active changes with their parsed data"""
        changes = []
        for change_id in self.list_changes():
            try:
                change_data = self.parse_change(change_id)
                changes.append(change_data)
            except Exception as e:
                logger.warning(f"Failed to parse change {change_id}: {e}")
        return changes
