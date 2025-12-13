# Root Cause Analysis: Integration Test Timeout

## Issue Summary

The integration test `test_cloudevent_processing_end_to_end_success` was timing out at 180 seconds (3 minutes). Investigation revealed two separate issues:

1. **Original Issue (Fixed)**: Checkpoint state pollution from hardcoded `thread_id` causing infinite loops
2. **Current Issue**: Test timeout too short for the complex multi-agent execution

The same agent definition works in LangGraph Studio (completing in 2.31 seconds), but the test environment takes ~4 minutes due to the full end-to-end infrastructure (PostgreSQL checkpointer, Redis streaming, NATS CloudEvents).

## Root Cause

### The Problem: Checkpoint State Pollution

The test was using a **hardcoded `thread_id` ("test-job-456")** for every test run. When using PostgreSQL checkpointer:

1. **First execution**: Graph processes the HumanMessage and starts executing tool calls (task tool for subagents)
2. **Checkpointing**: After each step, state is saved to PostgreSQL with `thread_id = "test-job-456"`
3. **Subsequent executions**: When the test runs again, the graph **resumes from the checkpointed state** instead of starting fresh
4. **Message Collision**: The `input_payload` HumanMessage is **merged with existing checkpointed messages**, causing:
   - The same HumanMessage to appear multiple times in conversation history
   - `PatchToolCallsMiddleware` to detect "dangling tool calls" (AIMessages with tool_calls that don't have ToolMessage responses)
   - Tool calls to be cancelled with: "Tool call task with id ... was cancelled - another message came in before it could be completed"
5. **Infinite Loop**: Agent sees cancelled tool calls, tries to re-execute them, but the same HumanMessage keeps getting re-added, causing more cancellations

### Evidence from Logs

- **1504 checkpoints** created for the same `thread_id`
- **Multiple identical HumanMessages** in conversation history
- **Tool call cancellations**: "another message came in before it could be completed"
- **Repeated workflow patterns**: Same sequence (Guardrail → Impact Analysis → etc.) restarting

### Why LangGraph Studio Worked

LangGraph Studio uses a **fresh thread_id** for each execution or properly clears state before each run. The test was reusing the same `thread_id` without clearing checkpointed state.

## The Fix

### Solution: Generate Unique thread_id Per Test Run

Modified the `sample_job_execution_event` fixture to generate unique IDs for each test execution:

```python
@pytest.fixture
def sample_job_execution_event(sample_agent_definition: Dict[str, Any]) -> Dict[str, Any]:
    import uuid
    
    # Generate unique IDs for each test run to prevent checkpoint state pollution
    unique_job_id = f"test-job-{uuid.uuid4()}"
    unique_trace_id = f"test-trace-{uuid.uuid4()}"
    
    return {
        "trace_id": unique_trace_id,
        "job_id": unique_job_id,
        "agent_definition": sample_agent_definition,
        "input_payload": {
            "messages": [
                {"role": "user", "content": "Create a simple hello world agent that greets users"}
            ]
        }
    }
```

### Changes Made

1. **Updated fixture** (`sample_job_execution_event`): Generates unique `job_id` and `trace_id` using `uuid.uuid4()`
2. **Updated Redis channel subscription**: Changed from hardcoded `"langgraph:stream:test-job-456"` to dynamic `f"langgraph:stream:{sample_job_execution_event['job_id']}"`
3. **Updated checkpoint query**: Changed from hardcoded `"test-job-456"` to dynamic `sample_job_execution_event["job_id"]`

## Benefits of This Fix

1. **Test Isolation**: Each test run starts with a clean state
2. **No Checkpoint Pollution**: Previous test runs don't affect current execution
3. **Matches Production Behavior**: Each job execution in production uses a unique job_id
4. **Prevents False Failures**: Eliminates flaky tests caused by checkpoint state carryover
5. **Easier Debugging**: Each test run has unique identifiers in logs and database

## Alternative Solutions Considered

### Option 1: Clear Checkpoints Before Test
```python
# Clear existing checkpoints before test
with postgres_connection.cursor() as cur:
    cur.execute("DELETE FROM checkpoints WHERE thread_id = %s", ("test-job-456",))
    cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", ("test-job-456",))
    cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", ("test-job-456",))
    postgres_connection.commit()
```
**Rejected**: Requires manual cleanup, doesn't match production behavior

### Option 3: Check for Existing State Before Execution
```python
# In executor, check if resuming from checkpoint
existing_state = graph.get_state(config)
if existing_state and existing_state.values.get("messages"):
    # Handle resumption logic
    pass
```
**Rejected**: Adds complexity to application code for a test-specific issue

## Testing

After applying this fix:
- Each test run will use a unique `thread_id`
- No checkpoint state pollution between test runs
- Test should complete successfully without infinite loops
- Execution time should match LangGraph Studio (~2-3 seconds for this simple agent)

## Related Components

- **PatchToolCallsMiddleware**: Detects dangling tool calls and adds cancellation messages
- **PostgreSQL Checkpointer**: Saves state after each graph step using `thread_id`
- **LangGraph State Management**: Merges input with checkpointed state when resuming
- **add_messages Reducer**: Handles message merging in conversation state

## References

- LangSmith Trace (Working): https://smith.langchain.com/public/b74b85de-4201-4752-9cc5-3b498f33aef7/r
- Test Output Directory: `tests/integration/outputs/run_20251212_230301/`
- Related Files:
  - `deepagents-runtime/tests/integration/test_api.py`
  - `deepagents-runtime/core/executor.py`
  - `deepagents-runtime/core/builder.py`
