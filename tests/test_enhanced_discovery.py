"""Tests for enhanced skill discovery with new frontmatter fields."""

import pytest
from pathlib import Path

from amplifier_module_tool_skills.discovery import SkillMetadata, discover_skills


# ---------------------------------------------------------------------------
# Mock infrastructure for skill:loaded event tests
# ---------------------------------------------------------------------------


class MockHooks:
    """Mock hooks system that tracks registrations and emitted events."""

    def __init__(self):
        self.registered_hooks = []
        self.emitted_events = []

    def register(
        self, event: str, handler, priority: int = 10, name: str | None = None
    ):
        self.registered_hooks.append(
            {"event": event, "handler": handler, "priority": priority, "name": name}
        )

    async def emit(self, event_name: str, data):
        self.emitted_events.append((event_name, data))


class MockCoordinator:
    """Mock coordinator for testing event emission."""

    def __init__(self):
        self.capabilities = {}
        self.mounted_tools = {}
        self.hooks = MockHooks()
        self.config = {}

    def register_capability(self, name: str, value):
        self.capabilities[name] = value

    def get_capability(self, name: str):
        return self.capabilities.get(name)

    async def mount(self, category: str, tool, name: str):
        self.mounted_tools[name] = tool


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


# ---------------------------------------------------------------------------
# Tests for enriched skill:loaded event (acceptance criteria for task-5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skill_loaded_event_includes_context(tmp_path: Path):
    """skill:loaded event includes context field from metadata."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "ctx-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: ctx-skill
description: Skill with context field
context: fork
---
Body content
"""
    )

    coordinator = MockCoordinator()
    tool = SkillsTool({}, coordinator, resolved_dirs=[tmp_path])  # type: ignore[arg-type]
    await tool._load_skill("ctx-skill")

    events = [e for e in coordinator.hooks.emitted_events if e[0] == "skill:loaded"]
    assert len(events) == 1
    event_data = events[0][1]
    assert "context" in event_data
    assert event_data["context"] == "fork"


@pytest.mark.asyncio
async def test_skill_loaded_event_includes_disable_model_invocation(tmp_path: Path):
    """skill:loaded event includes disable_model_invocation field from metadata."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "dmi-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: dmi-skill
description: Skill with disable-model-invocation
disable-model-invocation: true
---
Body content
"""
    )

    coordinator = MockCoordinator()
    tool = SkillsTool({}, coordinator, resolved_dirs=[tmp_path])  # type: ignore[arg-type]
    await tool._load_skill("dmi-skill")

    events = [e for e in coordinator.hooks.emitted_events if e[0] == "skill:loaded"]
    assert len(events) == 1
    event_data = events[0][1]
    assert "disable_model_invocation" in event_data
    assert event_data["disable_model_invocation"] is True


@pytest.mark.asyncio
async def test_skill_loaded_event_includes_user_invocable(tmp_path: Path):
    """skill:loaded event includes user_invocable field from metadata."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "ui-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: ui-skill
description: Skill with user-invocable false
user-invocable: false
---
Body content
"""
    )

    coordinator = MockCoordinator()
    tool = SkillsTool({}, coordinator, resolved_dirs=[tmp_path])  # type: ignore[arg-type]
    await tool._load_skill("ui-skill")

    events = [e for e in coordinator.hooks.emitted_events if e[0] == "skill:loaded"]
    assert len(events) == 1
    event_data = events[0][1]
    assert "user_invocable" in event_data
    assert event_data["user_invocable"] is False


@pytest.mark.asyncio
async def test_skill_loaded_event_includes_allowed_tools(tmp_path: Path):
    """skill:loaded event includes allowed_tools field from metadata."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "at-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: at-skill
description: Skill with allowed-tools
allowed-tools:
  - bash
  - read_file
---
Body content
"""
    )

    coordinator = MockCoordinator()
    tool = SkillsTool({}, coordinator, resolved_dirs=[tmp_path])  # type: ignore[arg-type]
    await tool._load_skill("at-skill")

    events = [e for e in coordinator.hooks.emitted_events if e[0] == "skill:loaded"]
    assert len(events) == 1
    event_data = events[0][1]
    assert "allowed_tools" in event_data
    assert event_data["allowed_tools"] == ["bash", "read_file"]


