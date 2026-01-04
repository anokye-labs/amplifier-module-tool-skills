# Manual Testing Steps for Skills Module

**Important**: These steps test the LOCAL development version with hooks.py. The GitHub version doesn't have these changes yet.

---

## Quick Test

### Prerequisites
- Must run from: `amplifier-module-tool-skills/` directory
- Uses `$PWD` in test bundle, so location matters

### Testing (4 commands)

```bash
cd amplifier-module-tool-skills

# 1. Copy test fixtures to default location
mkdir -p .amplifier && cp -r tests/fixtures/skills .amplifier/

# 2. Register test bundle (loads local development version)
amplifier bundle add file://$PWD/ai_working/test-local-bundle.md

# 3. Test visibility
amplifier run --bundle test-local-skills "What skills do you see available? Don't use any tools."
```

**Expected**: Agent lists 3 skills without calling load_skill tool:
- amplifier-philosophy
- module-development  
- python-standards

**This proves the visibility hook is working.**

---

## Cleanup (3 commands)

```bash
# 1. Remove bundle
amplifier bundle remove test-local-skills

# 2. Clean persisted registry
cat ~/.amplifier/registry.json | jq 'del(.bundles["test-local-skills"])' > ~/.amplifier/registry.json.tmp && mv ~/.amplifier/registry.json.tmp ~/.amplifier/registry.json

# 3. Remove test files
rm -rf .amplifier
```

**Verify**:
```bash
amplifier bundle list | grep skills
```
**Expected**: No output

---

## Why Local Source is Required

**The Issue**: 
- Main bundle.md references: `git+https://github.com/microsoft/amplifier-module-tool-skills@main`
- GitHub doesn't have hooks.py yet (not merged)
- Testing requires local version

**The Solution**:
- File `ai_working/test-local-bundle.md` uses: `source: file://$PWD`
- Loads LOCAL development version with hooks.py
- Visibility hook runs and injects skills

---

## Additional Tests (Optional)

After registering the bundle:

### Test load_skill tool
```bash
amplifier run --bundle test-local-skills "Use load_skill to list skills"
```

### Test loading full content
```bash
amplifier run --bundle test-local-skills "Load the amplifier-philosophy skill"
```

### Test spec compliance
The new `compatibility` and `allowed-tools` fields are tested by the test suite:
```bash
uv run pytest tests/test_hooks.py -v
```

---

## Test Files Included

**Pre-created**: `ai_working/test-local-bundle.md`
- Uses `source: file://$PWD` for local loading
- Bundle name: `test-local-skills`  
- Just register with `bundle add` and use by name

**Test fixtures**: `tests/fixtures/skills/`
- Already in repo, just copy to `.amplifier/`
