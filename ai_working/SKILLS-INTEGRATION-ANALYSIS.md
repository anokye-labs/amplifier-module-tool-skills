# Skills Integration Analysis - Anthropic Spec Compliance

**Date**: 2026-01-02
**Purpose**: Analyze tool-skills against official Anthropic Skills specification and design integration improvements

---

## Executive Summary

**Current State**: tool-skills implements the core Anthropic Skills specification correctly, with strong progressive disclosure and tool-based approach.

**Gaps Identified**:
1. Missing `compatibility` field (optional but useful)
2. `allowed-tools` parsing incomplete (not split from string)
3. No automatic skills visibility (Anthropic recommends system prompt injection)

**Architectural Decisions**:
- ✅ **NO** Skill protocol needed in amplifier-core (skills are data, not services)
- ✅ **NO** skills mount point needed (skills remain internal to tool-skills module)
- ✅ **YES** integrated visibility hook in tool-skills (tight coupling appropriate)

**Total Work**: ~312 lines of code, all within tool-skills module, no kernel changes

---

## Official Anthropic Skills Specification

### Source
- **Specification**: https://agentskills.io/specification
- **Integration Guide**: https://agentskills.io/integrate-skills

### Skill Format

**Required Directory Structure**:
```
skill-name/
├── SKILL.md          # Required: frontmatter + markdown body
├── scripts/          # Optional: executable code
├── references/       # Optional: additional docs
└── assets/           # Optional: templates, images, data
```

**Required YAML Frontmatter**:
```yaml
---
name: skill-name              # 1-64 chars, lowercase alphanumeric + hyphens
description: What it does...  # 1-1024 chars, when to use it
---
```

**Optional Fields**:
- `version`: Version string
- `license`: License name or reference
- `compatibility`: Environment requirements (max 500 chars)
- `allowed-tools`: Pre-approved tools (space-delimited or list)
- `metadata`: Arbitrary key-value mapping

### Progressive Disclosure

**Three Levels**:
1. **Metadata** (name + description): ~100 tokens - loaded at startup
2. **Instructions** (SKILL.md body): <5000 tokens recommended - loaded on activation
3. **Resources** (scripts/, references/, assets/): 0 tokens until accessed

### Integration Recommendations

**Anthropic's Guidance**:
- **Inject skill metadata into system prompt** so agents know what's available
- Use XML format for clarity:
  ```xml
  <available_skills>
  <skill>
  <name>pdf-processing</name>
  <description>Extracts text and tables from PDF files...</description>
  <location>/path/to/skills/pdf-processing/SKILL.md</location>
  </skill>
  </available_skills>
  ```
- Parse only frontmatter at startup (low context usage)
- Load full content only when skill is activated
- Tool-based or filesystem-based approach both valid

---

## Current tool-skills Implementation Analysis

### What's Implemented Correctly ✅

1. **Core Specification Compliance**
   - ✅ SKILL.md with YAML frontmatter + markdown body
   - ✅ Required fields: name (validated), description
   - ✅ Name format validation: lowercase alphanumeric + hyphens
   - ✅ Directory name matching (warns if mismatch)
   - ✅ Optional fields: version, license, metadata

2. **Progressive Disclosure**
   - ✅ Level 1: `load_skill(list=true)` - name + description only
   - ✅ Level 2: `load_skill(skill_name="...")` - full content
   - ✅ Level 3: Returns `skill_directory` for companion file access
   - ✅ Search operation: `load_skill(search="term")`
   - ✅ Info operation: `load_skill(info="name")` - metadata without content

3. **Tool-Based Integration**
   - ✅ Clean Tool protocol implementation
   - ✅ Multiple operations in single tool
   - ✅ Proper ToolResult responses

4. **Amplifier-Specific Enhancements**
   - ✅ Multi-source discovery (workspace, user, custom)
   - ✅ Priority-based first-match-wins
   - ✅ Event emission: `skills:discovered`, `skill:loaded`

### Gaps vs. Specification

#### 🔴 HIGH PRIORITY: Missing `compatibility` Field

**Spec Definition**: Optional field for environment requirements (max 500 chars)

**Example**:
```yaml
---
name: my-skill
description: Does something
compatibility: Requires git, docker, jq, and access to the internet
---
```

**Current State**:
- ❌ Not in SkillMetadata dataclass (discovery.py:21-32)
- ❌ Not parsed from frontmatter (discovery.py:152-165)
- ❌ Not exposed in info mode (__init__.py:264-276)

**Impact**: Skills can't declare environment requirements, making it harder for agents to assess if a skill is usable.

