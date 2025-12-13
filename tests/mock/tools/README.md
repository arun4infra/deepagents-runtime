# Agent Tool Scripts

This directory contains Python scripts for each tool in the test definition.

## Purpose

Tool scripts are stored in separate `.py` files for:
- **Better readability**: Proper Python syntax highlighting
- **Easier debugging**: Can view/edit/test tools independently
- **Version control**: Cleaner diffs when tools change
- **IDE support**: Full Python IDE features (linting, autocomplete, etc.)

## File Naming Convention

Each file is named after the tool's `name` field from `definition.json`:
- `generate_diff.py` → Diff generation tool
- `propose_changes.py` → Change proposal tool
- `validate_definition.py` → Definition validation tool
- `finalize_compilation.py` → Compilation finalization tool

## How It Works

1. `definition.json` contains placeholder: `"script": "loaded from tools/name.py file"`
2. Test helper `load_definition_with_files()` reads the JSON
3. For each tool with placeholder, it loads content from `{tool_name}.py`
4. Returns complete definition with tool scripts loaded

## Usage in Tests

```python
from tests.integration.test_helpers import load_definition_with_files

definition = load_definition_with_files(Path("tests/mock/definition.json"))
# definition now has all tool scripts loaded from .py files
```

## Tool Structure

Each tool file should:
- Import required dependencies
- Use `@tool` decorator from `langchain_core.tools`
- Define the tool function with proper type hints
- Include docstring describing the tool's purpose

## Note

This is **only for test definitions**. Production definitions should continue using inline scripts or their own loading mechanism.
