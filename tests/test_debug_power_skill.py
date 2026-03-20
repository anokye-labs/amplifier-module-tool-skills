"""Tests for the /debug power skill in amplifier-bundle-skills."""

from pathlib import Path

from amplifier_module_tool_skills.discovery import discover_skills, extract_skill_body

# Path to the bundle's skills directory, relative to this test file's location.
# This file is at: amplifier-module-tool-skills/tests/test_debug_power_skill.py
# The bundle is at: amplifier-bundle-skills/
BUNDLE_SKILLS_DIR = (
    Path(__file__).parent.parent.parent / "amplifier-bundle-skills" / "skills"
)

DEBUG_SKILL_PATH = BUNDLE_SKILLS_DIR / "debug" / "SKILL.md"


def test_debug_skill_file_exists():
    """SKILL.md file must exist at amplifier-bundle-skills/skills/debug/SKILL.md."""
    assert DEBUG_SKILL_PATH.exists(), f"SKILL.md not found at {DEBUG_SKILL_PATH}"


def test_debug_skill_is_discoverable():
    """Skill must be discoverable via discover_skills()."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    assert "debug" in skills, (
        f"'debug' skill not found via discover_skills(). Found: {list(skills.keys())}"
    )


def test_debug_skill_context_is_fork():
    """metadata.context must be 'fork'."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["debug"]
    assert skill.context == "fork", (
        f"Expected context='fork', got context={skill.context!r}"
    )


def test_debug_skill_disable_model_invocation_is_true():
    """metadata.disable_model_invocation must be True."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["debug"]
    assert skill.disable_model_invocation is True, (
        f"Expected disable_model_invocation=True, got {skill.disable_model_invocation!r}"
    )


def test_debug_skill_model_role_is_general():
    """metadata.model_role must be 'general'."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["debug"]
    assert skill.model_role == "general", (
        f"Expected model_role='general', got model_role={skill.model_role!r}"
    )


def test_debug_skill_user_invocable_is_true():
    """metadata.user_invocable must be True."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["debug"]
    assert skill.user_invocable is True, (
        f"Expected user_invocable=True, got user_invocable={skill.user_invocable!r}"
    )


def test_debug_skill_body_contains_arguments_placeholder():
    """Body must contain $ARGUMENTS placeholder for specific question."""
    body = extract_skill_body(DEBUG_SKILL_PATH)
    assert body is not None, "Could not extract body from SKILL.md"
    assert "$ARGUMENTS" in body, (
        "Body does not contain '$ARGUMENTS' placeholder for specific question"
    )


def test_debug_skill_description_mentions_diagnostics():
    """Skill description must reference diagnostics / troubleshoot."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    skill = skills["debug"]
    desc_lower = skill.description.lower()
    assert "diagnostic" in desc_lower or "troubleshoot" in desc_lower, (
        f"Description does not mention diagnostics or troubleshoot: {skill.description!r}"
    )


def test_debug_skill_body_describes_diagnostic_steps():
    """Body must describe a diagnostic process with gather/analyze/report steps."""
    body = extract_skill_body(DEBUG_SKILL_PATH)
    assert body is not None
    body_lower = body.lower()
    # Should mention gathering diagnostics
    assert "gather" in body_lower or "diagnostic" in body_lower, (
        "Body does not describe gathering diagnostics"
    )
    # Should mention analysis
    assert "analyz" in body_lower or "analysis" in body_lower, (
        "Body does not describe analysis step"
    )
    # Should mention reporting
    assert "report" in body_lower or "section" in body_lower, (
        "Body does not describe report step"
    )


def test_debug_skill_body_mentions_environment():
    """Body must describe environment diagnostics (env vars, working directory)."""
    body = extract_skill_body(DEBUG_SKILL_PATH)
    assert body is not None
    body_lower = body.lower()
    assert "environment" in body_lower or "env" in body_lower, (
        "Body does not mention environment diagnostics"
    )


def test_debug_skill_body_mentions_structured_report_sections():
    """Body must reference structured report sections (Environment/Config/Issues/Recommendations)."""
    body = extract_skill_body(DEBUG_SKILL_PATH)
    assert body is not None
    body_lower = body.lower()
    # Must mention at least two of the four sections
    sections = ["environment", "configuration", "issues", "recommendation"]
    found = sum(1 for s in sections if s in body_lower)
    assert found >= 2, (
        f"Body does not mention structured report sections. "
        f"Found only {found} of: {sections}"
    )


def test_all_four_skills_discoverable_together():
    """All 4 skills (image-vision + simplify + batch + debug) must be discoverable together."""
    skills = discover_skills(BUNDLE_SKILLS_DIR)
    expected_skills = {"image-vision", "simplify", "batch", "debug"}
    missing = expected_skills - set(skills.keys())
    assert not missing, f"Missing skills: {missing}. Found: {list(skills.keys())}"
