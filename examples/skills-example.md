---
bundle:
  name: skills-example
  version: 1.0.0
  description: Example bundle demonstrating skills support

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: skills:behaviors/skills

tools:
  - module: tool-skills
    config:
      skills_dirs:
        - .amplifier/skills
        # - ~/anthropic-skills  # Uncomment if you cloned github.com/anthropics/skills
---

# Skills-Enabled Bundle

This bundle demonstrates Amplifier's support for [Anthropic Skills](https://github.com/anthropics/skills) - folders of instructions that agents load dynamically for specialized tasks.

## What This Enables

Skills provide progressive disclosure of domain knowledge:
- List available skills using the load_skill tool
- Load full content only when needed (60-65% token savings)
- Support multiple skill sources (Anthropic + your own)
- Access companion files using skill_directory path returned by load_skill

## Quick Start

### With Test Skills (Included)

```bash
# Copy bundle
cp examples/skills-example.md my-skills-bundle.md

# Copy test skills
mkdir -p .amplifier/skills
cp -r tests/fixtures/skills/* .amplifier/skills/

# Use the bundle
amplifier run --bundle my-skills-bundle.md "List available skills"
```

### With Anthropic Skills (Recommended)

```bash
# Clone Anthropic skills
git clone https://github.com/anthropics/skills ~/anthropic-skills

# Uncomment the ~/anthropic-skills line in this bundle

# Use the bundle
amplifier run --bundle my-skills-bundle.md "List available skills"
```

### Using the Skills Bundle Directly

```bash
# Add the skills bundle
amplifier bundle add git+https://github.com/microsoft/amplifier-module-tool-skills@main

# Use it
amplifier bundle use skills
amplifier run "List available skills"
```

## Workflow

When working with skills:
1. List available skills: `load_skill(list=true)`
2. Load when needed: `load_skill(skill_name="skill-name")`
3. Follow guidelines from loaded skills
4. Skills persist across conversation turns

## Configuration

**Default**: Configured to look in `.amplifier/skills/`

**Multiple sources**: Uncomment `~/anthropic-skills` in the tools config to add Anthropic's skill library

**Custom locations**: Edit `skills_dirs` in the tool-skills config to point to your skill directories

---

@foundation:context/shared/common-system-base.md
