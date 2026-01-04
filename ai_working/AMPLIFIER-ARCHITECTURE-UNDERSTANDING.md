# Amplifier Architecture Understanding

**Date**: 2026-01-02
**Purpose**: Document our understanding of Amplifier's contract-based architecture and tool system

---

## The Foundational Architecture

### Core Principle: Contract-Based Modularity

Amplifier achieves **zero cross-dependencies between modules** through Protocol-based contracts defined in the kernel (amplifier-core).

**Dependency Graph**:
```
amplifier-core (kernel - defines contracts)
    ↑
    │ depends on (ONLY the kernel)
    │
    ├─ tool-bash           (implements Tool protocol)
    ├─ tool-filesystem     (implements Tool protocol)
    ├─ tool-web            (implements Tool protocol)
    ├─ loop-basic          (implements Orchestrator protocol)
    ├─ loop-streaming      (implements Orchestrator protocol)
    ├─ context-simple      (implements ContextManager protocol)
    ├─ provider-anthropic  (implements Provider protocol)
    └─ [any other module]

NO dependencies between modules - only to kernel contracts!
```

---

## The Five Core Protocols

**Defined in**: `amplifier-core/amplifier_core/interfaces.py`

### 1. Tool Protocol (lines 129-153)
```python
@runtime_checkable
class Tool(Protocol):
    @property
    def name(self) -> str: ...
    
    @property
    def description(self) -> str: ...
    
    @property
    def input_schema(self) -> dict[str, Any]: ...  # JSON Schema
    
    async def execute(self, input: dict[str, Any]) -> ToolResult: ...
```

### 2. Orchestrator Protocol (lines 34-58)
```python
@runtime_checkable
class Orchestrator(Protocol):
    async def execute(
        self,
        prompt: str,
        context: ContextManager,
        providers: dict[str, Provider],
        tools: dict[str, Tool],
        hooks: HookRegistry,
    ) -> str: ...
```

### 3. ContextManager Protocol (lines 156-202)
```python
@runtime_checkable
class ContextManager(Protocol):
    async def add_message(self, message: dict[str, Any]) -> None: ...
    async def get_messages_for_request(
        self, token_budget: int | None = None, provider: Any | None = None
    ) -> list[dict[str, Any]]: ...
    async def get_messages(self) -> list[dict[str, Any]]: ...
    async def set_messages(self, messages: list[dict[str, Any]]) -> None: ...
    async def clear(self) -> None: ...
```

### 4. Provider Protocol (lines 62-126)
```python
@runtime_checkable
class Provider(Protocol):
    @property
    def name(self) -> str: ...
    
    def get_info(self) -> ProviderInfo: ...
    async def list_models(self) -> list[ModelInfo]: ...
    async def complete(self, request: ChatRequest, **kwargs) -> ChatResponse: ...
    def parse_tool_calls(self, response: ChatResponse) -> list[ToolCall]: ...
```

### 5. HookHandler Protocol (lines 206-220)
```python
@runtime_checkable
class HookHandler(Protocol):
    async def __call__(self, event: str, data: dict[str, Any]) -> HookResult: ...
```

**Key Point**: These are Python Protocols (PEP 544) - structural typing. Modules don't inherit, they just implement the methods.

---

## Module Entry Point Pattern

**Every module must provide**:

```python
# Module-level constant (optional but recommended)
__amplifier_module_type__ = "tool"  # or "orchestrator", "provider", "context", "hook"

# Entry point function (REQUIRED)
async def mount(coordinator: ModuleCoordinator, config: dict[str, Any]) -> Callable | None:
    """Initialize and register module.
    
    Args:
        coordinator: Infrastructure context from kernel
        config: Module-specific configuration from bundle YAML
    
    Returns:
        Optional cleanup callable for resource cleanup
    """
    # 1. Create module instance
    module = MyTool(config)
    
    # 2. Register with coordinator
    await coordinator.mount("tools", module, name=module.name)
    
    # 3. Return optional cleanup function
    async def cleanup():
        await module.close()
    
    return cleanup
```

