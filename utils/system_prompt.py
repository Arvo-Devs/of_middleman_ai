
from typing import Dict, Any
from supabase import Client

def get_system_prompt_by_id(supabase: Client, system_prompt_id: str) -> Dict[str, Any]:
    """
    Helper function to get system prompt details by ID.
    
    Args:
        system_prompt_id: The system prompt ID to fetch
        
    Returns:
        System prompt data dictionary
        
    Raises:
        ValueError: If system prompt not found
    """
    system_prompt_response = supabase.table("system_prompt").select("*").eq("id", system_prompt_id).execute()
    if not system_prompt_response.data:
        raise ValueError("System prompt not found")
    return system_prompt_response.data[0]