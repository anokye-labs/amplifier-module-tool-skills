"""Tests for SkillsDiscovery class."""

from pathlib import Path


from amplifier_module_tool_skills import SkillsDiscovery
from amplifier_module_tool_skills.discovery import SkillMetadata


def _make_skill(
    name: str,
    description: str,
    user_invocable: bool = False,
    context: str | None = None,
) -> SkillMetadata:
    """Helper to create test SkillMetadata."""
    return SkillMetadata(
        name=name,
        description=description,
        path=Path(f"/fake/{name}/SKILL.md"),
        source="/fake",
        user_invocable=user_invocable,
        context=context,
    )


class TestSkillsDiscoveryListSkills:
    """Tests for SkillsDiscovery.list_skills()."""

    def test_returns_name_description_pairs(self):
        """list_skills() returns (name, description) tuples."""
        skills = {
            "my-skill": _make_skill("my-skill", "A test skill"),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.list_skills()
        assert ("my-skill", "A test skill") in result

    def test_sorted_alphabetically(self):
        """list_skills() returns pairs sorted alphabetically by name."""
        skills = {
            "zebra-skill": _make_skill("zebra-skill", "Zebra"),
            "apple-skill": _make_skill("apple-skill", "Apple"),
            "mango-skill": _make_skill("mango-skill", "Mango"),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.list_skills()
        names = [name for name, _ in result]
        assert names == sorted(names)

    def test_includes_all_skills(self):
        """list_skills() includes all skills in the dict."""
        skills = {
            "skill-a": _make_skill("skill-a", "A"),
            "skill-b": _make_skill("skill-b", "B"),
            "skill-c": _make_skill("skill-c", "C"),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.list_skills()
        assert len(result) == 3

    def test_handles_empty(self):
        """list_skills() returns empty list when no skills."""
        discovery = SkillsDiscovery({})
        result = discovery.list_skills()
        assert result == []


class TestSkillsDiscoveryFind:
    """Tests for SkillsDiscovery.find()."""

    def test_finds_existing_skill(self):
        """find() returns SkillMetadata for existing skill."""
        skill = _make_skill("my-skill", "A test skill")
        skills = {"my-skill": skill}
        discovery = SkillsDiscovery(skills)
        result = discovery.find("my-skill")
        assert result is skill

    def test_returns_none_for_missing(self):
        """find() returns None for non-existent skill."""
        discovery = SkillsDiscovery({"my-skill": _make_skill("my-skill", "Test")})
        result = discovery.find("nonexistent")
        assert result is None


class TestSkillsDiscoveryGetShortcuts:
    """Tests for SkillsDiscovery.get_shortcuts()."""

    def test_returns_only_user_invocable(self):
        """get_shortcuts() returns only skills with user_invocable=True as keys."""
        skills = {
            "public-skill": _make_skill("public-skill", "Public", user_invocable=True),
            "private-skill": _make_skill(
                "private-skill", "Private", user_invocable=False
            ),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.get_shortcuts()
        assert "public-skill" in result
        assert "private-skill" not in result

    def test_has_required_keys(self):
        """Each shortcut value dict has 'description' and 'context' keys."""
        skills = {
            "public-skill": _make_skill("public-skill", "Public", user_invocable=True),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.get_shortcuts()
        assert len(result) == 1
        shortcut = result["public-skill"]
        assert "description" in shortcut
        assert "context" in shortcut

    def test_description_matches_metadata(self):
        """Shortcut description matches SkillMetadata.description."""
        skills = {
            "my-skill": _make_skill("my-skill", "My description", user_invocable=True),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.get_shortcuts()
        assert result["my-skill"]["description"] == "My description"

    def test_empty_when_none_user_invocable(self):
        """get_shortcuts() returns empty dict when no user_invocable skills."""
        skills = {
            "private-skill": _make_skill(
                "private-skill", "Private", user_invocable=False
            ),
        }
        discovery = SkillsDiscovery(skills)
        result = discovery.get_shortcuts()
        assert result == {}
