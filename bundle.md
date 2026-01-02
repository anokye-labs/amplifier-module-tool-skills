---
bundle:
  name: skills
  version: 1.0.0
  description: Anthropic Skills support for Amplifier

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-skills
    source: git+https://github.com/microsoft/amplifier-module-tool-skills@main
---

# Skills Bundle

Load domain knowledge from Anthropic Skills with progressive disclosure.

## What Are Skills?

Skills are domain knowledge packages following the [Anthropic Skills specification](https://github.com/anthropics/skills). They provide structured information that agents can discover and load on demand, minimizing context usage through progressive disclosure:

- **Level 1 (Metadata)**: Name + description (~100 tokens) - always visible via list/search
- **Level 2 (Content)**: Full markdown body (~1-5k tokens) - loaded on demand
- **Level 3 (References)**: Additional files (0 tokens until accessed via read_file)

## Available Tool

### load_skill

Discover and load skills from configured directories.

**Operations:**
- `load_skill(list=true)` - List all available skills
- `load_skill(search="pattern")` - Filter by keyword
- `load_skill(info="skill-name")` - Get metadata only
- `load_skill(skill_name="skill-name")` - Load full content

## Usage Examples

**List available skills:**
```
load_skill(list=true)
```

**Search for specific skills:**
```
load_skill(search="python")
```

**Load a skill:**
```
load_skill(skill_name="example-skill")
```

## Configuration

Skills are discovered from these locations by default:
1. `.amplifier/skills/` (workspace)
2. `~/.amplifier/skills/` (user home)
3. `AMPLIFIER_SKILLS_DIR` environment variable

### Override in Your Bundle

To specify custom skill directories:

```yaml
tools:
  - module: tool-skills
    config:
      skills_dirs:
        - /custom/path/to/skills
        - /another/path
```

### Multi-Source Priority

When multiple directories contain the same skill name, the first match wins (priority order matches the list order).

## Creating Skills

Skills use a simple markdown format with YAML frontmatter:

```markdown
---
name: my-skill
description: Brief description of what this skill provides
---

# Skill Content

Detailed information here...
```

Place `SKILL.md` files in any configured skills directory.

For the complete specification, see the [Anthropic Skills repository](https://github.com/anthropics/skills).

---

@foundation:context/shared/common-system-base.md
