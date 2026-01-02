# Bundle Integration Implementation Plan

**Date**: 2026-01-02
**Goal**: Add bundle integration layer to amplifier-module-tool-skills
**Target**: PR to microsoft/amplifier-module-tool-skills

---

## Context

The skills module is technically excellent and aligned with current Amplifier architecture, but missing the **bundle integration layer** that is now the primary composition mechanism in Amplifier.

### What We're Adding

1. **behaviors/skills.yaml** - Makes skills capability composable
2. **bundle.md** - Thin bundle showcasing the pattern
3. **Updated README** - Bundle-first approach (profiles being deprecated)
4. **Updated example** - Convert to bundle format

### Key Principles

- **Documentation URLs**: Use `microsoft/amplifier-module-tool-skills` in all docs
- **Testing URLs**: Use `robotdad/amplifier-module-tool-skills` for local testing only
- **No profile references**: Profiles are being deprecated/removed
- **Follow foundation patterns**: Match amplifier-foundation's behavior pattern exactly

---

## Files to Create

### 1. behaviors/skills.yaml

**Purpose**: Enable other bundles to include skills capability

**Pattern**: Follow foundation's `behaviors/todo-reminder.yaml` model

**Content**:
```yaml
bundle:
  name: skills-behavior
  version: 1.0.0
  description: Anthropic Skills support with progressive disclosure

tools:
  - module: tool-skills
    source: git+https://github.com/microsoft/amplifier-module-tool-skills@main
    config:
      # Default: uses ~/.amplifier/skills and .amplifier/skills
      # Users can override via bundle composition or settings.yaml
```

### 2. bundle.md

**Purpose**: Showcase skills as a complete bundle

**Pattern**: Thin bundle including foundation + skills behavior

**Content**:
```markdown
---
bundle:
  name: skills
  version: 1.0.0
  description: Anthropic Skills support for Amplifier

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: skills:behaviors/skills
---

# Skills Bundle

Load domain knowledge from Anthropic Skills with progressive disclosure.

## Available Tool

- **load_skill** - Discover and load skills from configured directories

## Usage Examples

List available skills:
```
load_skill(list=true)
```

Load a specific skill:
```
load_skill(skill_name="example-skill")
```

## Configuration

Skills are discovered from:
1. `.amplifier/skills/` (workspace)
2. `~/.amplifier/skills/` (user home)
3. `AMPLIFIER_SKILLS_DIR` environment variable

Override in your bundle:
```yaml
tools:
  - module: tool-skills
    config:
      skills_dirs:
        - /custom/path/to/skills
```

---

@foundation:context/shared/common-system-base.md
```

### 3. README.md Updates

**Changes needed**:
1. Move "Bundle Configuration" section to be FIRST (before project-specific)
2. Add "For Bundle Authors" section showing behavior inclusion
3. Remove/minimize profile references (being deprecated)
4. Update examples to show bundle usage first

**New section to add**:
```markdown
## For Bundle Authors

To include skills in your custom bundle:

```yaml
includes:
  - bundle: git+https://github.com/microsoft/amplifier-module-tool-skills@main#subdirectory=behaviors/skills.yaml
```

Or if you've already installed the skills bundle:

```yaml
includes:
  - bundle: skills:behaviors/skills
```
```

### 4. examples/skills-example.md

**Convert from profile to bundle**:
- Change frontmatter from `profile:` to `bundle:`
- Update includes to use bundle pattern
- Remove profile-specific references

---

## Implementation Steps

### Phase 1: Create New Files
- [x] Fork repo to robotdad
- [x] Add robotdad remote
- [x] Create ai_working/bundle-integration-plan.md
- [ ] Create behaviors/skills.yaml
- [ ] Create bundle.md
- [ ] Create examples/bundle-example.md (new file showing thin bundle pattern)

### Phase 2: Update Existing Files
- [ ] Update README.md structure (bundle-first)
- [ ] Convert examples/skills-example.md to bundle format
- [ ] Review TESTING.md for profile references

### Phase 3: Testing
- [ ] Test bundle loading with robotdad URL
- [ ] Verify behavior inclusion works
- [ ] Test configuration override patterns

### Phase 4: PR Preparation
- [ ] Update all URLs to microsoft in documentation
- [ ] Create comprehensive commit message
- [ ] Verify no profile references remain
- [ ] Create PR description

---

## Testing Approach

### Local Testing URLs
For testing, use:
```yaml
source: git+https://github.com/robotdad/amplifier-module-tool-skills@bundle-integration
```

### Documentation URLs
In all docs, use:
```yaml
source: git+https://github.com/microsoft/amplifier-module-tool-skills@main
```

### Test Bundle
Create `ai_working/test-bundle.md`:
```yaml
bundle:
  name: test-skills
includes:
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-skills@bundle-integration
```

---

## Success Criteria

- [x] Fork exists at robotdad/amplifier-module-tool-skills
- [ ] behaviors/skills.yaml follows foundation pattern
- [ ] bundle.md is thin bundle including foundation
- [ ] README is bundle-first (no profile emphasis)
- [ ] Example converted to bundle format
- [ ] All docs use microsoft URLs
- [ ] Local testing successful with robotdad URLs
- [ ] Ready for PR submission

---

## Notes

- Profiles are being deprecated/removed - don't preserve backward compatibility
- Follow foundation's behavior pattern exactly (consistency matters)
- Keep implementation simple (philosophy: ruthless simplicity)
- Documentation should be clear for bundle authors
