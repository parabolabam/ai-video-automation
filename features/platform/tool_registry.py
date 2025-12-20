from typing import Callable, Dict, Any

# Import tools from the science domain
from features.agents.science_agents.tools import (
    web_search,
    science_news_search,
    fact_check,
)
from features.agents.science_agents.scene_planner import submit_scene_plan

# Define the type for the registry dictionary
ToolRegistryType = Dict[str, Callable[..., Any]]

# The central registry mapping string IDs to functions
# This allows the dynamic runner to load tools based on the 'tools' array in the 'agents' table.
TOOL_REGISTRY: ToolRegistryType = {
    # Research Tools
    "web_search": web_search,
    "science_news_search": science_news_search,
    
    # Validation Tools
    "fact_check": fact_check,
    
    # Scene Planning Tools
    "submit_scene_plan": submit_scene_plan,
}

def get_tool_by_id(tool_id: str) -> Callable[..., Any]:
    """Retrieve a tool function by its string ID.
    
    Args:
        tool_id: The unique identifier string for the tool.
        
    Returns:
        The tool function.
        
    Raises:
        ValueError: If the tool_id is not found in the registry.
    """
    if tool_id not in TOOL_REGISTRY:
        raise ValueError(f"Tool with ID '{tool_id}' not found in registry.")
    return TOOL_REGISTRY[tool_id]
