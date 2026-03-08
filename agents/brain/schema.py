from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from enum import Enum
from typing import List, Optional, Dict, Annotated

class TarsState(TypedDict):
    # 1. History: The conversation between you and TARS
    messages: Annotated[List[BaseMessage], add_messages]

    
    # 4. Memory: Files TARS has "seen" or read in this session
    working_context: List[Dict[str, str]] 
    
    is_complete: bool
    active_expert: str
    
    # 6. Explicit Mode: User-selected mode (e.g., "engineer", "roleplay", "coder")
    user_mode: Optional[str]
    
    # 7. Roleplay Spec: Specific persona for Roleplay mode
    selected_role: Optional[str]
    scene_context: Optional[str]
    user_role: Optional[str]
    selected_source: Optional[str] # Or doc_id, useful for fetching DB personas
    
    # User Identification for Memory Isolation
    user_id: Optional[int]