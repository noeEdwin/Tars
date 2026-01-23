from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from enum import Enum

class FileAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"

class TarsState(TypedDict):
    # 1. History: The conversation between you and TARS
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 2. Vision: Your system map 
    system_map: Dict[str, List[str]]
    
    # 3. Location: The path TARS is currently focused on
    current_path: str
    
    # 4. Memory: Files TARS has "seen" or read in this session
    working_context: List[Dict[str, str]] 
    
    # 5. Intent: The plan TARS has decided to follow
    next_steps: List[str]
    is_complete: bool


class TarsResponse(BaseModel):
    """The schema for TARS's informative responses."""
    found: bool = Field(description="True if the requested folder/file was located.")
    message: str = Field(description="The natural language explanation for the user.")
    identified_paths: List[str] = Field(default=[], description="List of paths from the system map relevant to the query.")
    next_suggestion: Optional[str] = Field(None, description="A suggestion for the next logical step (e.g., 'Should I list the files in this folder?')")

class TarsAction(BaseModel):
    """Schema for TARS to modify the filesystem."""
    action_type: FileAction = Field(description="The specific type of filesystem operation.")
    source_path: str = Field(description="The full path of the file to be acted upon.")
    content: Optional[str] = Field(None, description="The new content (for CREATE or UPDATE).")
    destination_path: Optional[str] = Field(None, description="The target path (for MOVE).")
    reason: str = Field(description="A brief explanation of why this action is being taken.")
