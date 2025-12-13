from langchain_core.tools import tool
from langgraph.types import Command
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage

@tool
def propose_changes(path: str, diff: str, action: str = "update", runtime: ToolRuntime = None) -> Command:
    """Update proposed_changes state incrementally."""
    tool_call_id = runtime.tool_call_id if runtime else "unknown"
    return Command(
        update={
            "proposed_changes": [{
                "file_path": path,
                "diff": diff,
                "action": action
            }],
            "messages": [ToolMessage(
                content=f"Proposed changes for {path} ({action})",
                tool_call_id=tool_call_id
            )]
        }
    )