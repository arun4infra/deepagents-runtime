import difflib
from langchain_core.tools import tool

@tool
def generate_diff(original: str, new: str) -> str:
    """Generate unified diff between original and new content."""
    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile='original',
        tofile='new',
        lineterm=''
    )
    return ''.join(diff_lines)