@pytest.mark.asyncio
async def test_skill_loaded_event_includes_slash_command(tmp_path: Path):
    """skill:loaded event includes slash_command field (derived from skill name)."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
---
Body content
"""
    )

    coordinator = MockCoordinator()
    tool = SkillsTool({}, coordinator, resolved_dirs=[tmp_path])  # type: ignore[arg-type]
    await tool._load_skill("my-skill")

    events = [e for e in coordinator.hooks.emitted_events if e[0] == "skill:loaded"]
    assert len(events) == 1
    event_data = events[0][1]
    assert "slash_command" in event_data
    assert event_data["slash_command"] == "my-skill"


@pytest.mark.asyncio
async def test_skill_loaded_event_all_enriched_fields_present(tmp_path: Path):
    """skill:loaded event includes all enriched fields with MockCoordinator/MockHooks."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "full-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: full-skill
description: Skill with all enhanced fields
version: 1.2.3
context: fork
disable-model-invocation: true
user-invocable: false
allowed-tools:
  - bash
  - write_file
---
Full skill body content
"""
    )

    coordinator = MockCoordinator()
    tool = SkillsTool({}, coordinator, resolved_dirs=[tmp_path])  # type: ignore[arg-type]
    result = await tool._load_skill("full-skill")

    assert result.success is True

    events = [e for e in coordinator.hooks.emitted_events if e[0] == "skill:loaded"]
    assert len(events) == 1
    event_data = events[0][1]

    # Existing fields still present
    assert event_data["skill_name"] == "full-skill"
    assert event_data["source"] is not None
    assert event_data["content_length"] > 0
    assert event_data["version"] == "1.2.3"
    assert event_data["skill_directory"] is not None
    assert "hooks" in event_data

    # New enriched fields
    assert event_data["context"] == "fork"
    assert event_data["disable_model_invocation"] is True
    assert event_data["user_invocable"] is False
    assert event_data["allowed_tools"] == ["bash", "write_file"]
    assert event_data["slash_command"] == "full-skill"


# ---------------------------------------------------------------------------
# Tests for preprocessing wiring in _load_skill() (acceptance criteria task-7)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_skill_substitutes_skill_dir(tmp_path: Path):
    """${SKILL_DIR} is substituted in loaded inline skill content."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "dir-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: dir-skill
description: Skill with SKILL_DIR placeholder
---
The skill lives at ${SKILL_DIR} and has companion files there.
"""
    )

    tool = SkillsTool({}, None, resolved_dirs=[tmp_path])
    result = await tool._load_skill("dir-skill")

    assert result.success is True
    content = result.output["content"]
    # ${SKILL_DIR} should NOT appear in result
    assert "${SKILL_DIR}" not in content
    # Actual skill directory path should appear
    assert str(skill_dir) in content


@pytest.mark.asyncio
async def test_load_skill_skill_dir_placeholder_replaced_with_actual_path(
    tmp_path: Path,
):
    """The actual skill directory path appears in result content."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "path-skill"
    skill_dir.mkdir()
    expected_path = str(skill_dir)
    (skill_dir / "SKILL.md").write_text(
        """---
name: path-skill
description: Skill to verify path replacement
---
Reference: ${SKILL_DIR}/examples/code.py
"""
    )

    tool = SkillsTool({}, None, resolved_dirs=[tmp_path])
    result = await tool._load_skill("path-skill")

    assert result.success is True
    content = result.output["content"]
    assert f"{expected_path}/examples/code.py" in content


@pytest.mark.asyncio
async def test_load_skill_fork_skill_not_preprocessed(tmp_path: Path):
    """Fork skills (context: fork) are NOT preprocessed in _load_skill()."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "fork-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: fork-skill
description: Fork skill with SKILL_DIR placeholder
context: fork
---
Fork path: ${SKILL_DIR}/data
"""
    )

    tool = SkillsTool({}, None, resolved_dirs=[tmp_path])
    result = await tool._load_skill("fork-skill")

    assert result.success is True
    content = result.output["content"]
    # Fork skills should NOT have ${SKILL_DIR} substituted at this point
    assert "${SKILL_DIR}" in content


@pytest.mark.asyncio
async def test_load_skill_inline_skill_no_placeholders_unaffected(tmp_path: Path):
    """Inline skills without ${SKILL_DIR} are returned unchanged."""
    from amplifier_module_tool_skills import SkillsTool

    skill_dir = tmp_path / "plain-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: plain-skill
description: Plain skill without any placeholders
---
Just plain content here, no substitutions needed.
"""
    )

    tool = SkillsTool({}, None, resolved_dirs=[tmp_path])
    result = await tool._load_skill("plain-skill")

    assert result.success is True
    content = result.output["content"]
    assert "Just plain content here, no substitutions needed." in content