**Registered in pyproject.toml**:
```toml
[project.entry-points."amplifier.modules"]
tool-mymodule = "my_package:mount"
```

---

## The ModuleCoordinator

**Defined in**: `amplifier-core/coordinator.py:39-500`

**What it is**: Infrastructure context object that modules receive during mount

**Provides to modules**:

1. **Mount Points** (the registries):
   ```python
   mount_points = {
       "orchestrator": None,      # Single orchestrator
       "providers": {},           # dict[name, Provider]
       "tools": {},               # dict[name, Tool]
       "context": None,           # Single context manager
       "hooks": HookRegistry(),   # Built-in hook system
       "module-source-resolver": None,
   }
   ```

2. **Infrastructure Properties**:
   - `coordinator.session_id` - Current session identifier
   - `coordinator.parent_id` - Parent session (for spawned agents)
   - `coordinator.config` - The complete mount plan/configuration
   - `coordinator.loader` - ModuleLoader for dynamic loading
   - `coordinator.session` - Reference to AmplifierSession

3. **Key Methods**:
   - `coordinator.mount(slot, module, name)` - Register module
   - `coordinator.get(slot, name=None)` - Retrieve module(s)
   - `coordinator.hooks.register(event, handler, priority, name)` - Register hook
   - `coordinator.hooks.emit(event, data)` - Emit event
   - `coordinator.process_hook_result(result, event, hook_name)` - Route hook actions

**Where created**: By `AmplifierSession.__init__()` in `session.py:66`:
```python
self.coordinator = ModuleCoordinator(session=self)
```

**Why it exists**: Provides "minimal context plumbing" - the infrastructure that makes module boundaries work without tight coupling.

---

## How Tools Are Built and Used

### The Complete Flow

#### 1. Bundle Declares Tools (YAML)
```yaml
# foundation/bundle.md
tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
```

#### 2. Session Loads Modules
**Code**: `session.py:173-188`
```python
for tool_config in self.config.get("tools", []):
    module_id = tool_config.get("module")
    # Loader resolves source, imports module, gets mount() function
    tool_mount = await self.loader.load(module_id, config, source)
    # Call mount function with coordinator
    cleanup = await tool_mount(self.coordinator)
```

#### 3. Module Registers Itself
**Code**: `tool-skills/__init__.py:46`
```python
async def mount(coordinator: ModuleCoordinator, config: dict):
    tool = SkillsTool(config, coordinator)
    await coordinator.mount("tools", tool, name=tool.name)  # ← Adds to dict
    return  # Optional cleanup callable
```

**Result**: Tool instance stored in `coordinator.mount_points["tools"]["load_skill"]`

#### 4. Session Passes Tools Dict to Orchestrator
**Code**: `session.py:254-260`
```python
tools = self.coordinator.get("tools")  # Returns dict[str, Tool]

await orchestrator.execute(
    prompt=prompt,
    context=context,
    providers=providers,
    tools=tools,  # ← Dict of all tool instances
    hooks=hooks,
)
```

---

## The Tool Invocation Cycle

### Round 1: Initial Request

**Orchestrator converts tools → ToolSpec** (loop-basic/__init__.py:136-141):
```python
tools_list = [
    ToolSpec(name=t.name, description=t.description, parameters=t.input_schema)
    for t in tools.values()  # Iterate over tool instances
]
```

**Provider converts ToolSpec → Anthropic format** (provider-anthropic/__init__.py:891):
```python
anthropic_tools = [
    {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters
    }
    for tool in tools_list
]
```

**Sent to Anthropic API**:
```json
{
  "model": "claude-sonnet-4-5",
  "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "Read session.py"}],
  "tools": [
    {
      "name": "read_file",
      "description": "Read a file from filesystem...",
      "input_schema": {
        "type": "object",
        "properties": {"file_path": {"type": "string"}, ...},
        "required": ["file_path"]
      }
    },
    // ... more tools
  ]
}
```

### Round 2: LLM Decides to Use Tool

