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


class MockCoordinator:
    """Mock coordinator for testing."""

    def __init__(self):
        self.capabilities = {}
        self.mounted_tools = {}
        self.hooks = MockHooks()
        self.config = {}

    def register_capability(self, name: str, value):
        self.capabilities[name] = value

    def get_capability(self, name: str):
        return self.capabilities.get(name)

    def get(self, name: str):
        return None

    async def mount(self, category: str, tool, name: str):
        self.mounted_tools[name] = tool


class MockHooks:
    """Mock hooks system for testing."""

    def __init__(self):
        self.listeners = {}
        self.emitted_events = []
        self.registered_hooks = []

    def on(self, event_name: str, listener):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(listener)

    def register(self, event: str, handler, priority: int = 10, name: str = None):
        self.registered_hooks.append({
            "event": event,
            "handler": handler,
            "priority": priority,
            "name": name,
        })
        self.on(event, handler)

    async def emit(self, event_name: str, data):
        self.emitted_events.append((event_name, data))
        if event_name in self.listeners:
            for listener in self.listeners[event_name]:
                await listener(event_name, data)


class MockMentionResolver:
    """Mock mention resolver capability."""

    def __init__(self, resolve_map: dict[str, Path]):
        self.resolve_map = resolve_map
        self.calls = []

    def resolve(self, mention: str) -> Path | None:
        self.calls.append(mention)
        return self.resolve_map.get(mention)


@pytest.mark.asyncio
async def test_resolve_source_mention_with_resolver(tmp_path):
    """Test _resolve_source resolves @namespace:path via mention_resolver."""
    resolver = MockMentionResolver({"@superpowers:skills": tmp_path})
    coordinator = MockCoordinator()
    coordinator.register_capability("mention_resolver", resolver)

    tool = SkillsTool(config={}, coordinator=coordinator)
    result = await tool._resolve_source("@superpowers:skills")

    assert result == tmp_path
    assert resolver.calls == ["@superpowers:skills"]


@pytest.mark.asyncio
async def test_resolve_source_mention_no_resolver():
    """Test _resolve_source returns None when mention_resolver not available."""
    coordinator = MockCoordinator()
    # No mention_resolver registered

    tool = SkillsTool(config={}, coordinator=coordinator)
    result = await tool._resolve_source("@nonexistent:bundle")

    assert result is None


@pytest.mark.asyncio
async def test_resolve_source_remote_url(tmp_path, monkeypatch):
    """Test _resolve_source resolves git+https:// via resolve_skill_source."""
    expected_path = tmp_path / "cached-skills"
    expected_path.mkdir()

    async def mock_resolve(source, cache_dir=None):
        return expected_path

    monkeypatch.setattr(
        "amplifier_module_tool_skills.resolve_skill_source",
        mock_resolve,
    )

    tool = SkillsTool(config={})
    result = await tool._resolve_source("git+https://github.com/example/skills@main")

    assert result == expected_path


@pytest.mark.asyncio
async def test_resolve_source_remote_url_fails(monkeypatch):
    """Test _resolve_source returns None when remote resolution fails."""

    async def mock_resolve(source, cache_dir=None):
        return None

    monkeypatch.setattr(
        "amplifier_module_tool_skills.resolve_skill_source",
        mock_resolve,
    )

    tool = SkillsTool(config={})
    result = await tool._resolve_source("git+https://github.com/nonexistent/repo@main")

    assert result is None


@pytest.mark.asyncio
async def test_execute_source_discovers_and_merges_skills(tmp_path):
    """Test execute with source param discovers skills and merges them."""
    # Create a source directory with skills
    skill_dir = tmp_path / "new-source" / "cool-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("""---
name: cool-skill
description: A cool new skill
---
# Cool Skill Content""")

    coordinator = MockCoordinator()
    tool = SkillsTool(config={}, coordinator=coordinator)

    # Verify skill doesn't exist yet
    assert "cool-skill" not in tool.skills

    result = await tool.execute({"source": str(tmp_path / "new-source")})

    assert result.success is True
    assert "cool-skill" in tool.skills
    assert "cool-skill" in str(result.output)
