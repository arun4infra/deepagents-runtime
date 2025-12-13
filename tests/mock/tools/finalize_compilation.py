from langchain_core.tools import tool
from langgraph.types import Command

@tool
def finalize_compilation(definition: dict) -> dict:
    """Finalizes compilation by returning a Command to update the definition state."""
    return Command(update={"definition": definition})