**Fix Required**: Add `compatibility: dict[str, Any] | None = None` to SkillMetadata, parse and expose.

#### 🟡 MEDIUM: `allowed-tools` Parsing Incomplete

**Spec Definition**: "Space-delimited list of pre-approved tools"

**Example**:
```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
# OR
allowed-tools:
  - Bash(git:*)
  - Read
```

**Current State**:
- ⚠️ Stored as-is from frontmatter (discovery.py:153)
- No parsing: if string, should be split on spaces
- Could be string or list depending on YAML format

**Impact**: Consumers must parse it themselves; not normalized.

**Fix Required**: Parse string → list, normalize format.

#### 🟡 MEDIUM: No System Prompt Injection

**Spec Recommendation**: Inject metadata into system prompt at startup

**Current State**:
- ❌ Tool-based only (requires explicit `load_skill(list=true)`)
- No automatic injection into agent context
- Agent must actively discover skills

**Impact**: Agents may not know skills exist; more discovery overhead.

**Fix Required**: Add visibility hook (already planned).

#### 🔵 LOW: Optional Directories Not Documented

**Spec Defines**: `scripts/`, `references/`, `assets/` subdirectories

**Current State**:
- ✅ Tool returns `skill_directory` path for access
- ⚠️ Not documented or validated
- Agents can use `read_file(skill_directory + "/scripts/...")` but may not know the convention

**Impact**: Minor - skill authors and agents may not know about standard structure.

**Fix Required**: Document in README.md.

---

## Architectural Decisions

### Decision 1: NO Skill Protocol ✅

**Question**: Should amplifier-core define a `Skill` protocol?

**Answer**: **NO**

**Rationale**:
1. **Skills are data structures, not services**
   - All existing protocols (Tool, Provider, Orchestrator) define executable services with lifecycle methods
   - Skills are metadata + content - passive data
   - No execute() method, no service contract
   
2. **Skills are managed content**
   - Like messages (managed by ContextManager) - no Message protocol
   - Like agent definitions - no Agent protocol
   - The manager has the protocol (Tool), not the data

3. **Implementation detail of tool-skills**
   - Accessed via Tool protocol: `tool.execute({"list": True})`
   - Or programmatically: `coordinator.get("tools")["load_skill"].skills`
   - No need for external contract

**Philosophy Compliance**: ✅ Avoids unnecessary abstraction

### Decision 2: NO Skills Mount Point ✅

**Question**: Should coordinator.mount_points include "skills": {}?

**Answer**: **NO**

**Rationale**:
1. **Mount points are for services**
   - All mount points hold protocol-implementing services
   - Skills don't implement a protocol
   
2. **Wrong granularity**
   - Would require mounting each skill individually
   - Skills discovered at runtime - dynamic set
   - Would duplicate tool.skills dict - violates DRY

3. **Current access works**
   - Via tool instance: `coordinator.get("tools")["load_skill"].skills`
   - Clean encapsulation within the tool module
   - Skills are implementation detail of the tool

**Philosophy Compliance**: ✅ Maintains clean boundaries

### Decision 3: Integrated Visibility Hook ✅

**Question**: How to make skills visible to agents?

**Answer**: **Integrated hook within tool-skills module**

**Rationale**:
1. **Tight coupling is appropriate**
   - Skills visibility inherent to skills capability
   - Hook needs direct access to tool.skills data
   - Single feature: include skills → get visibility automatically

2. **Precedent in foundation**
   - `hooks-todo-display` embedded in foundation modules/
   - Not every hook needs separate repo
   - When coupling is tight, integrate

3. **Follows Anthropic recommendation**
   - Inject metadata into context (via system message or user message)
   - Before each request ensures current state
   - Progressive disclosure: metadata visible, content loaded on demand

4. **Minimal complexity**
   - ~80 lines of hook code
   - Shares tool.skills data (no duplication)
   - Single mount() function handles both tool and hook

**Philosophy Compliance**: ✅ Ruthlessly simple, appropriate coupling

---

## Complete Implementation Specification

### Changes Required

| File | Type | LOC | Description |
|------|------|-----|-------------|
| `discovery.py` | MODIFY | +15 | Add compatibility, fix allowed-tools parsing |
| `__init__.py` | MODIFY | +20 | Mount hook, expose new fields in info |
| `hooks.py` | CREATE | ~80 | SkillsVisibilityHook implementation |
| `behaviors/skills.yaml` | MODIFY | +12 | Add visibility config |
| `bundle.md` | MODIFY | +55 | Document visibility |
| `tests/test_hooks.py` | CREATE | ~130 | Hook test suite |
| **TOTAL** | | **~312** | **All in tool-skills module** |

