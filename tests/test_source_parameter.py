"""Tests for the load_skill source parameter feature."""

import pytest
from pathlib import Path
from amplifier_module_tool_skills import SkillsTool


def test_input_schema_includes_source():
    """Test that input_schema advertises the 'source' parameter."""
    tool = SkillsTool(config={})
    schema = tool.input_schema
    assert "source" in schema["properties"]
    assert schema["properties"]["source"]["type"] == "string"
    assert "description" in schema["properties"]["source"]


@pytest.mark.asyncio
async def test_resolve_source_local_path_exists(tmp_path):
    """Test _resolve_source returns path for existing local directory."""
    # Create a directory with a SKILL.md so it's a plausible skills dir
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: Test skill
---
# Test""")

    tool = SkillsTool(config={})
    result = await tool._resolve_source(str(tmp_path))
    assert result is not None
    assert result == tmp_path.resolve()


@pytest.mark.asyncio
async def test_resolve_source_local_path_not_exists():
    """Test _resolve_source returns None for nonexistent path."""
    tool = SkillsTool(config={})
    result = await tool._resolve_source("/nonexistent/path/that/does/not/exist")
    assert result is None
