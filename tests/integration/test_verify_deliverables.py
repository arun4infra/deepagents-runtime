"""
Test the verify_deliverables tool.
"""
import os
import tempfile
import shutil
from pathlib import Path


def test_post_work_tool():
    """Test the post_work tool with a temporary filesystem."""
    # Import the tool
    from tests.mock.tools.post_work import post_work
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Test 1: Missing file - should fail
            result = post_work.invoke({"agent_name": "Guardrail Agent"})
            assert "✗ QC FAILED" in result
            assert "guardrail_assessment.md" in result
            print("✅ Test 1 passed: Correctly detected missing file")
            
            # Test 2: Create the file with valid content - should pass
            with open("guardrail_assessment.md", "w") as f:
                f.write("""# Guardrail Assessment

## Overall Assessment
Status: Approved

## Contextual Guardrails
1. Some guardrail
""")
            
            result = post_work.invoke({"agent_name": "Guardrail Agent"})
            assert "✓ QC PASSED" in result
            print("✅ Test 2 passed: Correctly verified existing file with valid content")
            
            # Test 3: Impact Analysis Agent - missing file
            result = post_work.invoke({"agent_name": "Impact Analysis Agent"})
            assert "✗ QC FAILED" in result
            assert "impact_assessment.md" in result
            print("✅ Test 3 passed: Impact Analysis Agent check works")
            
            # Test 4: Impact Analysis Agent - file exists but missing content
            with open("impact_assessment.md", "w") as f:
                f.write("# Impact Assessment\n\nSome content but missing required strings\n")
            
            result = post_work.invoke({"agent_name": "Impact Analysis Agent"})
            assert "✗ QC FAILED" in result
            assert "Content validation failures" in result
            assert "requirements.md" in result.lower()
            print("✅ Test 4 passed: Content validation detects missing strings")
            
            # Test 5: Impact Analysis Agent - valid content
            with open("impact_assessment.md", "w") as f:
                f.write("""# Impact Assessment

## Constitutional Compliance Analysis
Some analysis here

## File-by-File Implementation Plan

### 1. File: /THE_SPEC/requirements.md
### 2. File: /THE_SPEC/constitution.md  
### 3. File: /THE_SPEC/plan.md
""")
            
            result = post_work.invoke({"agent_name": "Impact Analysis Agent"})
            assert "✓ QC PASSED" in result
            print("✅ Test 5 passed: Valid content passes validation")
            
            # Test 6: Workflow Spec Agent - multiple files
            os.makedirs("THE_SPEC", exist_ok=True)
            result = post_work.invoke({"agent_name": "Workflow Spec Agent"})
            assert "✗ QC FAILED" in result
            assert "constitution.md" in result or "plan.md" in result or "requirements.md" in result
            print("✅ Test 6 passed: Multiple file check works")
            
            # Create all required files
            Path("THE_SPEC/constitution.md").write_text("# Constitution\n")
            Path("THE_SPEC/plan.md").write_text("# Plan\n")
            Path("THE_SPEC/requirements.md").write_text("# Requirements\n")
            
            result = post_work.invoke({"agent_name": "Workflow Spec Agent"})
            assert "✓ QC PASSED" in result
            print("✅ Test 7 passed: All files verified successfully")
            
            # Test 8: Directory check for Agent Spec Agent - empty
            os.makedirs("THE_CAST", exist_ok=True)
            result = post_work.invoke({"agent_name": "Agent Spec Agent"})
            assert "✗ QC FAILED" in result
            assert "empty" in result.lower()
            print("✅ Test 8 passed: Empty directory detected")
            
            # Test 9: Agent Spec Agent - file without required sections
            Path("THE_CAST/test_agent.md").write_text("# Test Agent\n\nSome content\n")
            result = post_work.invoke({"agent_name": "Agent Spec Agent"})
            assert "✗ QC FAILED" in result
            assert "Content validation failures" in result
            assert "System Prompt" in result or "Tools" in result
            print("✅ Test 9 passed: Missing sections detected in agent files")
            
            # Test 10: Agent Spec Agent - valid file with required sections
            Path("THE_CAST/test_agent.md").write_text("""# Test Agent

## System Prompt
You are a test agent.

## Tools
- tool1
- tool2
""")
            result = post_work.invoke({"agent_name": "Agent Spec Agent"})
            assert "✓ QC PASSED" in result
            print("✅ Test 10 passed: Valid agent file with required sections")
            
            # Test 11: Guardrail Agent - content validation
            with open("guardrail_assessment.md", "w") as f:
                f.write("# Guardrail Assessment\n\nMissing required sections\n")
            
            result = post_work.invoke({"agent_name": "Guardrail Agent"})
            assert "✗ QC FAILED" in result
            assert "Content validation failures" in result
            print("✅ Test 11 passed: Guardrail content validation works")
            
            # Test 12: Guardrail Agent - valid content
            with open("guardrail_assessment.md", "w") as f:
                f.write("""# Guardrail Assessment

## Overall Assessment
Status: Approved

## Contextual Guardrails
1. Guardrail 1
""")
            
            result = post_work.invoke({"agent_name": "Guardrail Agent"})
            assert "✓ QC PASSED" in result
            print("✅ Test 12 passed: Valid guardrail content passes")
            
            # Test 13: Invalid agent name
            result = post_work.invoke({"agent_name": "Invalid Agent"})
            assert "Error: Unknown agent name" in result
            print("✅ Test 13 passed: Invalid agent name handled correctly")
            
        finally:
            os.chdir(original_cwd)
    
    print("\n✅ All 13 post_work tool tests passed!")


if __name__ == "__main__":
    test_verify_deliverables_tool()