**No changes to**: amplifier-core, amplifier-foundation, or any other repos ✅

### File-by-File Specifications

#### 1. `amplifier_module_tool_skills/discovery.py`

**Change A: Update SkillMetadata dataclass (line 21-32)**

```python
@dataclass
class SkillMetadata:
    """Metadata from a SKILL.md file's YAML frontmatter.
    
    Follows Anthropic Skills Specification:
    https://agentskills.io/specification
    
    Required fields: name, description
    Optional fields: version, license, compatibility, allowed-tools, metadata
    """
    name: str
    description: str
    path: Path
    source: str
    version: str | None = None
    license: str | None = None
    compatibility: dict[str, Any] | None = None  # ← ADD: Environment requirements
    allowed_tools: list[str] | None = None
    metadata: dict[str, Any] | None = None
```

**Change B: Fix allowed-tools parsing (line 152-165)**

```python
# Parse optional fields
# allowed-tools: Can be list or comma-separated string
allowed_tools_raw = frontmatter.get("allowed-tools")
allowed_tools = None
if allowed_tools_raw:
    if isinstance(allowed_tools_raw, list):
        allowed_tools = [str(tool) for tool in allowed_tools_raw]
    elif isinstance(allowed_tools_raw, str):
        # Support space-delimited string format per spec
        allowed_tools = [tool.strip() for tool in allowed_tools_raw.split()]
    else:
        logger.warning(
            f"Invalid allowed-tools format in {skill_file}: {type(allowed_tools_raw)}"
        )

# Parse compatibility field
compatibility = frontmatter.get("compatibility")
```

**Change C: Update SkillMetadata creation (line 156-165)**

```python
metadata = SkillMetadata(
    name=name,
    description=description,
    path=skill_file,
    source=str(skills_dir),
    version=frontmatter.get("version"),
    license=frontmatter.get("license"),
    compatibility=compatibility,  # ← ADD
    allowed_tools=allowed_tools,  # ← Now properly parsed
    metadata=frontmatter.get("metadata"),
)
```

#### 2. `amplifier_module_tool_skills/__init__.py`

**Change A: Add import (line 11)**

```python
from amplifier_module_tool_skills.hooks import SkillsVisibilityHook
```

**Change B: Mount visibility hook (after line 46)**

```python
# Mount skills visibility hook if enabled
visibility_config = config.get("visibility", {})
if visibility_config.get("enabled", True):  # Default: enabled
    hook = SkillsVisibilityHook(tool.skills, visibility_config)
    
    # Register hook on provider:request event
    coordinator.hooks.register(
        event="provider:request",
        handler=hook.on_provider_request,
        priority=hook.priority,
        name="skills-visibility",
    )
    
    logger.info(f"Mounted skills visibility hook with {len(tool.skills)} skills")
```

**Change C: Expose new fields in _get_skill_info (line 264-276)**

```python
def _get_skill_info(self, skill_name: str) -> ToolResult:
    """Get metadata for a skill without loading full content."""
    if skill_name not in self.skills:
        available = ", ".join(sorted(self.skills.keys()))
        return ToolResult(
            success=False,
            error={"message": f"Skill '{skill_name}' not found. Available: {available}"},
        )

    metadata = self.skills[skill_name]
    info = {
        "name": metadata.name,
        "description": metadata.description,
        "version": metadata.version,
        "license": metadata.license,
        "compatibility": metadata.compatibility,  # ← ADD
        "allowed_tools": metadata.allowed_tools,  # ← ADD
        "path": str(metadata.path),
    }

    if metadata.metadata:
        info["metadata"] = metadata.metadata

    return ToolResult(success=True, output=info)
```

#### 3. `amplifier_module_tool_skills/hooks.py` (CREATE)

**Complete new file** - see zen-architect's specification for full implementation (~80 lines)

Key components:
- `SkillsVisibilityHook` class
- `on_provider_request()` handler
- `_format_skills_list()` formatter
- Configuration support (enabled, inject_role, max_visible, ephemeral, priority)

#### 4. `behaviors/skills.yaml`

**Add visibility configuration**:

