"""
Test the pre_work tool.
"""
import os
import tempfile
from pathlib import Path


def test_pre_work_tool():
    """Test the pre_work tool with a temporary filesystem."""
    # Import the tool
    from tests.mock.tools.pre_work import pre_work
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Test 1: Guardrail Agent - missing user_request.md
            result = pre_work.invoke({"agent_name": "Guardrail Agent"})
            assert "✗ PRE-WORK FAILED" in result
            assert "user_request.md" in result
            print("✅ Test 1 passed: Missing prerequisite detected")
            
            # Test 2: Guardrail Agent - user_request.md exists
            with open("user_request.md", "w") as f:
                f.write("Create a hello world agent\n")
            
            result = pre_work.invoke({"agent_name": "Guardrail Agent"})
            assert "✓ PRE-WORK PASSED" in result
            print("✅ Test 2 passed: Prerequisites verified")
            
            # Test 3: Impact Analysis Agent - missing guardrail_assessment.md
            result = pre_work.invoke({"agent_name": "Impact Analysis Agent"})
            assert "✗ PRE-WORK FAILED" in result
            assert "guardrail_assessment.md" in result
            print("✅ Test 3 passed: Multiple prerequisites check works")
            
            # Test 4: Impact Analysis Agent - all prerequisites exist
            with open("guardrail_assessment.md", "w") as f:
                f.write("# Guardrail Assessment\n")
            
            result = pre_work.invoke({"agent_name": "Impact Analysis Agent"})
            assert "✓ PRE-WORK PASSED" in result
            print("✅ Test 4 passed: All prerequisites verified")
            
            # Test 5: Workflow Spec Agent - missing impact_assessment.md
            result = pre_work.invoke({"agent_name": "Workflow Spec Agent"})
            assert "✗ PRE-WORK FAILED" in result
            assert "impact_assessment.md" in result
            print("✅ Test 5 passed: Workflow Spec prerequisites check")
            
            # Test 6: Multi-Agent Compiler - missing all spec files
            result = pre_work.invoke({"agent_name": "Multi-Agent Compiler Agent"})
            assert "✗ PRE-WORK FAILED" in result
            assert "requirements.md" in result or "plan.md" in result
            print("✅ Test 6 passed: Compiler prerequisites check")
            
            # Test 7: Multi-Agent Compiler - create all prerequisites
            os.makedirs("THE_SPEC", exist_ok=True)
            os.makedirs("THE_CAST", exist_ok=True)
            Path("THE_SPEC/requirements.md").write_text("# Requirements\n")
            Path("THE_SPEC/plan.md").write_text("# Plan\n")
            Path("THE_SPEC/constitution.md").write_text("# Constitution\n")
            Path("THE_CAST/agent.md").write_text("# Agent\n")
            Path("impact_assessment.md").write_text("# Impact\n")
            
            result = pre_work.invoke({"agent_name": "Multi-Agent Compiler Agent"})
            assert "✓ PRE-WORK PASSED" in result
            print("✅ Test 7 passed: All compiler prerequisites verified")
            
            # Test 8: Invalid agent name
            result = pre_work.invoke({"agent_name": "Invalid Agent"})
            assert "Error: Unknown agent name" in result
            print("✅ Test 8 passed: Invalid agent name handled")
            
        finally:
            os.chdir(original_cwd)
    
    print("\n✅ All 8 pre_work tool tests passed!")


if __name__ == "__main__":
    test_pre_work_tool()
