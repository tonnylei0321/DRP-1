"""
Tests for OpenSpec Parser
"""

import pytest
from pathlib import Path
import tempfile

from sdd_integration import OpenSpecParser, Requirement, Design, Task


class TestOpenSpecParser:
    """Tests for OpenSpec parser"""

    def test_parse_proposal(self):
        """Test parsing proposal.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create openspec structure
            changes_dir = Path(tmpdir) / "openspec" / "changes" / "test-change"
            changes_dir.mkdir(parents=True)

            proposal = changes_dir / "proposal.md"
            proposal.write_text('''# Change: Add New Feature

## Why

We need this feature because it improves user experience.

## What Changes

- Add new API endpoint
- Update database schema
- **BREAKING** Remove old endpoint

## Impact

- Affected specs: user-management
- Affected code: api/users.py, models/user.py
''')

            parser = OpenSpecParser(str(Path(tmpdir) / "openspec"))
            req = parser.parse_proposal(proposal, "test-change")

            assert req.change_id == "test-change"
            assert "Add New Feature" in req.title
            assert "user experience" in req.rationale
            assert len(req.breaking_changes) >= 1

    def test_parse_tasks(self):
        """Test parsing tasks.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            changes_dir = Path(tmpdir) / "openspec" / "changes" / "test-change"
            changes_dir.mkdir(parents=True)

            tasks = changes_dir / "tasks.md"
            tasks.write_text('''# Tasks

## Phase 1: Setup

- [x] Create `api/users.py`
- [ ] Update `models/user.py`

## Phase 2: Implementation

- [ ] Implement endpoint
- [ ] Add tests
''')

            parser = OpenSpecParser(str(Path(tmpdir) / "openspec"))
            task_list = parser.parse_tasks(tasks, "test-change")

            assert len(task_list) == 4
            assert task_list[0].completed == True
            assert task_list[1].completed == False
            assert "api/users.py" in task_list[0].file_paths

    def test_list_changes(self):
        """Test listing changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            openspec_dir = Path(tmpdir) / "openspec" / "changes"
            openspec_dir.mkdir(parents=True)

            (openspec_dir / "change-1").mkdir()
            (openspec_dir / "change-2").mkdir()
            (openspec_dir / "archive").mkdir()  # Should be excluded

            parser = OpenSpecParser(str(Path(tmpdir) / "openspec"))
            changes = parser.list_changes()

            assert "change-1" in changes
            assert "change-2" in changes
            assert "archive" not in changes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