```yaml
bundle:
  name: skills-behavior
  version: 1.0.0
  description: Anthropic Skills support with progressive disclosure and automatic visibility

tools:
  - module: tool-skills
    source: git+https://github.com/microsoft/amplifier-module-tool-skills@main
    config:
      # Skills directories (optional - uses defaults if not specified)
      # skills_dirs:
      #   - ~/.amplifier/skills
      #   - .amplifier/skills
      
      # Skills visibility (automatic context injection)
      visibility:
        enabled: true              # Show available skills to agent
        inject_role: "user"        # Inject as user message
        max_skills_visible: 50     # Limit for large skill sets
        ephemeral: true            # Don't persist in history
        priority: 20               # Hook priority
```

#### 5. `bundle.md`

**Add documentation section** after "Available Tool" (around line 35):

```markdown
## Skills Visibility

When this bundle is included, agents **automatically see** a list of available skills in their context before each request. This follows Anthropic's Skills specification recommendation for progressive disclosure.

### How It Works

**Progressive Disclosure:**
- **Level 1 (Always visible)**: Skill metadata (name + description) - ~30-50 tokens per skill
- **Level 2 (On demand)**: Full skill content - loaded via `load_skill(skill_name="...")`
- **Level 3 (References)**: Companion files - accessed via `read_file(skill_directory + "/file")`

**What agents see:**

```
<available_skills>
Available skills (use load_skill tool):
- **python-testing**: Best practices for Python testing with pytest
- **git-workflow**: Git branching and commit message standards
- **api-design**: RESTful API design patterns and conventions
</available_skills>
```

Skills are injected before each LLM request using an integrated hook, ensuring agents always have current skill awareness without manual discovery.

### Configuration

**Default behavior** (visibility enabled):
```yaml
tools:
  - module: tool-skills
    # Uses default visibility settings
```

**Disable visibility** (manual discovery only):
```yaml
tools:
  - module: tool-skills
    config:
      visibility:
        enabled: false
```

**Limit visible skills** (for large collections):
```yaml
tools:
  - module: tool-skills
    config:
      visibility:
        max_skills_visible: 20
```

### Token Cost

- ~30-50 tokens per skill (metadata only)
- Typical: 10 skills = ~500 tokens per request
- Large collections: Use `max_skills_visible` to limit
- Trade-off: Saves 1-2 discovery tool calls (~200-500 tokens)
```

#### 6. `tests/test_hooks.py` (CREATE)

**Complete test suite** - see zen-architect's specification (~130 lines)

Test coverage:
- Skills list injection
- Enabled/disabled flag
- Empty skills handling
- max_visible limit
- XML boundaries
- Configuration options (role, ephemeral)

---

## Why No Protocol or Mount Point

### Comparison with Existing Patterns

| Concept | Has Protocol? | Has Mount Point? | Why? |
|---------|---------------|------------------|------|
| **Tools** | ✅ Yes (Tool) | ✅ Yes (tools) | Executable services invoked by orchestrator |
| **Providers** | ✅ Yes (Provider) | ✅ Yes (providers) | Executable services invoked by orchestrator |
| **Messages** | ❌ No | ❌ No | Data managed by ContextManager |
| **Agent Definitions** | ❌ No | ✅ Yes (agents) | Configuration data for spawning |
| **Skills** | ❌ No | ❌ No | Data managed by Tool (load_skill) |

**The Pattern**:
- **Protocols** = Services with lifecycle/invocation (Tool, Provider, Orchestrator)
- **Mount Points** = Where protocol-implementing services register
- **Data Structures** = Managed by services, not directly mounted

**Skills are data**, like messages. They're managed by a service (SkillsTool), which implements the Tool protocol.

### Access Patterns

**Current (Perfect for data)**:
```python
# Via tool protocol
result = await coordinator.get("tools")["load_skill"].execute({"list": True})

# Programmatic access (for hooks)
skills_dict = coordinator.get("tools")["load_skill"].skills
```

**If we had mount point (Wrong)**:
```python
# Would require mounting each skill
await coordinator.mount("skills", skill, name="python-testing")
await coordinator.mount("skills", skill, name="git-workflow")
# ... mount 50 skills individually?

# Then access
skill = coordinator.get("skills", "python-testing")
# But skills don't DO anything - this is the wrong abstraction
```

The mount point pattern is for **services that do things**. Skills are **content that gets loaded**. Big difference.

---

## Implementation Phases

### Phase 1: Anthropic Spec Compliance (Essential)

**Priority**: HIGH - Brings tool-skills into full spec compliance

**Changes**:
1. Add `compatibility` field to SkillMetadata
2. Fix `allowed-tools` parsing (string → list)
3. Expose both in info mode
4. Add tests for new fields
5. Update README documenting compatibility and allowed-tools

**Effort**: ~2-3 hours
**Value**: Full spec compliance, better skill metadata

