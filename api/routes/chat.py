"""Chat routes: session start, WebSocket streaming, and Tars response handling."""
import asyncio
import base64
import logging
import re
import time
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agents.brain.nodes import workflow, config as base_config
from agents.RAG.save_memory import save_long_term_memory
from agents.RAG.utils import clear_turn_cache, get_embedding
from agents.dataBase.main_queries import get_user_hsk_level, get_scene_from_filename
from agents.dataBase.conversations import get_or_create_active_conversation
from auth.security import get_current_user
from ChatMessage.infraestructure.tts.google_tts import get_mixed_audio_bytes
from api.models import StartSessionRequest, StartSessionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared state — populated by app lifespan
app_state: dict = {}
active_tasks: dict = {}


@router.post("/start_session", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest, current_user_id: int = Depends(get_current_user)):
    """Initialise a session for a user."""
    if req.mode == "tars_roleplay":
        thread_id = f"{current_user_id}_roleplay_{uuid.uuid4().hex[:8]}"
    else:
        thread_id = f"{current_user_id}_normal"

    conversation_id = get_or_create_active_conversation(current_user_id, req.mode)

    cfg = {**base_config, "configurable": {"thread_id": thread_id}}
    app_instance = app_state["app_instance"]
    snapshot = await app_instance.aget_state(cfg)
    is_empty = not (snapshot.values and "messages" in snapshot.values)

    tars_message = ""
    if is_empty:
        if req.mode == "tars_roleplay":
            scene = req.scene or "A generic roleplay scenario."
            doc_id = None
            if req.filename:
                res = get_scene_from_filename(current_user_id, req.filename)
                if res:
                    doc_id, scene = res

            sys_msg_text = (
                f"SYSTEM UPDATE: User has initiated a roleplay.\n"
                f"SCENE: {scene}\nUSER ROLE: {req.user_role}\nTARS ROLE: {req.tars_role}\n\n"
                f"ADOPT THIS PERSONA IMMEDIATELY."
            )

            init_state = {
                "user_mode": "tars_roleplay",
                "active_expert": "tars_roleplay",
                "user_id": current_user_id,
                "hsk_level": get_user_hsk_level(current_user_id),
                "current_lesson": 1,
                "scene_context": scene,
                "user_role": req.user_role,
                "selected_role": req.tars_role,
                "selected_source": str(doc_id) if doc_id else None,
                "messages": [HumanMessage(content=sys_msg_text)],
            }
        else:
            init_state = {
                "user_mode": req.mode,
                "active_expert": req.mode,
                "user_id": current_user_id,
                "hsk_level": get_user_hsk_level(current_user_id),
                "current_lesson": 1,
                "awaiting_answer": False,
                "messages": [HumanMessage(
                    content=(
                        "SYSTEM UPDATE: A new Chinese learning session has started. "
                        "Start the lesson immediately — introduce the first word."
                    )
                )],
            }
        await app_instance.aupdate_state(cfg, init_state)
        tars_message = ""

    else:
        last_msgs = snapshot.values.get("messages", [])
        if last_msgs:
            last = last_msgs[-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                tool_recovery = [
                    ToolMessage(content="System: session resumed.", tool_call_id=tc["id"])
                    for tc in last.tool_calls
                ]
                await app_instance.aupdate_state(cfg, {"messages": tool_recovery})

        if req.mode == "tars_normal":
            saved_progress = snapshot.values.get("lesson_progress", 0)
            saved_target = snapshot.values.get("target_word")
            saved_words = snapshot.values.get("lesson_words")
            saved_awaiting = snapshot.values.get("awaiting_answer", False)

            if saved_progress > 0 and saved_target:
                resume_msg = (
                    f"SYSTEM: The user has returned. "
                    f"Saved progress: {saved_progress} words completed. "
                    f"Current word: {saved_target}. "
                    f"Resume the lesson where you left off — do NOT start from scratch."
                )
            else:
                resume_msg = "SYSTEM: New lesson session. Present the first word."

            await app_instance.aupdate_state(cfg, {
                "user_mode": "tars_normal",
                "lesson_words": saved_words,
                "lesson_progress": saved_progress,
                "target_word": saved_target,
                "awaiting_answer": saved_awaiting,
                "messages": [HumanMessage(content=resume_msg)],
            })
            tars_message = ""
        else:
            tars_message = "¡Bienvenido de vuelta! Continuemos donde nos quedamos."

    if tars_message:
        await asyncio.to_thread(save_long_term_memory, conversation_id, "assistant", tars_message)

    audio_b64 = None
    if tars_message:
        audio_bytes = await get_mixed_audio_bytes(tars_message)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return StartSessionResponse(
        thread_id=thread_id,
        conversation_id=conversation_id,
        tars_message=tars_message,
        audio_b64=audio_b64,
    )


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "interrupt":
                if user_id in active_tasks:
                    active_tasks[user_id].cancel()
                continue

            if msg_type == "init_session":
                logger.info(f"WebSocket vinculado silenciosamente para el usuario {user_id}")
                continue

            if msg_type == "chat":
                user_input = data.get("text")
                thread_id = data.get("thread_id")
                conv_id = data.get("conversation_id")
                mode = data.get("mode", "tars_roleplay")

                if not user_input or str(user_input).strip() == "":
                    logger.warning("Mensaje de chat vacío recibido y descartado.")
                    continue

                if user_id in active_tasks and not active_tasks[user_id].done():
                    active_tasks[user_id].cancel()

                task = asyncio.create_task(
                    handle_tars_response(websocket, user_id, user_input, thread_id, conv_id, mode)
                )
                active_tasks[user_id] = task
    except WebSocketDisconnect:
        if user_id in active_tasks:
            active_tasks[user_id].cancel()


async def handle_tars_response(websocket, user_id, user_input, thread_id, conv_id, mode="tars_normal"):
    cfg = {**base_config, "configurable": {"thread_id": thread_id}}
    full_response_content = ""
    sentence_buffer = ""
    app_instance = app_state["app_instance"]
    clear_turn_cache()

    try:
        audio_queue = asyncio.Queue()

        async def audio_worker():
            while True:
                text_chunk = await audio_queue.get()
                if text_chunk is None:
                    break
                try:
                    audio_bytes = await get_mixed_audio_bytes(text_chunk)
                    if audio_bytes:
                        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                        await websocket.send_json({"type": "audio_chunk", "audio_b64": audio_b64})
                except Exception as e:
                    logger.error("Error in TTS: %s", e)
                finally:
                    audio_queue.task_done()

        worker_task = asyncio.create_task(audio_worker())

        if mode == "tars_roleplay":
            input_data = {"messages": [HumanMessage(content=user_input)]}
        else:
            if user_input:
                user_embedding = get_embedding(user_input)
                asyncio.create_task(
                    asyncio.to_thread(save_long_term_memory, conv_id, "user", user_input, user_embedding)
                )
                input_data = {
                    "user_mode": mode,
                    "active_expert": mode,
                    "user_id": user_id,
                    "hsk_level": get_user_hsk_level(user_id),
                    "messages": [HumanMessage(content=user_input)],
                }
            else:
                input_data = None

        is_json_filtered = False
        first_tokens_buffer = ""

        async for event in app_instance.astream_events(input_data, cfg, version="v2"):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                if token:
                    if mode == "tars_roleplay" and not is_json_filtered:
                        first_tokens_buffer += token
                        if not first_tokens_buffer.lstrip().startswith("{"):
                            is_json_filtered = True
                            await websocket.send_json({"type": "token", "text": first_tokens_buffer})
                            full_response_content += first_tokens_buffer
                        elif "}" in first_tokens_buffer:
                            is_json_filtered = True
                            clean_text = first_tokens_buffer.split("}", 1)[1].lstrip(" \n-_")
                            if clean_text:
                                await websocket.send_json({"type": "token", "text": clean_text})
                                full_response_content += clean_text
                    else:
                        full_response_content += token
                        sentence_buffer += token
                        await websocket.send_json({"type": "token", "text": token})

                        if re.search(r"[。！？.!?]", token):
                            text_to_process = sentence_buffer.strip()
                            sentence_buffer = ""
                            if text_to_process:
                                audio_queue.put_nowait(text_to_process)

            if mode == "tars_roleplay":
                if event["event"] == "on_chat_model_end" and len(full_response_content.strip()) > 0:
                    logger.debug("LLM finished speaking. Releasing interface.")
                    break

        if sentence_buffer.strip():
            audio_queue.put_nowait(sentence_buffer.strip())
        audio_queue.put_nowait(None)

        if mode == "tars_roleplay":
            logger.debug("Releasing Roleplay interface.")
        else:
            await worker_task

        await websocket.send_json({"type": "tars_answer_end", "text": full_response_content})
        asyncio.create_task(
            asyncio.to_thread(save_long_term_memory, conv_id, "assistant", full_response_content)
        )

    except asyncio.CancelledError:
        await websocket.send_json({"type": "status", "message": "Interrupted by user."})
    except Exception as e:
        logger.error("Error in Tars Response: %s", e)
        await websocket.send_json({"type": "error", "message": str(e)})
