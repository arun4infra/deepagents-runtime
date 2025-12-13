"""
Pre-Work Validation Tool - Checks if specialist agents have required prerequisites.

This tool performs prerequisite checks before each specialist is invoked,
verifying that all required input files exist for the agent to do its work.
"""
from typing import Dict, List, Annotated, TypedDict
from langchain_core.tools import tool
from langchain.tools import InjectedState


class FileData(TypedDict):
    """Data structure for storing file contents with metadata."""
    content: List[str]
    created_at: str
    modified_at: str


# Mapping of files to the agents responsible for creating them
FILE_TO_AGENT_MAPPING = {
    "/user_request.md": "Orchestrator (Step 1)",
    "/guardrail_assessment.md": "Guardrail Agent",
    "/impact_assessment.md": "Impact Analysis Agent",
    "/THE_SPEC/requirements.md": "Workflow Spec Agent",
    "/THE_SPEC/plan.md": "Workflow Spec Agent",
    "/THE_SPEC/constitution.md": "Workflow Spec Agent",
    "/THE_CAST/": "Agent Spec Agent"
}

# Prerequisites per specialist agent
AGENT_PREREQUISITES = {
    "Guardrail Agent": {
        "files": ["/user_request.md"],
        "description": "User request file for assessment"
    },
    "Impact Analysis Agent": {
        "files": [
            "/user_request.md",
            "/guardrail_assessment.md"
        ],
        "description": "User request and guardrail assessment for blueprint creation"
    },
    "Workflow Spec Agent": {
        "files": ["/impact_assessment.md"],
        "description": "Impact assessment with implementation plan"
    },
    "Agent Spec Agent": {
        "files": ["/impact_assessment.md"],
        "description": "Impact assessment with implementation plan"
    },
    "Multi-Agent Compiler Agent": {
        "files": [
            "/THE_SPEC/requirements.md",
            "/THE_SPEC/plan.md",
            "/THE_SPEC/constitution.md",
            "/THE_CAST/"
        ],
        "description": "All specification files for compilation"
    }
}


@tool
def pre_work(
    agent_name: str,
    files: Annotated[Dict[str, FileData], InjectedState("files")]
) -> str:
    """Validates that all prerequisites exist before invoking a specialist agent.
    
    This tool checks the agent state files to ensure all required input files exist
    before a specialist agent is invoked. Use this to catch missing prerequisites
    early and avoid wasted agent invocations.
    
    Args:
        agent_name: Name of the specialist agent to check prerequisites for
        files: Agent state files dict (automatically injected, not visible to LLM)
    
    Returns:
        Success message if all prerequisites exist, or detailed error with missing files.
        
    Example Usage:
        Before invoking Impact Analysis Agent:
        pre_work(agent_name="Impact Analysis Agent")
        
        Returns either:
        - "✓ PRE-WORK PASSED: All prerequisites verified for Impact Analysis Agent"
        - "✗ PRE-WORK FAILED: Missing prerequisites for Impact Analysis Agent: ..."
    """
    try:
        # Debug: Check if files dict is available
        if files is None:
            return f"✗ PRE-WORK ERROR: Files dict is None. This indicates InjectedState is not working correctly."
        
        if not isinstance(files, dict):
            return f"✗ PRE-WORK ERROR: Files is not a dict, got type: {type(files)}"
    except Exception as e:
        return f"✗ PRE-WORK ERROR: Exception accessing files parameter: {str(e)}"
    
    # Validate agent name
    if agent_name not in AGENT_PREREQUISITES:
        available_agents = ", ".join(AGENT_PREREQUISITES.keys())
        return f'''Error: Unknown agent name "{agent_name}".

Available agents for prerequisite checking:
{available_agents}

Please use the exact agent name from the list above.'''
    
    config = AGENT_PREREQUISITES[agent_name]
    required_files = config["files"]
    description = config["description"]
    
    missing_files = []
    
    # Check file existence in agent state files dict
    for file_path in required_files:
        # Special handling for directory checks (ends with /)
        if file_path.endswith("/"):
            # Check if any files in state start with this directory path
            dir_files = [f for f in files.keys() if f.startswith(file_path)]
            if not dir_files:
                missing_files.append(f"{file_path} (directory does not exist or is empty)")
        else:
            # Regular file check - look for file in state files dict
            if file_path not in files:
                missing_files.append(file_path)
    
    # Return result
    if not missing_files:
        return f"✓ PRE-WORK PASSED: All prerequisites verified for {agent_name}"
    else:
        # Build detailed missing files list with responsible agents
        missing_details = []
        agents_to_retry = set()
        
        for missing_file in missing_files:
            # Extract the file path (remove directory status messages)
            file_path = missing_file.split(" (")[0]
            responsible_agent = FILE_TO_AGENT_MAPPING.get(file_path, "Unknown")
            missing_details.append(f"{missing_file} → Retry: {responsible_agent}")
            
            # Track which agents need to be retried (skip Orchestrator)
            if responsible_agent != "Orchestrator (Step 1)":
                agents_to_retry.add(responsible_agent)
        
        missing_list = "\n  - ".join(missing_details)
        
        # Build retry instruction
        if agents_to_retry:
            retry_agents = ", ".join(sorted(agents_to_retry))
            retry_instruction = f"Re-invoke the following agent(s) to create the missing file(s): {retry_agents}"
        else:
            retry_instruction = "Workflow initialization incomplete. Ensure Step 1 (Document Your Mission) is completed."
        
        return f'''✗ PRE-WORK FAILED: Missing prerequisites for {agent_name}

Expected: {description}

Missing files and responsible agents:
  - {missing_list}

REQUIRED ACTION:
{retry_instruction}'''
