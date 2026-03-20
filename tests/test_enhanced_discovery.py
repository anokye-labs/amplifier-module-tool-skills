"""Tests for enhanced skill discovery with new frontmatter fields."""

from pathlib import Path

from amplifier_module_tool_skills.discovery import SkillMetadata, discover_skills


def test_skill_metadata_enhanced_fields_defaults():
    """SkillMetadata has all 7 new fields with correct defaults."""
    metadata = SkillMetadata(
        name="test-skill",
        description="A test skill",
        path=Path("/skills/test-skill/SKILL.md"),
        source="/skills",
    )

    assert metadata.context is None
    assert metadata.agent is None
    assert metadata.disable_model_invocation is False
    assert metadata.user_invocable is True
    assert metadata.model is None
    assert metadata.model_role is None
    assert metadata.provider_preferences is None


def test_discover_skills_parses_enhanced_frontmatter(tmp_path: Path):
    """discover_skills() correctly parses enhanced frontmatter fields."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A skill with enhanced fields
context: fork
agent: foundation:explorer
disable-model-invocation: true
user-invocable: false
model: claude-opus-4-5
model_role: coding
provider_preferences:
  - provider: anthropic
    model: claude-opus-4-5
---
Body content
"""
    )

    skills = discover_skills(tmp_path)
    assert "my-skill" in skills

    skill = skills["my-skill"]
    assert skill.context == "fork"
    assert skill.agent == "foundation:explorer"
    assert skill.disable_model_invocation is True
    assert skill.user_invocable is False
    assert skill.model == "claude-opus-4-5"
    assert skill.model_role == "coding"
    assert skill.provider_preferences == [
        {"provider": "anthropic", "model": "claude-opus-4-5"}
    ]


def test_discover_skills_backward_compatible(tmp_path: Path):
    """Existing skills without enhanced fields still work."""
    skill_dir = tmp_path / "old-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: old-skill
description: A legacy skill without enhanced fields
version: 1.0.0
---
Body content
"""
    )

    skills = discover_skills(tmp_path)
    assert "old-skill" in skills

    skill = skills["old-skill"]
    assert skill.name == "old-skill"
    assert skill.description == "A legacy skill without enhanced fields"
    assert skill.version == "1.0.0"
    # Enhanced fields should have defaults
    assert skill.context is None
    assert skill.agent is None
    assert skill.disable_model_invocation is False
    assert skill.user_invocable is True
    assert skill.model is None
    assert skill.model_role is None
    assert skill.provider_preferences is None


def test_discover_skills_model_role_as_list(tmp_path: Path):
    """model_role can be a list (fallback chain)."""
    skill_dir = tmp_path / "multi-model-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: multi-model-skill
description: A skill with model_role as a list
model_role:
  - reasoning
  - coding
  - general
---
Body content
"""
    )

    skills = discover_skills(tmp_path)
    assert "multi-model-skill" in skills

    skill = skills["multi-model-skill"]
    assert isinstance(skill.model_role, list)
    assert skill.model_role == ["reasoning", "coding", "general"]


def test_discover_skills_snake_case_keys(tmp_path: Path):
    """discover_skills() supports both hyphen-case and snake_case keys."""
    skill_dir = tmp_path / "snake-case-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: snake-case-skill
description: A skill using snake_case keys
disable_model_invocation: true
user_invocable: false
---
Body content
"""
    )

    skills = discover_skills(tmp_path)
    assert "snake-case-skill" in skills

    skill = skills["snake-case-skill"]
    assert skill.disable_model_invocation is True
    assert skill.user_invocable is False
