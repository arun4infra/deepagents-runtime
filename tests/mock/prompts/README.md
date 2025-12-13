# Agent System Prompts

This directory contains system prompts for each agent in the test definition.

## Purpose

System prompts are stored in separate `.md` files for:
- **Better readability**: Markdown format with proper formatting
- **Easier debugging**: Can view/edit prompts without parsing JSON
- **Version control**: Cleaner diffs when prompts change

## File Naming Convention

Each file is named after the agent's `id` field from `definition.json`:
- `builder_agent_orchestrator.md` → Orchestrator agent
- `guardrail-agent.md` → Guardrail specialist
- `impact-analysis-agent.md` → Impact Analysis specialist
- `workflow-spec-agent.md` → Workflow Spec specialist
- `agent-spec-agent.md` → Agent Spec specialist
- `multiagent-compiler-agent.md` → Multi-Agent Compiler specialist

## How It Works

1. `definition.json` contains placeholder: `"system_prompt": "loaded from file"`
2. Test helper `load_definition_with_files()` reads the JSON
3. For each node with placeholder, it loads content from `{node_id}.md`
4. Returns complete definition with prompts and tools loaded

## Usage in Tests

```python
from tests.integration.test_helpers import load_definition_with_files

definition = load_definition_with_files(Path("tests/mock/definition.json"))
# definition now has all system_prompts and tool scripts loaded from files
```

## Note

This is **only for test definitions**. Production definitions should continue using inline prompts or their own loading mechanism.
