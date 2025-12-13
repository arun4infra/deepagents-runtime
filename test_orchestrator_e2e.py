"""
End-to-end test for orchestrator with pre_work and post_work tools.
"""
import sys
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent / "tests"
sys.path.insert(0, str(tests_dir))

from integration.test_helpers import load_definition_with_files
from core.builder import GraphBuilder


def test_orchestrator_tools():
    """Test that orchestrator can use pre_work and post_work tools."""
    # Load test definition
    definition_path = Path(__file__).parent / "tests" / "mock" / "definition.json"
    definition = load_definition_with_files(definition_path)
    
    # Build agent
    builder = GraphBuilder()
    agent = builder.build_from_definition(definition)
    
    # Test input
    test_input = {
        "messages": [{
            "role": "user",
            "content": "Create a simple hello world feature"
        }]
    }
    
    print("\n" + "="*80)
    print("TESTING ORCHESTRATOR WITH PRE_WORK AND POST_WORK TOOLS")
    print("="*80 + "\n")
    
    # Run agent
    result = agent.invoke(test_input)
    
    # Check results
    print("\n" + "="*80)
    print("AGENT EXECUTION COMPLETED")
    print("="*80 + "\n")
    
    # Print messages
    for i, msg in enumerate(result.get("messages", [])):
        print(f"\n--- Message {i+1} ({msg.__class__.__name__}) ---")
        if hasattr(msg, "content"):
            content = msg.content
            if isinstance(content, str):
                print(content[:500] + ("..." if len(content) > 500 else ""))
            else:
                print(content)
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"\nTool Calls: {len(msg.tool_calls)}")
            for tc in msg.tool_calls[:3]:  # Show first 3
                print(f"  - {tc.get('name', 'unknown')}")
    
    # Print files created
    files = result.get("files", {})
    print(f"\n\n--- Files Created ({len(files)}) ---")
    for file_path in sorted(files.keys())[:10]:  # Show first 10
        print(f"  - {file_path}")
    
    # Check if pre_work was called
    messages_str = str(result.get("messages", []))
    pre_work_called = "pre_work" in messages_str
    post_work_called = "post_work" in messages_str
    
    print(f"\n\n--- Tool Usage ---")
    print(f"pre_work called: {pre_work_called}")
    print(f"post_work called: {post_work_called}")
    
    if pre_work_called:
        print("\n✓ SUCCESS: Orchestrator is using pre_work tool!")
    else:
        print("\n✗ ISSUE: Orchestrator did not call pre_work tool")
    
    if post_work_called:
        print("✓ SUCCESS: Orchestrator is using post_work tool!")
    else:
        print("✗ ISSUE: Orchestrator did not call post_work tool")
    
    return result


if __name__ == "__main__":
    test_orchestrator_tools()
