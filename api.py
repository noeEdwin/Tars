"""
FastAPI backend for Tars — exposes the LangGraph workflow over HTTP.
Run with: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import sys
import uuid
from pathlib import Path

# Path setup (mirrors main.py)
project_root = str(Path(__file__).resolve().parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "agents"))
sys.path.insert(0, os.path.join(project_root, "agents", "brain"))

from dotenv import load_dotenv
load_dotenv()

import base64
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.postgres import PostgresSaver

from openai import OpenAI
openai_client = OpenAI()

from agents.brain.nodes import workflow, config as base_config
from agents.RAG.save_memory import get_db_uri, save_long_term_memory
from dataBase.main_queries import get_user_id_from_username, get_roleplay_contexts, get_scene_from_filename, get_user_hsk_level
from dataBase.user_management import get_or_create_active_conversation
from ChatMessage.infraestructure.tts.google_tts import get_mixed_audio_bytes

# ─── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Tars API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # open during development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URI = get_db_uri()

# ─── Models ─────────────────────────────────────────────────────────────────
class StartSessionRequest(BaseModel):
    user_id: int = 1
    mode: str = "tars_normal"   # or "tars_roleplay"
    filename: str = None
    tars_role: str = None
    user_role: str = None
    scene: str = None

class StartSessionResponse(BaseModel):
    thread_id: str
    conversation_id: int
    tars_message: str
    audio_b64: str = None

class ChatRequest(BaseModel):
    user_id: int
    thread_id: str
    conversation_id: int
    user_input: str
    mode: str = "tars_normal"

class ChatResponse(BaseModel):
    tars_message: str
    audio_b64: str = None

# ─── Helpers ─────────────────────────────────────────────────────────────────
def _extract_tars_message(result: dict, start_len: int = 0) -> str:
    """Pull the final Tars text out of a workflow result."""
    messages = result.get("messages", [])
    new_msgs = messages[start_len:]
    for msg in reversed(new_msgs):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc["name"] in ("TarsResponse", "TarsChineseResponse"):
                    return tc["args"].get("message", "")
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            return msg.content
    return ""

@app.get("/roleplay/files")
def get_roleplay_files(user_id: int = 1):
    filenames = get_roleplay_contexts(user_id)
    return {"files": filenames}

@app.post("/start_session", response_model=StartSessionResponse)
def start_session(req: StartSessionRequest):
    """
    Initialise a session for a user.
    """
    if req.mode == "tars_roleplay":
        thread_id = f"{req.user_id}_roleplay_{uuid.uuid4().hex[:8]}"
    else:
        thread_id = f"{req.user_id}_normal"
        
    conversation_id = get_or_create_active_conversation(req.user_id, req.mode)

    cfg = {**base_config, "configurable": {"thread_id": thread_id}}

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        app_instance = workflow.compile(checkpointer=checkpointer)

        snapshot = app_instance.get_state(cfg)
        is_empty = not (snapshot.values and "messages" in snapshot.values)

        tars_message = ""
        if is_empty:
            if req.mode == "tars_roleplay":
                scene = req.scene or "A generic roleplay scenario."
                doc_id = None
                if req.filename:
                    res = get_scene_from_filename(req.user_id, req.filename)
                    if res:
                        doc_id, scene = res

                sys_msg_text = f"SYSTEM UPDATE: User has initiated a roleplay.\nSCENE: {scene}\nUSER ROLE: {req.user_role}\nTARS ROLE: {req.tars_role}\n\n PLEASE ADOPT THIS PERSONA IMMEDIATELY."
                
                init_state = {
                    "user_mode": "tars_roleplay",
                    "active_expert": "tars_roleplay",
                    "user_id": req.user_id,
                    "hsk_level": get_user_hsk_level(req.user_id),
                    "current_lesson": 1,
                    "scene_context": scene,
                    "user_role": req.user_role,
                    "selected_role": req.tars_role,
                    "selected_source": str(doc_id) if doc_id else None,
                    "messages": [HumanMessage(content=sys_msg_text)]
                }
            else:
                init_state = {
                    "user_mode": req.mode,
                    "active_expert": req.mode,
                    "user_id": req.user_id,
                    "hsk_level": get_user_hsk_level(req.user_id),
                    "current_lesson": 1,
                    "messages": [HumanMessage(
                        content=(
                            "SYSTEM UPDATE: A new Chinese learning session has started. "
                            "Introduce yourself briefly as the HSK Teacher. "
                            "DO NOT ask the user what they want to learn. "
                            "State what you are going to teach right now and directly ask them "
                            "a question or start an exercise to make them speak immediately."
                        )
                    )],
                }
            result = app_instance.invoke(init_state, config=cfg)
            tars_message = _extract_tars_message(result)
            if tars_message:
                save_long_term_memory(conversation_id, "assistant", tars_message)
        else:
            # Existing session — send a re-entry prompt
            snapshot = app_instance.get_state(cfg)
            last_msgs = snapshot.values.get("messages", [])
            # Check if last message was interrupted (has pending tool calls)
            if last_msgs:
                last = last_msgs[-1]
                if hasattr(last, "tool_calls") and last.tool_calls:
                    tool_recovery = [
                        ToolMessage(
                            content="System: session resumed.",
                            tool_call_id=tc["id"]
                        )
                        for tc in last.tool_calls
                    ]
                    app_instance.update_state(cfg, {"messages": tool_recovery})
            tars_message = "¡Bienvenido de vuelta! Continuemos donde nos quedamos."

    audio_b64 = None
    if tars_message:
        audio_bytes = get_mixed_audio_bytes(tars_message)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

    return StartSessionResponse(
        thread_id=thread_id,
        conversation_id=conversation_id,
        tars_message=tars_message,
        audio_b64=audio_b64
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a user message and get Tars' response."""
    cfg = {**base_config, "configurable": {"thread_id": req.thread_id}}

    save_long_term_memory(req.conversation_id, "user", req.user_input)

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        app_instance = workflow.compile(checkpointer=checkpointer)

        snapshot = app_instance.get_state(cfg)
        existing = snapshot.values.get("messages", []) if snapshot.values else []
        start_len = len(existing)

        state_update = {
            "user_mode": req.mode,
            "active_expert": req.mode,
            "user_id": req.user_id,
            "hsk_level": get_user_hsk_level(req.user_id),
            "current_lesson": 1,
            "messages": [HumanMessage(content=req.user_input)],
        }

        result = app_instance.invoke(state_update, config=cfg)
        tars_message = _extract_tars_message(result, start_len)

    if not tars_message:
        raise HTTPException(status_code=500, detail="No response from Tars")

    save_long_term_memory(req.conversation_id, "assistant", tars_message)
    
    audio_b64 = None
    audio_bytes = get_mixed_audio_bytes(tars_message)
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

    return ChatResponse(tars_message=tars_message, audio_b64=audio_b64)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/stt")
async def stt_endpoint(audio: UploadFile = File(...)):
    """Accepts an audio file and transcribes it using OpenAI Whisper to auto-detect the language."""
    try:
        audio_bytes = await audio.read()
        # OpenAI expects a tuple with (filename, bytes) or a file-like object
        # The filename extension helps Whisper understand the audio format (e.g., webm from browsers)
        file_tuple = (audio.filename or "audio.webm", audio_bytes)
        
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1", 
            file=file_tuple,
            prompt="这是一段简体中文对话，请使用简体中文输出。"
        )
        return {"text": transcription.text.strip()}
    except Exception as e:
        print(f"Error in backend STT: {e}")
        raise HTTPException(status_code=500, detail=str(e))
