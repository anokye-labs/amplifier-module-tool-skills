# Manual Testing Steps for Skills Module

Follow these steps to test bundle integration, skills visibility, and Anthropic spec compliance.

---

## Quick Test (Simplest)

### Testing (4 commands)

```bash
cd /Users/robotdad/Source/Work/skills/amplifier-module-tool-skills

# Copy test fixtures to default location
mkdir -p .amplifier && cp -r tests/fixtures/skills .amplifier/

# Create test bundle pointing to LOCAL module
cat > ai_working/test-local.md << 'EOF'
---
bundle:
  name: test-local-skills
  version: 1.0.0
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
tools:
  - module: tool-skills
    source: file:///Users/robotdad/Source/Work/skills/amplifier-module-tool-skills
---
# Test Local Skills
---
@foundation:context/shared/common-system-base.md
EOF

# Test visibility
amplifier run --bundle ai_working/test-local.md "What skills do you see available? Don't use any tools, just tell me what you see in your context."
```

**Expected**: Agent should see and list the 3 skills WITHOUT calling load_skill tool:
- amplifier-philosophy
- module-development  
- python-standards

### Cleanup (3 commands)

```bash
# Clean persisted registry
cat ~/.amplifier/registry.json | jq 'del(.bundles["test-local-skills"])' > ~/.amplifier/registry.json.tmp && mv ~/.amplifier/registry.json.tmp ~/.amplifier/registry.json

# Remove test files
rm -rf .amplifier
rm -f ai_working/test-local.md

# Verify
amplifier bundle list | grep skills
```

**Expected**: No output

---

## Why Local Source is Needed

**The Issue**: 
- The main `bundle.md` references: `source: git+https://github.com/microsoft/amplifier-module-tool-skills@main`
- That GitHub version doesn't have hooks.py yet (not merged)
- So using `--bundle skills` loads the old version without visibility

**The Fix**:
- Use `source: file:///Users/robotdad/Source/Work/skills/amplifier-module-tool-skills`
- This loads the LOCAL development version with hooks.py
- Visibility hook runs and injects skills

---

## Comprehensive Testing

### Part 1: Setup

#### 1. Navigate to directory

```bash
cd /Users/robotdad/Source/Work/skills/amplifier-module-tool-skills
```

#### 2. Copy test fixtures

```bash
mkdir -p .amplifier && cp -r tests/fixtures/skills .amplifier/
```

**Verify skills copied**:
```bash
ls .amplifier/skills/
```

**Expected**: amplifier-philosophy, module-development, python-standards

---

### Part 2: Test Skills Visibility (Core Feature)

#### 3. Create test bundle with local module source

```bash
cat > ai_working/test-local.md << 'EOF'
---
bundle:
  name: test-local-skills
  version: 1.0.0
  description: Test bundle using local development version
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
tools:
  - module: tool-skills
    source: file:///Users/robotdad/Source/Work/skills/amplifier-module-tool-skills
    config:
      # Uses default: .amplifier/skills
      visibility:
        enabled: true  # Test visibility feature
---
# Test Local Skills Bundle
---
@foundation:context/shared/common-system-base.md
EOF
```

#### 4. Test automatic skills visibility

```bash
amplifier run --bundle ai_working/test-local.md "What skills do you see available? Don't use any tools, just tell me what you see in your context."
```

**Expected**: Agent lists skills WITHOUT using load_skill tool. Example output:
```
I can see these skills available in my context:
- amplifier-philosophy: Amplifier design philosophy...
- module-development: Guide for creating new Amplifier modules...
- python-standards: Python coding standards...
```

**This proves the visibility hook is working.**

#### 5. Test load_skill tool still works

```bash
amplifier run --bundle ai_working/test-local.md "Use the load_skill tool to list available skills"
```

**Expected**: Tool executes and returns same 3 skills with descriptions.

#### 6. Test loading full skill content

```bash
amplifier run --bundle ai_working/test-local.md "Load the amplifier-philosophy skill and summarize its key points"
```

**Expected**: Agent calls load_skill(skill_name="amplifier-philosophy") and reads full content.