**Anthropic responds**:
```json
{
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01234567890",
      "name": "read_file",
      "input": {"file_path": "session.py"}
    }
  ]
}
```

**Provider parses response** (provider-anthropic/__init__.py:911-966):
```python
tool_calls = []
for block in response.content:
    if block.type == "tool_use":
        tool_calls.append(
            ToolCall(
                id=block.id,
                name=block.name,
                arguments=block.input
            )
        )

return ChatResponse(content=[...], tool_calls=tool_calls)
```

### Round 3: Orchestrator Executes Tool

**Tool lookup and execution** (loop-basic/__init__.py:259):
```python
tool_name = tc.name  # "read_file"
tool = tools.get(tool_name)  # Dict lookup - returns Tool instance

# Execute via protocol method
result = await tool.execute(tc.arguments)  # {"file_path": "session.py"}
```

**Tool executes** (in tool-filesystem module):
```python
async def execute(self, input: dict) -> ToolResult:
    file_path = input["file_path"]
    content = read_file(file_path)
    return ToolResult(success=True, output=content)
```

**Add result to context** (loop-basic/__init__.py:334-343):
```python
await context.add_message({
    "role": "tool",
    "tool_call_id": "toolu_01234567890",
    "content": "<file contents here>"
})
```

### Round 4: Back to LLM with Results

**Orchestrator continues loop** (loop-basic/__init__.py:345-347):
```python
iteration += 1
continue  # Back to top of while loop
```

**Next iteration**:
- Get messages from context (now includes tool result)
- Convert tools dict → ToolSpec list again (same tools available)
- Create ChatRequest with updated messages
- Send to LLM

**Provider sends**:
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Read session.py"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_01234567890", "name": "read_file", ...}]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_01234567890", "content": "<file contents>"}]}
  ],
  "tools": [/* same tools list */]
}
```

**LLM sees results and either**:
- Generates final text response → Loop exits
- Makes more tool calls → Cycle repeats

---

## Key Architectural Insights

### 1. The Coordinator is Infrastructure (Part of Core)

**Location**: `amplifier-core/coordinator.py`

**Role**: Minimal context plumbing that allows modules to work together without knowing about each other

**Not policy**: Doesn't decide which provider to use, how to orchestrate, what to log

### 2. Tools Dict is Simple Python Dict

No complex registry - just `dict[str, Tool]`:
- Built at session initialization
- Modules self-register via `coordinator.mount("tools", tool, name)`
- Session retrieves via `coordinator.get("tools")`
- Passed to orchestrator as parameter
- Orchestrator uses dict lookup: `tools.get(tool_name)`

### 3. Protocol-Based Duck Typing

Orchestrator doesn't import tool modules:
```python
# Orchestrator doesn't know what FilesystemTool is
tool = tools.get("read_file")  # Returns something implementing Tool protocol

# Just knows it has these methods
assert hasattr(tool, "name")
assert hasattr(tool, "execute")

# Calls protocol method
result = await tool.execute(args)  # Works via duck typing!
```

### 4. Two Separate Channels for Tool Information

**Channel 1: Structured Data** (ChatRequest.tools)
- Tool definitions with schemas
- Sent to LLM API every request
- How LLM knows what tools exist and how to call them

**Channel 2: Text Instructions** (System message)
- Policies about WHEN to use tools
- Not comprehensive tool listings
- Focused on usage patterns, not capabilities catalog

**Foundation Pattern**: 
- Root coordinators DON'T list all tools in markdown
- Specialized agents DO list their specific tool subset
- Trust ChatRequest.tools for capability awareness
- Use text for usage policies and patterns

---

## The Complete Tool Invocation Cycle

### Simplified Diagram

```
1. Bundle YAML
   tools: [tool-filesystem, tool-bash]
        ↓
2. Session loads & mounts modules
   coordinator.mount("tools", tool, name="bash")
        ↓
3. Tools stored in dict
   mount_points["tools"] = {"bash": <instance>, "read_file": <instance>, ...}
        ↓
