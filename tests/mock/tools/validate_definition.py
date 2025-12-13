"""
Validate Definition Tool - Validates workflow definitions against the master schema.

The schema and example are injected at load time from:
- tests/mock/schema.json (authoritative schema)
- tests/mock/schema_example.json (valid example)

Placeholders __SCHEMA_JSON__ and __SCHEMA_EXAMPLE_JSON__ are replaced by
load_definition_with_files() in test_helpers.py before this script is executed.
"""
import json
from jsonschema import validate, ValidationError
from langchain_core.tools import tool
from langgraph.types import Command
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage


# These placeholders are replaced at load time by load_definition_with_files()
# DO NOT modify these lines - they are pattern-matched for replacement
AUTHORITATIVE_SCHEMA = __SCHEMA_JSON__
SCHEMA_EXAMPLE = __SCHEMA_EXAMPLE_JSON__


@tool
def validate_definition(workflow_definition: dict = None, runtime: ToolRuntime = None) -> str:
    """Validates a definition.json object against the master schema.
    
    Args:
        workflow_definition: A dictionary containing the complete workflow definition with:
            - name: string (workflow name)
            - version: string (version number)
            - tool_definitions: array (can be empty [])
            - nodes: array of node objects with id, type, and config
            - edges: array of edge objects with source, target, and type
    
    Returns:
        "Validation successful." if valid, or an error message with guidance.
    """
    # Handle missing or empty workflow_definition
    if workflow_definition is None or workflow_definition == {}:
        return f'''Error: workflow_definition parameter is required but was not provided.

You must pass a complete workflow definition object to this tool. 

EXAMPLE:
{SCHEMA_EXAMPLE}

Please construct your definition.json object and pass it as the workflow_definition parameter.'''

    try:
        validate(instance=workflow_definition, schema=AUTHORITATIVE_SCHEMA)
        tool_call_id = runtime.tool_call_id if runtime else "unknown"
        return Command(
            update={
                "definition": workflow_definition,
                "messages": [ToolMessage(content="Validation successful.", tool_call_id=tool_call_id)]
            }
        )
    except ValidationError as e:
        error_path = ' -> '.join(str(p) for p in e.path) if e.path else 'root'
        
        return f'''Validation Error at path: {error_path}
Message: {e.message}

REQUIRED SCHEMA STRUCTURE:
{json.dumps(AUTHORITATIVE_SCHEMA, indent=2)}

VALID EXAMPLE:
{SCHEMA_EXAMPLE}

Please fix the error and try again.'''
