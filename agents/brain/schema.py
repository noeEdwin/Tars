from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from enum import Enum
from typing import List, Optional, Dict, Annotated

class FileAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"
    LIST = "list"
    READ = "read"
    CREATE_DIRECTORY = "create_directory"

class FileMode(str, Enum):
    APPEND = "append"
    OVERWRITE = "overwrite"
    
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
    content: Optional[str] = Field(None, description="The content to write. If mode='append', this is added to the end. If mode='overwrite', this replaces lines in the file or the file itself.")
    destination_path: Optional[str] = Field(None, description="The target path (for MOVE).")
    reason: str = Field(description="A brief explanation of why this action is being taken.")
    mode: FileMode = Field(
        default=FileMode.APPEND, 
        description="Crucial for UPDATE: 'append' to add new lines, 'overwrite' to replace some lines or the entire file."
    )
