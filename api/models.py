"""Pydantic request/response models for the chat and session endpoints."""
from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    mode: str = "tars_normal"
    filename: str | None = None
    tars_role: str | None = None
    user_role: str | None = None
    scene: str | None = None


class StartSessionResponse(BaseModel):
    thread_id: str
    conversation_id: int
    tars_message: str
    audio_b64: str | None = None


class ChatRequest(BaseModel):
    user_id: int
    thread_id: str
    conversation_id: int
    user_input: str
    mode: str = "tars_normal"


class ChatResponse(BaseModel):
    tars_message: str
    audio_b64: str | None = None
