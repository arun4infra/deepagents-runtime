"""
Unit tests for orchestrator tools (pre_work and post_work) with InjectedState.
"""
import pytest
from tests.mock.tools.pre_work import pre_work
from tests.mock.tools.post_work import post_work


def test_pre_work_with_injected_state():
    """Test that pre_work tool works with InjectedState."""
    # Simulate agent state with files dict (FileData structure)
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
    
    # The tool should be callable with the state
    # In actual agent execution, the files parameter is injected automatically
    # For testing, we need to pass it explicitly
    result = pre_work.invoke({
        "agent_name": "Impact Analysis Agent",
        "files": mock_state["files"]
    })
    
    # Should pass because both required files exist
    assert "✓ PRE-WORK PASSED" in result
    assert "Impact Analysis Agent" in result


def test_pre_work_missing_files():
    """Test pre_work detects missing files."""
    mock_state = {
        "messages": [],
        "files": {
            "/user_request.md": {
                "content": ["# User Request", "", "Test content"],
                "created_at": "2025-12-13T00:00:00Z",
                "modified_at": "2025-12-13T00:00:00Z"
            }
            # Missing /guardrail_assessment.md
        }
    }
    
    result = pre_work.invoke({
        "agent_name": "Impact Analysis Agent",
        "files": mock_state["files"]
    })
    
    # Should fail because guardrail_assessment.md is missing
    assert "✗ PRE-WORK FAILED" in result
    assert "/guardrail_assessment.md" in result


def test_post_work_with_injected_state():
    """Test that post_work tool works with InjectedState."""
    mock_state = {
        "messages": [],
        "files": {
            "/guardrail_assessment.md": {
                "content": [
                    "# Guardrail Assessment",
                    "",
                    "## Overall Assessment",
                    "",
                    "Status: APPROVED",
                    "",
                    "## Contextual Guardrails",
                    "",
                    "Test content"
                ],
                "created_at": "2025-12-13T00:00:00Z",
                "modified_at": "2025-12-13T00:00:00Z"
            }
        }
    }
    
    result = post_work.invoke({
        "agent_name": "Guardrail Agent",
        "files": mock_state["files"]
    })
    
    # Should pass because file exists with required content
    assert "✓ QC PASSED" in result
    assert "Guardrail Agent" in result


def test_post_work_missing_content():
    """Test post_work detects missing required content."""
    mock_state = {
        "messages": [],
        "files": {
            "/guardrail_assessment.md": {
                "content": ["# Guardrail Assessment", "", "Incomplete content"],
                "created_at": "2025-12-13T00:00:00Z",
                "modified_at": "2025-12-13T00:00:00Z"
            }
        }
    }
    
    result = post_work.invoke({
        "agent_name": "Guardrail Agent",
        "files": mock_state["files"]
    })
    
    # Should fail because required content sections are missing
    assert "✗ QC FAILED" in result
    assert "Missing required content" in result