4. Session gets dict & passes to orchestrator
   tools = coordinator.get("tools")
   orchestrator.execute(tools=tools)
        ↓
5. Orchestrator converts to ToolSpec list
   tools_list = [ToolSpec(name=t.name, ...) for t in tools.values()]
        ↓
6. Provider converts to API format
   anthropic_tools = [{name: t.name, input_schema: t.parameters} for t in tools_list]
        ↓
7. Sent to Anthropic API
   POST /v1/messages {messages: [...], tools: anthropic_tools}
        ↓
8. LLM responds with tool_use
   {content: [{type: "tool_use", name: "read_file", input: {...}}]}
        ↓
9. Provider parses to ToolCall objects
   ToolCall(id="...", name="read_file", arguments={...})
        ↓
10. Orchestrator looks up tool
    tool = tools.get("read_file")  # Dict lookup by name
        ↓
11. Orchestrator executes tool
    result = await tool.execute(arguments)
        ↓
12. Add result to context
    context.add_message({role: "tool", content: result})
        ↓
13. Loop continues
    Get updated messages → Send to LLM with tool results → Repeat
```

### Detailed Code References

**Step 5: Convert to ToolSpec**
- File: `amplifier-module-loop-basic/__init__.py`
- Lines: 136-141
- Action: `ToolSpec(name=t.name, description=t.description, parameters=t.input_schema)`

**Step 6: Convert to Anthropic format**
- File: `amplifier-module-provider-anthropic/__init__.py`
- Lines: 891-909
- Action: Transform ToolSpec → `{name, description, input_schema}` dict

**Step 7: Send to API**
- File: `amplifier-module-provider-anthropic/__init__.py`
- Lines: 461-466
- Action: `params["tools"] = self._convert_tools_from_request(request.tools)`

**Step 9: Parse tool_use**
- File: `amplifier-module-provider-anthropic/__init__.py`
- Lines: 911-966
- Action: Convert `tool_use` blocks → `ToolCall` objects

**Step 10-11: Execute tool**
- File: `amplifier-module-loop-basic/__init__.py`
- Lines: 259-288
- Action: `tool = tools.get(tool_name)` then `await tool.execute(args)`

**Step 12: Add to context**
- File: `amplifier-module-loop-basic/__init__.py`
- Lines: 334-343
- Action: `context.add_message({role: "tool", tool_call_id: ..., content: ...})`

---

## Message Flow Example

### Initial Request
```python
# To LLM
{
    "messages": [
        {"role": "system", "content": "You are Amplifier..."},
        {"role": "user", "content": "Read session.py"}
    ],
    "tools": [
        {
            "name": "read_file",
            "description": "Read a file...",
            "input_schema": {"type": "object", "properties": {...}}
        }
    ]
}
```

### LLM Response (with tool call)
```python
# From LLM
{
    "content": [
        {
            "type": "tool_use",
            "id": "toolu_01234567890",
            "name": "read_file",
            "input": {"file_path": "session.py"}
        }
    ]
}
```

### After Tool Execution
```python
# To LLM (next iteration)
{
    "messages": [
        {"role": "system", "content": "You are Amplifier..."},
        {"role": "user", "content": "Read session.py"},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_01234567890",
                    "name": "read_file",
                    "input": {"file_path": "session.py"}
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01234567890",
                    "content": "# File contents here..."
                }
            ]
        }
    ],
    "tools": [/* same tools list */]
}
```

### LLM Final Response (no more tool calls)
```python
# From LLM
{
    "content": [
        {
            "type": "text",
            "text": "I've read the session.py file. It contains..."
        }
    ]
}
```

Loop exits when `tool_calls` is empty or None.

---

## How This Enables Zero-Coupling Architecture

### What Each Module Knows

**tool-bash knows**:
- ✅ Tool protocol (name, description, execute)
- ✅ ModuleCoordinator (from mount)
- ❌ What orchestrator is running
- ❌ What other tools exist
- ❌ How it will be invoked

**loop-basic knows**:
- ✅ Orchestrator protocol signature
- ✅ Tool, Provider, ContextManager protocols (duck typing)
- ❌ What specific tools are in the dict
- ❌ What specific provider implementation is used
- ❌ What context manager implementation is used

**provider-anthropic knows**:
- ✅ Provider protocol
- ✅ Anthropic API format
- ❌ What orchestrator is calling it
- ❌ What tools are available
- ❌ What context manager is storing messages

**context-simple knows**:
- ✅ ContextManager protocol
- ✅ Its own compaction strategy
- ❌ What orchestrator is calling it
- ❌ What tools are being used
- ❌ What provider will receive messages

### The Session Ties It Together

```python
# session.py:254-260
async def execute(self, prompt: str) -> str:
    # Get modules from coordinator (by protocol)
    orchestrator = self.coordinator.get("orchestrator")
    context = self.coordinator.get("context")
    providers = self.coordinator.get("providers")  # dict
    tools = self.coordinator.get("tools")          # dict
    hooks = self.coordinator.get("hooks")
    
    # Pass to orchestrator - everything via parameters
    return await orchestrator.execute(
        prompt=prompt,
        context=context,    # Protocol-conforming instance
        providers=providers, # Dict of protocol-conforming instances
        tools=tools,        # Dict of protocol-conforming instances
        hooks=hooks,
    )
