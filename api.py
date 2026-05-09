"""
FastAPI backend for Tars — exposes the LangGraph workflow over HTTP.
Run with: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import sys
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

# Path setup (mirrors main.py)
project_root = str(Path(__file__).resolve().parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "agents"))
sys.path.insert(0, os.path.join(project_root, "agents", "brain"))

from dotenv import load_dotenv
load_dotenv()

import base64
from fastapi import FastAPI, HTTPException, UploadFile, File, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from openai import OpenAI
openai_client = OpenAI()

from agents.brain.nodes import workflow, config as base_config
from agents.RAG.save_memory import get_db_uri, save_long_term_memory
from dataBase.main_queries import get_user_id_from_username, get_roleplay_contexts, get_scene_from_filename, get_user_hsk_level, get_user_profile
from dataBase.user_management import get_or_create_active_conversation
from dataBase.auth_queries import get_user_by_username, get_user_by_email, get_user_by_username_simple, create_user, get_user_by_id, update_user_profile
from auth.security import hash_password, verify_password, create_access_token, get_current_user
from auth.schemas import RegisterRequest, RegisterResponse, LoginRequest, TokenResponse, UserProfile, ProfileUpdateRequest
from ChatMessage.infraestructure.tts.google_tts import get_mixed_audio_bytes


# ─── App ────────────────────────────────────────────────────────────────────
app_state = {}
DB_URI = get_db_uri()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Lógica de INICIO ---
    # Context manager of AsyncPostgresSaver yields the checkpointer instance
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        
        # Lo guardamos para que esté accesible en toda la app
        app_state["checkpointer"] = checkpointer
        app_state["app_instance"] = workflow.compile(checkpointer=checkpointer)
        yield

app = FastAPI(title="Tars API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:5173",
        "https://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_tasks = {}

# ─── Models ─────────────────────────────────────────────────────────────────
class StartSessionRequest(BaseModel):
    user_id: int = 1
    mode: str = "tars_normal"   # or "tars_roleplay"
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
async def start_session(req: StartSessionRequest):
    """
    Initialise a session for a user.
    """
    if req.mode == "tars_roleplay":
        thread_id = f"{req.user_id}_roleplay_{uuid.uuid4().hex[:8]}"
    else:
        thread_id = f"{req.user_id}_normal"
        
    conversation_id = get_or_create_active_conversation(req.user_id, req.mode)

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
                "awaiting_answer": False,  # lesson_prompt_node will set True after first word
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
        # Existing session — resume appropriately per mode
        last_msgs = snapshot.values.get("messages", [])
        # Recover from interrupted tool calls
        if last_msgs:
            last = last_msgs[-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                tool_recovery = [
                    ToolMessage(content="System: session resumed.", tool_call_id=tc["id"])
                    for tc in last.tool_calls
                ]
                await app_instance.aupdate_state(cfg, {"messages": tool_recovery})

        if req.mode == "tars_normal":
            # Reseteo de estado para lección fresca
            await app_instance.aupdate_state(cfg, {
                "lesson_words":    None,
                "lesson_progress": 0,
                "target_word":     None,
                "awaiting_answer": False,
            })
            await app_instance.aupdate_state(cfg, {
                "user_mode": "tars_normal",
                "messages": [HumanMessage(content="SYSTEM: Nueva sesión de lección. Presenta la primera palabra.")]
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
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

    return StartSessionResponse(
        thread_id=thread_id,
        conversation_id=conversation_id,
        tars_message=tars_message,
        audio_b64=audio_b64
    )

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "interrupt":
                if user_id in active_tasks:
                    active_tasks[user_id].cancel()
                continue

            if data.get("type") in ["chat", "init_session"]:
                user_input = data.get("text")
                thread_id = data.get("thread_id")
                conv_id = data.get("conversation_id")

                if user_id in active_tasks and not active_tasks[user_id].done():
                    active_tasks[user_id].cancel()

                task = asyncio.create_task(
                    handle_tars_response(websocket, user_id, user_input, thread_id, conv_id)
                )
                active_tasks[user_id] = task
    except WebSocketDisconnect:
        if user_id in active_tasks:
            active_tasks[user_id].cancel()    

async def handle_tars_response(websocket, user_id, user_input, thread_id, conv_id, mode="tars_normal"):
    """
    Procesa la respuesta de Tars, genera audio y envía por el socket.
    Esta función es cancelable si el usuario interrumpe.
    """
    import time
    import re
    t_start = time.time()
    print(f"[TIMER WS] 1. Llegó mensaje / inicio handler: 0.00s")
    cfg = {**base_config, "configurable": {"thread_id": thread_id}}
    full_response_content = ""
    sentence_buffer = ""
    app_instance = app_state["app_instance"]
    try:
        audio_queue = asyncio.Queue()
        
        async def audio_worker():
            while True:
                text_chunk = await audio_queue.get()
                if text_chunk is None:
                    break
                try:
                    # Generamos el audio de la frase secuencialmente pero en paralelo a la recepción de texto
                    audio_bytes = await get_mixed_audio_bytes(text_chunk)
                    if audio_bytes:
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio_chunk",
                            "audio_b64": audio_b64
                        })
                except Exception as e:
                    print(f"Error procesando chunk de audio: {e}")
                finally:
                    audio_queue.task_done()
                    
        worker_task = asyncio.create_task(audio_worker())

        if user_input:
            # 1. Fire-and-forget: we do NOT await this. It saves in the background!
            asyncio.create_task(asyncio.to_thread(save_long_term_memory, conv_id, "user", user_input))
            
            input_data = {
                "user_mode": mode,
                "active_expert": mode,
                "user_id": user_id,
                "hsk_level": get_user_hsk_level(user_id),
                "messages": [HumanMessage(content=user_input)],
            }
        else:
            input_data = None
            
        print(f"[TIMER WS] 3. Listo para astream_events: {time.time() - t_start:.2f}s")
        
        async for event in app_instance.astream_events(input_data, cfg, version="v2"):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                if token:
                    print(f"DEBUG: Token recibido -> {token}")
                    full_response_content += token
                    sentence_buffer += token
                    # 1. Enviamos el token al texto (UI)
                    await websocket.send_json({"type": "token", "text": token})
                    # 2. ¿Es el fin de una frase? (Detectar . ! ? 。 ！ ？)
                    if re.search(r'[。！？.!?]', token):
                        # Detectamos fin de frase. Añadimos a la cola de TTS
                        text_to_process = sentence_buffer.strip()
                        sentence_buffer = "" # Limpiamos el buffer para la siguiente frase
                        if text_to_process:
                            audio_queue.put_nowait(text_to_process)
        print("DEBUG: Fin de streaming de texto")

        print(f"[TIMER WS] 5. Todos los tokens procesados (fin LangGraph): {time.time() - t_start:.2f}s")
        # 3. Procesar cualquier residuo que haya quedado en el buffer al final
        if sentence_buffer.strip():
            audio_queue.put_nowait(sentence_buffer.strip())

        # 4. Cerramos la cola y esperamos a que envíe todo antes de cerrar
        audio_queue.put_nowait(None)
        await worker_task

        # 5. Mensaje de cierre 
        await websocket.send_json({"type": "tars_answer_end", "text": full_response_content})
        
        # Guardar en memoria (sin bloquear)
        asyncio.create_task(asyncio.to_thread(save_long_term_memory, conv_id, "assistant", full_response_content))
        
    except asyncio.CancelledError:
        # Aquí es donde ocurre la magia: si task.cancel() se llama, el código salta aquí.
        await websocket.send_json({"type": "status", "message": "Interrumpido por el usuario."})
    except Exception as e:
        print(f"Error en Tars Response: {e}")
        await websocket.send_json({"type": "error", "message": "Ocurrió un error interno."})

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/greeting")
async def get_greeting(user_id: int = 1):
    """
    Returns a short, personalised greeting from TARS based on the
    user's name, HSK level, and interest area stored in the DB.
    Uses GPT-4o-mini for speed (< 1 s round-trip).
    """
    profile = await asyncio.to_thread(get_user_profile, user_id)

    username    = profile["username"]
    hsk_level   = profile["hsk_level"]
    interest    = profile["interest_area"]

    prompt = (
        f"You are TARS, a witty, warm AI tutor for Chinese. "
        f"Generate ONE short greeting (1-2 sentences, ≤ 20 words) for a returning user. "
        f"Use their personal details to make it feel special and unique. "
        f"Details: name='{username}', HSK level={hsk_level}, interest/fandom='{interest}'. "
        f"Be creative and playful — reference their interest with a fun nickname or title. "
        f"Examples: 'Welcome back, my Cosmere traveller! Ready to conquer more characters?', "
        f"'Greetings, young Padawan {username} — the Force of Mandarin awaits you today!'. "
        f"Output ONLY the greeting sentence, nothing else."
        f"The greeting must be ON CHINESE, but adjust it to the HSK LEVEL={hsk_level}"
    )

    response = await asyncio.to_thread(
        lambda: openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.9,
        )
    )
    greeting = response.choices[0].message.content.strip()
    return {"greeting": greeting, "username": username}


# ── Emotion style map (mirrors node_learning.py) ────────────────────────────
EMOTION_MAP = {
    "RETRY":           "directo",
    "CORRECT_NEXT":    "motivacional",
    "LESSON_COMPLETE": "exclamativo",
    "INTRODUCE":       "neutro",
    "DEFAULT":         "neutro",
}

@app.get("/preload_message")
async def get_preload_message(user_id: int = 1):
    """
    Fast personalised TARS greeting for Normal Mode.
    Returns: { text, audio_b64 }
    - Profile + files fetched in parallel (2 DB queries)
    - GPT-4o-mini: max_tokens=55 → ~0.5s
    - TTS runs in parallel with LLM response processing → adds ~1s
    Total target: < 3s
    """
    # ── Parallel DB reads ─────────────────────────────────────────────────────
    profile, uploaded_files = await asyncio.gather(
        asyncio.to_thread(get_user_profile, user_id),
        asyncio.to_thread(get_roleplay_contexts, user_id),
    )

    username  = profile["username"]
    hsk_level = profile["hsk_level"]
    interest  = profile["interest_area"]
    files_tip = f"Tiene escenarios: {', '.join(uploaded_files[:2])}." if uploaded_files else ""

    prompt = (
        f"Eres TARS. Saluda a {username} (HSK{hsk_level}, fandom: {interest}) "
        f"en UNA oración breve. {files_tip} "
        f"Dale un apodo basado en su fandom. Incluye 一个汉字 (pīnyīn). "
        f"Solo el mensaje, sin explicaciones."
    )

    # ── LLM call ─────────────────────────────────────────────────────────────
    llm_response = await asyncio.to_thread(
        lambda: openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=55,
            temperature=0.9,
        )
    )
    text = llm_response.choices[0].message.content.strip()

    # ── TTS: generate audio for the short greeting ────────────────────────────
    audio_b64 = None
    try:
        audio_bytes = await get_mixed_audio_bytes(text)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"[preload_message] TTS skipped: {e}")

    return {"text": text, "audio_b64": audio_b64}




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
            prompt="这是一段简体中文和西班牙语的双语对话。请使用简体中文和西班牙语输出。"
        )
        text = transcription.text.strip()
        print(f"STT Output: {text}, size: {len(audio_bytes)}")

        # Filter known Whisper hallucinations (prompt echo on silent audio)
        WHISPER_HALLUCINATIONS = {
            "请使用简体中文输出。",
            "这是一段简体中文对话，请使用简体中文输出。",
            "这是一段简体中文和西班牙语的双语对话。请使用简体中文和西班牙语输出。",
            "字幕by索兰娅",
        }
        if text in WHISPER_HALLUCINATIONS or len(text) < 2:
            return {"text": ""}

        return {"text": text}
    except Exception as e:
        print(f"Error in backend STT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """
    Registra un nuevo usuario en Tars.

    Flujo:
    1. Pydantic valida los campos (longitud, formato, contraseñas coinciden).
    2. Verificar que username y email no estén ya en uso.
    3. Hashear la contraseña con bcrypt (cost=12).
    4. Insertar el registro en la BD y devolver 201.

    Seguridad:
    - La contraseña NUNCA se almacena en texto plano.
    - Los mensajes de error distinguen entre username y email para mejorar
      la UX en registro (es aceptable; el problema de enumeración es más
      crítico en /login).
    """
    # Verificar unicidad de username
    if await asyncio.to_thread(get_user_by_username_simple, req.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso. Elige otro.",
        )

    # Verificar unicidad de email
    if await asyncio.to_thread(get_user_by_email, req.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese correo electrónico.",
        )

    # Hash de contraseña (operación bloqueante → hilo separado)
    hashed = await asyncio.to_thread(hash_password, req.password)

    # Insertar usuario — id es SERIAL (Integer), la BD lo asigna automáticamente
    try:
        new_user = await asyncio.to_thread(
            create_user,
            req.username,
            req.first_name,
            req.last_name,
            req.email,
            hashed,
            req.hsk_level,
            req.native_language,
            req.learning_goals,
            req.interests,
        )
    except Exception as exc:
        print(f"[/auth/register] Error al crear usuario: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el usuario. Inténtalo de nuevo.",
        )

    return RegisterResponse(
        message="Cuenta creada exitosamente. ¡Bienvenido a Tars!",
        user_id=new_user["id"],          # Integer SERIAL
        username=new_user["username"],
    )


@app.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """
    Autentica a un usuario existente y devuelve un token JWT.

    Flujo:
    1. Buscar al usuario por username.
    2. Verificar la contraseña con bcrypt.
    3. Generar y devolver un JWT con user_id (Integer) en el payload.

    Seguridad (OWASP):
    - Mensaje de error genérico para evitar enumeración de usuarios.
    - verify_password usa tiempo constante (passlib) para prevenir timing attacks.
    - El hashed_password NUNCA se incluye en la respuesta.
    """
    # Buscar usuario (incluye hashed_password para verificación)
    user = await asyncio.to_thread(get_user_by_username, req.username)

    # Mensaje genérico deliberado: no revelar si el usuario existe o no
    INVALID_CREDENTIALS = "Usuario o contraseña incorrectos."

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_ok = await asyncio.to_thread(
        verify_password, req.password, user["hashed_password"]
    )
    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar token JWT — user_id es Integer SERIAL
    token = await asyncio.to_thread(
        create_access_token,
        {"sub": user["username"], "user_id": user["id"]},
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["id"],              # Integer SERIAL
        username=user["username"],
        first_name=user["first_name"],
        hsk_level=user["hsk_level"],
    )


@app.get("/api/user/profile", response_model=UserProfile)
async def get_profile(current_user_id: int = Depends(get_current_user)):
    """Obtiene el perfil completo del usuario autenticado."""
    user = await asyncio.to_thread(get_user_by_id, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserProfile(**user)


@app.put("/api/user/profile", response_model=UserProfile)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user_id: int = Depends(get_current_user)
):
    """Actualiza la información del perfil del usuario."""
    updated_user = await asyncio.to_thread(
        update_user_profile,
        current_user_id,
        profile_data.first_name,
        profile_data.last_name,
        profile_data.hsk_level,
        profile_data.native_language,
        profile_data.learning_goals,
        profile_data.interests,
    )
    if not updated_user:
        raise HTTPException(status_code=500, detail="Error al actualizar el perfil")
    return UserProfile(**updated_user)
