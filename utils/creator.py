from typing import Dict, Any
from supabase import Client


def get_creator_by_id(supabase: Client, creator_id: str) -> Dict[str, Any]:
    """
    Helper function to get creator details by ID.
    
    Args:
        supabase: Supabase client instance
        creator_id: The creator ID to fetch
        
    Returns:
        Creator data dictionary
        
    Raises:
        ValueError: If creator not found
    """
    creator_response = supabase.table("creator").select("*").eq("id", creator_id).execute()
    if not creator_response.data:
        raise ValueError("Creator not found")
    return creator_response.data[0]