```

**The beauty**: Orchestrator receives typed dicts (`dict[str, Tool]`) but doesn't know the concrete classes. Just calls protocol methods.

---

## Why This Architecture Matters

### Benefits

1. **Independent Module Development**
   - Tool developers don't need orchestrator code
   - Orchestrator developers don't need tool repos
   - Each module is independently testable

2. **Runtime Composition**
   - Configuration determines what gets loaded
   - Swap modules by changing YAML
   - No recompilation needed

3. **Stable Kernel**
   - Protocols rarely change
   - Modules evolve rapidly at the edges
   - "Center stays still, edges move fast"

4. **Zero Cross-Dependencies**
   - All modules → kernel (one direction only)
   - No module → module dependencies
   - Clean dependency graph

### The Tradeoff

**Flexibility for discovery complexity**: Modules don't advertise what they provide (like available skills). They just implement protocols and register themselves.

This is the challenge we're solving: **How to make discovered content (skills) visible when the architecture assumes static protocol implementations.**

---

## Implications for Skills Visibility

### What We Now Understand

1. **Tools are visible** because:
   - They're in the tools dict
   - Dict is converted to ToolSpec list
   - List is sent to LLM API as structured data
   - LLM automatically sees tool definitions

2. **Skills are NOT visible** because:
   - They're content discovered by tool-skills at mount time
   - They're stored in `tool.skills` dict (not a separate mount point)
   - They're not in ChatRequest.tools (they're not tools themselves)
   - No mechanism currently injects them into text context

3. **The solution must**:
   - Access discovered skills from `tool.skills` dict
   - Inject into text context (can't use tools parameter)
   - Use existing mechanisms (hooks with inject_context)
   - Be integrated with tool-skills (tight coupling is appropriate)

### Next Steps

This understanding informs how we design the skills visibility feature. We now know:
- Where skills data lives (tool.skills dict)
- How to access it (via coordinator.get("tools")["load_skill"].skills)
- What mechanism to use (HookResult with inject_context action)
- When to inject (provider:request event, like todo-reminder)
- Why it needs to be integrated (tight coupling to tool-skills)

---

## Repository Locations

For reference, the code examined:

- `amplifier-core/` - Kernel (protocols, session, coordinator, loader)
- `amplifier-module-loop-basic/` - Basic orchestrator implementation
- `amplifier-module-provider-anthropic/` - Anthropic provider implementation
- `amplifier-module-tool-filesystem/` - Example tool implementation
- `amplifier-module-tool-bash/` - Example tool implementation
- `amplifier-module-context-simple/` - Context manager implementation

All located in: `/Users/robotdad/Source/Work/skills/`
