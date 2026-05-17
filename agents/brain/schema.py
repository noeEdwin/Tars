from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TarsState(BaseModel):
    """LangGraph state schema for the Tars AI agent."""

    # Core fields — required at session creation
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    user_id: int
    active_expert: str
    user_mode: str

    # Memory: files TARS has "seen" or read in this session
    working_context: List[Dict[str, str]] = Field(default_factory=list)

    # Graph control
    is_complete: bool = False

    # Roleplay spec
    selected_role: Optional[str] = None
    scene_context: Optional[str] = None
    user_role: Optional[str] = None
    selected_source: Optional[str] = None

    # Educational context
    current_lesson: int = Field(default=1, ge=1)
    hsk_level: int = Field(default=1, ge=1, le=6)
    lesson_progress: int = Field(default=0, ge=0)
    target_word: Optional[str] = None
    lesson_words: List[str] = Field(default_factory=list)
    awaiting_answer: bool = False
