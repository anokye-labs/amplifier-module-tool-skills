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


@pytest.mark.asyncio
async def test_shell_echo_hello_world(tmp_path):
    """!`echo hello-world` is replaced with 'hello-world' (hyphenated output)."""
    body = "!`echo hello-world`"
    result = await preprocess(body, skill_dir=tmp_path, arguments=None)
    assert result == "hello-world"


@pytest.mark.asyncio
async def test_shell_failed_command_injects_error(tmp_path):
    """Failed shell commands inject error inline with '[preprocessing error:' prefix."""
    body = "Result: !`exit 1`"
    result = await preprocess(body, skill_dir=tmp_path, arguments=None)
    assert "[preprocessing error:" in result


@pytest.mark.asyncio
async def test_shell_command_uses_skill_dir_as_cwd(tmp_path):
    """Shell commands execute with skill_dir as working directory (can cat files from there)."""
    # Write a file in the skill dir
    (tmp_path / "hello.txt").write_text("from-skill-dir\n")
    body = "!`cat hello.txt`"
    result = await preprocess(body, skill_dir=tmp_path, arguments=None)
    assert result == "from-skill-dir"


@pytest.mark.asyncio
async def test_shell_multiple_patterns_all_replaced(tmp_path):
    """Multiple !`command` patterns in a body are all replaced."""
    body = "A=!`echo alpha` B=!`echo beta`"
    result = await preprocess(body, skill_dir=tmp_path, arguments=None)
    assert result == "A=alpha B=beta"


@pytest.mark.asyncio
async def test_shell_substitution_runs_before_shell_execution(tmp_path):
    """String substitution ($ARGUMENTS etc.) runs before shell execution."""
    # $ARGUMENTS is substituted to "world", then !`echo world` runs
    body = "!`echo $ARGUMENTS`"
    result = await preprocess(body, skill_dir=tmp_path, arguments="world")
    assert result == "world"


@pytest.mark.asyncio
async def test_normal_backticks_not_affected(tmp_path):
    """Normal backticks like `code` are not treated as shell commands."""
    body = "Use `some_function()` in your code."
    result = await preprocess(body, skill_dir=tmp_path, arguments=None)
    assert result == "Use `some_function()` in your code."
