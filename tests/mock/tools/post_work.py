"""
Post-Work Validation Tool - Checks if specialist agents created their mandatory deliverables.

This tool performs Quality Control (QC) checks after each specialist completes,
verifying that all mandatory deliverable files exist and contain required content.
"""
from typing import Dict, List, Annotated, TypedDict
from langchain_core.tools import tool
from langchain.tools import InjectedState


class FileData(TypedDict):
    """Data structure for storing file contents with metadata."""
    content: List[str]
    created_at: str
    modified_at: str


# Mandatory deliverables per specialist agent
AGENT_DELIVERABLES = {
    "Guardrail Agent": {
        "files": ["/guardrail_assessment.md"],
        "description": "Guardrail assessment document with security and policy validation",
        "content_checks": {
            "/guardrail_assessment.md": [
                "## Overall Assessment",
                "Status:",
                "## Contextual Guardrails"
            ]
        }
    },
    "Impact Analysis Agent": {
        "files": ["/impact_assessment.md"],
        "description": "Impact assessment with file-by-file implementation plan",
        "content_checks": {
            "/impact_assessment.md": [
                "requirements.md",
                "constitution.md",
                "plan.md",
                "## File-by-File Implementation Plan",
                "## Constitutional Compliance Analysis"
            ]
        }
    },
    "Workflow Spec Agent": {
        "files": [
            "/THE_SPEC/constitution.md",
            "/THE_SPEC/plan.md",
            "/THE_SPEC/requirements.md"
        ],
        "description": "Workflow-level specification files (constitution, plan, requirements)",
        "content_checks": {}  # No content validation - existence only
    },
    "Agent Spec Agent": {
        "files": ["/THE_CAST/"],  # Directory check - at least one file should exist
        "description": "Agent specification files in /THE_CAST/ directory",
        "content_checks": {}  # Content checks done per-file in directory
    },
    "Multi-Agent Compiler Agent": {
        "files": ["/definition.json"],
        "description": "Compiled workflow definition",
        "content_checks": {}  # Skip - already validated by validate_definition tool
    }
}


@tool
def post_work(
    agent_name: str,
    files: Annotated[Dict[str, FileData], InjectedState("files")]
) -> str:
    """Validates that a specialist agent created all mandatory deliverable files.
    
    This tool checks the agent state files to ensure all required files exist after
    a specialist agent completes. Use this for Quality Control (QC) after each
    specialist finishes to catch missing deliverables early.
    
    Args:
        agent_name: Name of the specialist agent to verify (e.g., "Impact Analysis Agent")
        files: Agent state files dict (automatically injected, not visible to LLM)
    
    Returns:
        Success message if all files exist, or detailed error with missing files list.
        
    Example Usage:
        After Impact Analysis Agent completes:
        post_work(agent_name="Impact Analysis Agent")
        
        Returns either:
        - "✓ QC PASSED: All mandatory deliverables verified for Impact Analysis Agent"
        - "✗ QC FAILED: Missing deliverables for Impact Analysis Agent: ..."
    """
    # Debug: Check if files dict is available
    if files is None:
        return f"✗ QC ERROR: Files dict is None. This indicates InjectedState is not working correctly."
    
    if not isinstance(files, dict):
        return f"✗ QC ERROR: Files is not a dict, got type: {type(files)}"
    
    # Validate agent name
    if agent_name not in AGENT_DELIVERABLES:
        available_agents = ", ".join(AGENT_DELIVERABLES.keys())
        return f'''Error: Unknown agent name "{agent_name}".

Available agents for verification:
{available_agents}

Please use the exact agent name from the list above.'''
    
    config = AGENT_DELIVERABLES[agent_name]
    required_files = config["files"]
    description = config["description"]
    content_checks = config.get("content_checks", {})
    
    missing_files = []
    content_errors = []
    
    # Step 1: Check file existence in agent state files dict
    for file_path in required_files:
        # Special handling for directory checks (ends with /)
        if file_path.endswith("/"):
            # Check if any files in state start with this directory path
            dir_files = [f for f in files.keys() if f.startswith(file_path)]
            if not dir_files:
                missing_files.append(f"{file_path} (directory does not exist or is empty)")
            else:
                # For Agent Spec Agent, check content of files in directory
                if agent_name == "Agent Spec Agent":
                    for file_key in dir_files:
                        if file_key.endswith(".md"):
                            file_data = files[file_key]
                            # Join lines to get full content
                            content = "\n".join(file_data["content"])
                            # Check for required sections (case-insensitive)
                            content_lower = content.lower()
                            if "## system prompt" not in content_lower:
                                content_errors.append(f"{file_key}: Missing '## System Prompt' section")
                            if "## tools" not in content_lower:
                                content_errors.append(f"{file_key}: Missing '## Tools' section")
        else:
            # Regular file check - look for file in state files dict
            if file_path not in files:
                missing_files.append(file_path)
    
    # Step 2: Check file content (only if files exist)
    if not missing_files and content_checks:
        for file_path, required_strings in content_checks.items():
            if file_path in files:
                file_data = files[file_path]
                # Join lines to get full content
                content = "\n".join(file_data["content"])
                # Case-insensitive content check
                content_lower = content.lower()
                
                for required_string in required_strings:
                    if required_string.lower() not in content_lower:
                        content_errors.append(f"{file_path}: Missing required content '{required_string}'")
    
    # Step 3: Return result
    if not missing_files and not content_errors:
        return f"✓ QC PASSED: All mandatory deliverables verified for {agent_name}"
    
    # Build error message
    error_parts = []
    
    if missing_files:
        missing_list = "\n  - ".join(missing_files)
        error_parts.append(f'''Missing files:
  - {missing_list}''')
    
    if content_errors:
        content_list = "\n  - ".join(content_errors)
        error_parts.append(f'''Content validation failures:
  - {content_list}''')
    
    error_details = "\n\n".join(error_parts)
    
    # Generate revision prompt
    if missing_files and content_errors:
        action_msg = "create the missing files AND fix the content issues"
        example_prompt = f"The QC check failed. You must:\n1. Create the following missing files:\n{chr(10).join('   - ' + f for f in missing_files)}\n\n2. Fix the following content issues:\n{chr(10).join('   - ' + e for e in content_errors)}"
    elif missing_files:
        action_msg = "create the missing files"
        example_prompt = f"The QC check failed. You must create the following missing files:\n{chr(10).join('   - ' + f for f in missing_files)}"
    else:
        action_msg = "fix the content validation issues"
        example_prompt = f"The QC check failed. You must fix the following content issues:\n{chr(10).join('   - ' + e for e in content_errors)}"
    
    return f'''✗ QC FAILED: Deliverable validation failed for {agent_name}

Expected: {description}

{error_details}

REQUIRED ACTION:
Re-invoke the {agent_name} with a detailed prompt specifying what needs to be fixed.
The agent must {action_msg} before proceeding to the next step.

Example revision prompt:
"{example_prompt}

Please generate/update these files now according to the implementation plan."'''
