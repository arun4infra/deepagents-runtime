# Orchestrator Tools Fix

## Problem
The orchestrator was created with `tools=[]` (empty list) in `builder.py`, preventing it from accessing the `pre_work` and `post_work` validation tools defined in `definition.json`.

## Solution
Added code to extract and resolve orchestrator tools from config before passing to `create_deep_agent`.

## Changes Made

**File:** `deepagents-runtime/core/builder.py`

**Location:** Lines ~255-270 (after extracting system_prompt, before logging)

**Added:**
```python
# Extract and resolve orchestrator tools
orchestrator_tool_names = orchestrator_actual_config.get("tools", [])
orchestrator_tools = []

for tool_name in orchestrator_tool_names:
    if tool_name in available_tools:
        orchestrator_tools.append(available_tools[tool_name])
    else:
        logger.warning(
            "orchestrator_tool_not_found",
            tool_name=tool_name,
            available_tools=list(available_tools.keys())
        )
```

**Updated logging to include tool info:**
```python
requested_tools=orchestrator_tool_names,
resolved_tools=len(orchestrator_tools),
tool_names=[t.name if hasattr(t, 'name') else str(t) for t in orchestrator_tools],
```

**Changed create_deep_agent call:**
```python
# Before:
tools=[],

# After:
tools=orchestrator_tools,  # Pass resolved orchestrator tools
```

## Verification

Test logs now show:
```json
{
  "requested_tools": ["pre_work", "post_work"],
  "resolved_tools": 2,
  "tool_names": ["pre_work", "post_work"]
}
```

## Impact
- ✅ Orchestrator can now use `pre_work` and `post_work` validation tools
- ✅ No more manual file checks with `ls`
- ✅ Proper validation workflow can execute
- ✅ Minimal change (15 lines added)
- ✅ No breaking changes to existing functionality

## Related Files
- `deepagents-runtime/tests/mock/tools/pre_work.py` - Pre-work validation tool
- `deepagents-runtime/tests/mock/tools/post_work.py` - Post-work validation tool  
- `deepagents-runtime/tests/mock/definition.json` - Defines orchestrator tools
- `deepagents-runtime/core/mainagent_builder.py` - Alternative modular approach (not used)
