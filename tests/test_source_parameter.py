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
