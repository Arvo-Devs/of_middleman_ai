from typing import Dict, Any
from supabase import Client


def get_fan_by_id(supabase: Client,fan_id: str) -> Dict[str, Any]:
    """
    Helper function to get fan details by ID.
    
    Args:
        fan_id: The fan ID to fetch
        
    Returns:
        Fan data dictionary
        
    Raises:
        ValueError: If fan not found
    """
    fan_response = supabase.table("fan").select("*").eq("id", fan_id).execute()
    if not fan_response.data:
        raise ValueError("Fan not found")
    return fan_response.data[0]