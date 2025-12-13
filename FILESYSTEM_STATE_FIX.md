# Filesystem State Access Fix for Orchestrator Tools

## Problem

The `pre_work` and `post_work` validation tools were checking the OS filesystem using `os.path.isfile()`, but DeepAgents stores files in the **agent state** (in-memory) using a `FileData` structure, not as plain strings on disk. This caused validation failures even when files were created by the orchestrator.

### Error Observed
```
✗ PRE-WORK FAILED: Missing files and responsible agents: /user_request.md → Retry: Orchestrator (Step 1)
```

The orchestrator created `/user_request.md` using `write_file()`, but `pre_work` couldn't find it because it was looking in the wrong place.

## Root Cause

From DeepAgents documentation:
- **Files are stored in agent STATE by default**, not on disk
- `result.get("files", {})` contains all files created by the agent as `dict[str, FileData]`
- `FileData` structure: `{"content": List[str], "created_at": str, "modified_at": str}`
- Files persist in agent state for the conversation thread
- To access real filesystem, you need to configure `FilesystemBackend(root_dir="/path")`

## Solution

Use `InjectedState` to access the agent's `files` dict from within tools.

### Code Changes

#### 1. Import InjectedState and Define FileData
```python
from typing import Dict, List, Annotated, TypedDict
from langchain_core.tools import tool
from langchain.tools import InjectedState


class FileData(TypedDict):
    """Data structure for storing file contents with metadata."""
    content: List[str]
    created_at: str
    modified_at: str
```

#### 2. Update Tool Signature
```python
@tool
def pre_work(
    agent_name: str,
    files: Annotated[Dict[str, FileData], InjectedState("files")]
) -> str:
    """Validates that all prerequisites exist before invoking a specialist agent.
    
    Args:
        agent_name: Name of the specialist agent to check prerequisites for
        files: Agent state files dict (automatically injected, not visible to LLM)
    """
```

#### 3. Check Files in State Instead of OS
**Before (checking OS filesystem):**
```python
check_path = file_path.lstrip("/")
if not os.path.isfile(check_path):
    missing_files.append(file_path)
```

**After (checking agent state):**
```python
if file_path not in files:
    missing_files.append(file_path)
```

#### 4. Directory Checks
**Before:**
```python
if not os.path.isdir(check_path):
    missing_files.append(f"{file_path} (directory does not exist)")
```

**After:**
```python
dir_files = [f for f in files.keys() if f.startswith(file_path)]
if not dir_files:
    missing_files.append(f"{file_path} (directory does not exist or is empty)")
```

## How InjectedState Works

From LangGraph documentation:

```python
class InjectedState(InjectedToolArg):
    """Annotation for injecting graph state into tool arguments.
    
    This annotation enables tools to access graph state without exposing state
    management details to the language model. Tools annotated with `InjectedState`
    receive state data automatically during execution while remaining invisible
    to the model's tool-calling interface.
    """
```

### Key Points:
1. **Invisible to LLM**: The `files` parameter is NOT included in the tool schema shown to the LLM
2. **Automatically Injected**: The runtime injects the state value when the tool is called
3. **Type-Safe**: Uses Python type annotations for validation
4. **Field-Specific**: `InjectedState("files")` extracts just the `files` field from state

## Testing

### Unit Tests
```python
def test_pre_work_with_injected_state():
    """Test that pre_work tool works with InjectedState."""
    mock_state = {
        "messages": [],
        "files": {
            "/user_request.md": {
                "content": ["# User Request", "", "Test content"],
                "created_at": "2025-12-13T00:00:00Z",
                "modified_at": "2025-12-13T00:00:00Z"
            },
            "/guardrail_assessment.md": {
                "content": ["# Guardrail Assessment", "", "Test content"],
                "created_at": "2025-12-13T00:00:00Z",
                "modified_at": "2025-12-13T00:00:00Z"
            }
        }
    }
    
    result = pre_work.invoke({
        "agent_name": "Impact Analysis Agent",
        "files": mock_state["files"]
    })
    
    assert "✓ PRE-WORK PASSED" in result
```

### Integration Test
The orchestrator now successfully:
1. ✅ Creates files using `write_file()` (stored in agent state)
2. ✅ Calls `pre_work` tool with agent name only
3. ✅ Tool automatically receives `files` dict from state
4. ✅ Validates files exist in state
5. ✅ Returns success/failure message

## Files Modified

1. `tests/mock/tools/pre_work.py` - Updated to use InjectedState
2. `tests/mock/tools/post_work.py` - Updated to use InjectedState
3. `tests/unit/test_orchestrator_tools.py` - New unit tests
4. `test_orchestrator_e2e.py` - End-to-end validation test

## Verification

Run the unit tests:
```bash
python -m pytest tests/unit/test_orchestrator_tools.py -v
```

Expected output:
```
tests/unit/test_orchestrator_tools.py::test_pre_work_with_injected_state PASSED
tests/unit/test_orchestrator_tools.py::test_pre_work_missing_files PASSED
tests/unit/test_orchestrator_tools.py::test_post_work_with_injected_state PASSED
tests/unit/test_orchestrator_tools.py::test_post_work_missing_content PASSED
```

## Related Documentation

- DeepAgents: https://github.com/langchain-ai/deepagents
- LangGraph InjectedState: https://langchain-ai.github.io/langgraph/reference/prebuilt/#injectedstate
- Agent State Management: Files persist in `result.get("files", {})` by default

## Next Steps

With this fix in place:
1. ✅ Orchestrator tools can access agent state files
2. ✅ Pre-work validation works correctly
3. ✅ Post-work validation works correctly
4. 🔄 Ready to test full orchestrator workflow with subagent invocations