---

### Part 3: Test Spec Compliance Features

#### 7. Test compatibility field

```bash
mkdir -p .amplifier/skills/test-compat
cat > .amplifier/skills/test-compat/SKILL.md << 'EOF'
---
name: test-compat
description: Test compatibility field support
compatibility: Requires git and docker
---
# Test Skill
EOF

amplifier run --bundle ai_working/test-local.md "Use load_skill with info='test-compat' to show metadata"
```

**Expected**: Output includes `"compatibility": "Requires git and docker"`

#### 8. Test allowed-tools parsing

```bash
mkdir -p .amplifier/skills/test-tools
cat > .amplifier/skills/test-tools/SKILL.md << 'EOF'
---
name: test-tools
description: Test allowed-tools parsing
allowed-tools: bash read_file write_file
---
# Test Skill
EOF

amplifier run --bundle ai_working/test-local.md "Use load_skill with info='test-tools' to show metadata"
```

**Expected**: Output includes `"allowed_tools": ["bash", "read_file", "write_file"]` (parsed as list)

---

### Part 4: Test Configuration Options

#### 9. Test with visibility disabled

```bash
cat > ai_working/test-no-visibility.md << 'EOF'
---
bundle:
  name: test-no-visibility
  version: 1.0.0
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
tools:
  - module: tool-skills
    source: file:///Users/robotdad/Source/Work/skills/amplifier-module-tool-skills
    config:
      visibility:
        enabled: false  # Disable automatic visibility
---
# Test Without Visibility
---
@foundation:context/shared/common-system-base.md
EOF

amplifier run --bundle ai_working/test-no-visibility.md "What skills do you see? Don't use tools."
```

**Expected**: Agent reports NO skills visible (manual discovery only).

#### 10. Test with max_visible limit

```bash
cat > ai_working/test-limit.md << 'EOF'
---
bundle:
  name: test-limit
  version: 1.0.0
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
tools:
  - module: tool-skills
    source: file:///Users/robotdad/Source/Work/skills/amplifier-module-tool-skills
    config:
      visibility:
        max_skills_visible: 2  # Only show 2 skills
---
# Test Visibility Limit
---
@foundation:context/shared/common-system-base.md
EOF

amplifier run --bundle ai_working/test-limit.md "What skills do you see?"
```

**Expected**: Agent sees only 2 skills + message about "(1 more available)"

---

## Part 5: Cleanup

### 11. Clean persisted registry

```bash
cat ~/.amplifier/registry.json | jq 'del(.bundles["test-local-skills"], .bundles["test-no-visibility"], .bundles["test-limit"])' > ~/.amplifier/registry.json.tmp && mv ~/.amplifier/registry.json.tmp ~/.amplifier/registry.json
```

### 12. Remove test files

```bash
rm -rf .amplifier
rm -f ai_working/test-local.md
rm -f ai_working/test-no-visibility.md
rm -f ai_working/test-limit.md
```

### 13. Verify cleanup

```bash
amplifier bundle list | grep -E "skills|test"
```

**Expected**: No output

---

## Key Insight: Local Source Required for Testing

**Critical**: For testing the development version with hooks.py, you MUST use:

```yaml
tools:
  - module: tool-skills
    source: file:///Users/robotdad/Source/Work/skills/amplifier-module-tool-skills
```

**NOT**:
```yaml
tools:
  - module: tool-skills
    source: git+https://github.com/microsoft/amplifier-module-tool-skills@main
```

The git source will load the released version (without hooks.py until merged).

---

## What Gets Tested

### Bundle Integration ✅
- behaviors/skills.yaml composability
- bundle.md thin bundle pattern  
- README bundle-first approach

### Skills Visibility ✅
- Skills automatically visible in context
- No manual discovery needed
- Hook injection working
- Progressive disclosure (metadata → content → references)

### Spec Compliance ✅
- compatibility field support
- allowed-tools parsing (string → list)
- Full Anthropic spec compliance

### Configuration ✅
- Visibility can be enabled/disabled
- max_visible limit works
- Behavior inclusion pattern works
