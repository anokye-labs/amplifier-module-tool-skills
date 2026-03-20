"""Tests for the /batch power skill in amplifier-bundle-skills."""

from pathlib import Path

from amplifier_module_tool_skills.discovery import discover_skills, extract_skill_body

# Path to the bundle's skills directory, relative to this test file's location.
# This file is at: amplifier-module-tool-skills/tests/test_batch_power_skill.py
# The bundle is at: amplifier-bundle-skills/
BUNDLE_SKILLS_DIR = (
    Path(__file__).parent.parent.parent / "amplifier-bundle-skills" / "skills"
)

BATCH_SKILL_PATH = BUNDLE_SKILLS_DIR / "batch" / "SKILL.md"


def test_batch_skill_file_exists():
    """SKILL.md file must exist at amplifier-bundle-skills/skills/batch/SKILL.md."""
    assert BATCH_SKILL_PATH.exists(), f"SKILL.md not found at {BATCH_SKILL_PATH}"


def test_batch_skill_is_discoverable():
    """Skill must be discoverable via discover_skills()."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    assert "batch" in skills, (
        f"'batch' skill not found via discover_skills(). Found: {list(skills.keys())}"
    )


def test_batch_skill_context_is_fork():
    """metadata.context must be 'fork'."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["batch"]
    assert skill.context == "fork", (
        f"Expected context='fork', got context={skill.context!r}"
    )


def test_batch_skill_disable_model_invocation_is_true():
    """metadata.disable_model_invocation must be True."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["batch"]
    assert skill.disable_model_invocation is True, (
        f"Expected disable_model_invocation=True, got {skill.disable_model_invocation!r}"
    )


def test_batch_skill_model_role_is_reasoning():
    """metadata.model_role must be 'reasoning'."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["batch"]
    assert skill.model_role == "reasoning", (
        f"Expected model_role='reasoning', got model_role={skill.model_role!r}"
    )


def test_batch_skill_user_invocable_is_true():
    """metadata.user_invocable must be True."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["batch"]
    assert skill.user_invocable is True, (
        f"Expected user_invocable=True, got user_invocable={skill.user_invocable!r}"
    )


def test_batch_skill_body_contains_arguments_placeholder():
    """Body must contain $ARGUMENTS placeholder for change description."""
    body = extract_skill_body(BATCH_SKILL_PATH)
    assert body is not None, "Could not extract body from SKILL.md"
    assert "$ARGUMENTS" in body, (
        "Body does not contain '$ARGUMENTS' placeholder for change description"
    )


def test_batch_skill_description_mentions_parallel():
    """Skill description must reference parallel execution / work units."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["batch"]
    desc_lower = skill.description.lower()
    assert "parallel" in desc_lower or "work unit" in desc_lower, (
        f"Description does not mention parallel execution or work units: {skill.description!r}"
    )


def test_batch_skill_body_describes_decomposition():
    """Body must describe decomposing change into work units."""
    body = extract_skill_body(BATCH_SKILL_PATH)
    assert body is not None
    body_lower = body.lower()
    assert "decompose" in body_lower or "work unit" in body_lower, (
        "Body does not describe decomposing change into work units"
    )


def test_batch_skill_body_mentions_delegate_agents():
    """Body must mention delegate agents for parallel execution."""
    body = extract_skill_body(BATCH_SKILL_PATH)
    assert body is not None
    body_lower = body.lower()
    assert "delegate" in body_lower or "agent" in body_lower, (
        "Body does not mention delegate agents"
    )


def test_batch_skill_body_mentions_git_branches():
    """Body must mention git branches for work units."""
    body = extract_skill_body(BATCH_SKILL_PATH)
    assert body is not None
    body_lower = body.lower()
    assert "branch" in body_lower or "batch/" in body_lower, (
        "Body does not mention git branches for work units"
    )