### Phase 2: Skills Visibility (Recommended)

**Priority**: HIGH - Follows Anthropic's integration guidance

**Changes**:
1. Create hooks.py with SkillsVisibilityHook
2. Update __init__.py to mount hook
3. Update behaviors/skills.yaml with config
4. Update bundle.md with documentation
5. Create comprehensive test suite
6. Test end-to-end with real skills

**Effort**: ~4-5 hours
**Value**: Automatic skill discovery, better UX

### Phase 3: Documentation Enhancements (Optional)

**Priority**: MEDIUM - Improves clarity

**Changes**:
1. Document scripts/, references/, assets/ directories in README
2. Add validation utility for skill authors
3. Document security considerations

**Effort**: ~1-2 hours
**Value**: Better guidance for skill authors

---

## Testing Strategy

### Spec Compliance Tests

```python
# test_discovery.py additions

def test_compatibility_field_parsing():
    """Test compatibility field is parsed from frontmatter."""
    # Create skill with compatibility
    skill_md = """---
name: test-skill
description: Test
compatibility: Requires git and docker
---
# Test
"""
    # Verify parsed correctly
    
def test_allowed_tools_string_format():
    """Test allowed-tools parses space-delimited string."""
    skill_md = """---
name: test-skill
description: Test
allowed-tools: Bash(git:*) Bash(jq:*) Read
---
# Test
"""
    # Verify: ["Bash(git:*)", "Bash(jq:*)", "Read"]
    
def test_allowed_tools_list_format():
    """Test allowed-tools as YAML list."""
    skill_md = """---
name: test-skill
description: Test
allowed-tools:
  - Bash(git:*)
  - Read
---
# Test
"""
    # Verify: ["Bash(git:*)", "Read"]
```

### Visibility Hook Tests

See `tests/test_hooks.py` specification in zen-architect's output.

### End-to-End Integration Tests

```python
# test_integration.py additions

@pytest.mark.asyncio
async def test_skills_visible_in_context():
    """Test skills appear in agent context automatically."""
    # Create session with skills bundle
    # Verify skills list injected before LLM call
    # Check provider:request event contains skills in context
    
@pytest.mark.asyncio
async def test_visibility_respects_config():
    """Test visibility can be disabled."""
    # Create session with visibility.enabled=false
    # Verify no skills injection
```

---

## Success Criteria

### Spec Compliance ✅

- [ ] `compatibility` field added to SkillMetadata
- [ ] `compatibility` parsed from frontmatter
- [ ] `compatibility` exposed in info mode
- [ ] `allowed-tools` parsed as list (handles string and list YAML formats)
- [ ] `allowed_tools` exposed in info mode
- [ ] All spec fields documented

### Visibility ✅

- [ ] SkillsVisibilityHook class created
- [ ] Hook registered on provider:request
- [ ] Skills list injected before each LLM call
- [ ] Format follows Anthropic guidance
- [ ] Default enabled, configurable
- [ ] Documented in bundle.md

### Architecture ✅

- [ ] No changes to amplifier-core
- [ ] No new protocols defined
- [ ] No new mount points created
- [ ] Hook integrated in tool-skills module
- [ ] Philosophy compliant (ruthless simplicity)

### Testing ✅

- [ ] All existing tests pass
- [ ] New fields tested (compatibility, allowed-tools)
- [ ] Hook test suite comprehensive
- [ ] End-to-end visibility verified

---

## Next Steps

**Decision Point**: Should we:
1. Implement Phase 1 (spec compliance) only?
2. Implement both Phase 1 and Phase 2 (spec + visibility)?
3. Something else?

**Recommendation**: Implement both phases together in a single PR. They're related work, and visibility is the key value proposition for integrating skills properly.

**Estimated Total Effort**: ~6-8 hours
**Value**: Full Anthropic spec compliance + automatic skill discovery

---

## Philosophy Verification

### Ruthless Simplicity ✅
- No unnecessary abstractions (no protocol, no mount point)
- Minimal code (~312 lines total)
- Direct solution to real problem
- Reuses existing patterns (hooks, HookResult)

### Modular Design ✅
- Self-contained in tool-skills module
- Clear contract (Tool protocol)
- Regenerable independently
- No cross-module dependencies

### Mechanism Not Policy ✅
- Kernel unchanged (mechanisms stay stable)
- Policy in module (visibility strategy, format choices)
- Configuration controls behavior
- Swappable: disable visibility via config

**Assessment**: This design fully aligns with Amplifier's implementation philosophy and kernel architecture.
