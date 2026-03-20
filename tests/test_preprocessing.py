"""Tests for preprocessing pipeline — string substitution and shell execution."""

from pathlib import Path

import pytest

from amplifier_module_tool_skills.preprocessing import preprocess


@pytest.mark.asyncio
async def test_arguments_substitution():
    """$ARGUMENTS is replaced with the full argument string."""
    body = "Use these arguments: $ARGUMENTS"
    result = await preprocess(body, skill_dir=Path("/some/skill"), arguments="foo bar")
    assert result == "Use these arguments: foo bar"


@pytest.mark.asyncio
async def test_positional_substitution():
    """$0, $1, $2 are replaced with positional arguments."""
    body = "First: $0, Second: $1, Third: $2"
    result = await preprocess(
        body, skill_dir=Path("/some/skill"), arguments="alpha beta gamma"
    )
    assert result == "First: alpha, Second: beta, Third: gamma"


@pytest.mark.asyncio
async def test_skill_dir_substitution():
    """${SKILL_DIR} is replaced with the skill directory path."""
    body = "Skill lives at: ${SKILL_DIR}"
    skill_dir = Path("/path/to/my-skill")
    result = await preprocess(body, skill_dir=skill_dir, arguments=None)
    assert result == f"Skill lives at: {skill_dir}"


@pytest.mark.asyncio
async def test_missing_arguments_become_empty_string():
    """Missing/beyond-provided positional args and $ARGUMENTS with None become empty string."""
    body = "Args: $ARGUMENTS, Pos: $0, Missing: $1"
    result = await preprocess(body, skill_dir=Path("/some/skill"), arguments=None)
    assert result == "Args: , Pos: , Missing: "


@pytest.mark.asyncio
async def test_combined_substitutions():
    """Combined substitutions work together in a single body."""
    body = "Dir: ${SKILL_DIR}, All: $ARGUMENTS, First: $0"
    skill_dir = Path("/skills/my-skill")
    result = await preprocess(body, skill_dir=skill_dir, arguments="hello world")
    assert result == f"Dir: {skill_dir}, All: hello world, First: hello"


@pytest.mark.asyncio
async def test_body_without_markers_unchanged():
    """Body without any substitution markers passes through unchanged."""
    body = "This is plain text with no markers."
    result = await preprocess(body, skill_dir=Path("/some/skill"), arguments="ignored")
    assert result == "This is plain text with no markers."


@pytest.mark.asyncio
async def test_shell_command_execution(tmp_path):
    """!`command` patterns are executed and replaced with stdout output."""
    body = "Version: !`echo hello`"
    result = await preprocess(body, skill_dir=tmp_path, arguments=None)
    assert result == "Version: hello"
