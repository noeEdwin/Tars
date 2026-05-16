"""Profile routes: user profile, greeting, preload message."""
import asyncio
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from openai import OpenAI

from agents.dataBase.main_queries import get_user_profile, get_roleplay_contexts
from agents.dataBase.persona_db import fetch_persona_from_db
from agents.brain.utils import load_lesson_json
from auth.security import get_current_user
from auth.schemas import UserProfile, ProfileUpdateRequest
from agents.dataBase.auth_queries import get_user_by_id, update_user_profile
from ChatMessage.infraestructure.tts.google_tts import get_mixed_audio_bytes

logger = logging.getLogger(__name__)
router = APIRouter()
openai_client = OpenAI()

# Shared state — populated by app lifespan
app_state: dict = {}

# Emotion style map (mirrors node_learning.py)
EMOTION_MAP = {
    "RETRY": "directo",
    "CORRECT_NEXT": "motivacional",
    "LESSON_COMPLETE": "exclamativo",
    "INTRODUCE": "neutro",
    "DEFAULT": "neutro",
}


@router.get("/api/user/profile", response_model=UserProfile)
async def get_profile(current_user_id: int = Depends(get_current_user)):
    user = await asyncio.to_thread(get_user_by_id, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**user)


@router.put("/api/user/profile", response_model=UserProfile)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user_id: int = Depends(get_current_user),
):
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
        raise HTTPException(status_code=500, detail="Error updating profile")
    return UserProfile(**updated_user)


@router.get("/greeting")
async def get_greeting(current_user_id: int = Depends(get_current_user)):
    """Return a short, personalised greeting from TARS."""
    profile = await asyncio.to_thread(get_user_profile, current_user_id)

    username = profile["username"]
    hsk_level = profile["hsk_level"]
    interest = profile["interest_area"]

    prompt = (
        f"You are TARS, a witty, warm AI tutor for Chinese. "
        f"Generate ONE short greeting (1-2 sentences, <= 20 words) for a returning user. "
        f"Use their personal details to make it feel special and unique. "
        f"Details: name='{username}', HSK level={hsk_level}, interest/fandom='{interest}'. "
        f"Be creative and playful — reference their interest with a fun nickname or title. "
        f"Examples: 'Welcome back, my Cosmere traveller! Ready to conquer more characters?', "
        f"'Greetings, young Padawan {username} — the Force of Mandarin awaits you today!'. "
        f"Output ONLY the greeting sentence, nothing else. "
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


async def _get_next_lesson_word(user_id: int) -> dict:
    """Get the next word the user should learn from LangGraph state."""
    app_instance = app_state.get("app_instance")
    if app_instance:
        try:
            thread_id = f"{user_id}_normal"
            cfg = {"configurable": {"thread_id": thread_id}}
            snapshot = await app_instance.aget_state(cfg)

            if snapshot.values:
                current_lesson = snapshot.values.get("current_lesson", 1)
                lesson_progress = snapshot.values.get("lesson_progress", 0)
                target_word = snapshot.values.get("target_word")
                lesson_words = snapshot.values.get("lesson_words", [])

                if target_word and lesson_words:
                    lesson_data = load_lesson_json(current_lesson)
                    vocab = lesson_data.get("vocabulary", [])
                    vocab_by_zh = {v["zh"]: v for v in vocab}
                    word_info = vocab_by_zh.get(target_word, {})
                    return {
                        "word": target_word,
                        "pinyin": word_info.get("py", ""),
                        "meaning": word_info.get("es", ""),
                        "progress": lesson_progress,
                        "total": len(lesson_words),
                        "lesson": current_lesson,
                        "is_continuing": lesson_progress > 0,
                    }
        except Exception as e:
            logger.warning("Could not read LangGraph state: %s", e)

    # Fallback: lesson 1, first word
    lesson_data = load_lesson_json(1)
    vocab = lesson_data.get("vocabulary", [])
    if vocab:
        first = vocab[0]
        return {
            "word": first["zh"],
            "pinyin": first["py"],
            "meaning": first["es"],
            "progress": 0,
            "total": len(vocab),
            "lesson": 1,
            "is_continuing": False,
        }
    return {"word": "你好", "pinyin": "nǐ hǎo", "meaning": "hola", "progress": 0, "total": 0, "lesson": 1, "is_continuing": False}


@router.get("/preload_message")
async def get_preload_message(current_user_id: int = Depends(get_current_user)):
    """Personalised TARS greeting for Normal Mode with lesson context."""
    profile, uploaded_files, next_word = await asyncio.gather(
        asyncio.to_thread(get_user_profile, current_user_id),
        asyncio.to_thread(get_roleplay_contexts, current_user_id),
        _get_next_lesson_word(current_user_id),
    )

    username = profile["username"]
    hsk_level = profile["hsk_level"]
    interest = profile["interest_area"]
    files_tip = f"Has scenarios available: {', '.join(uploaded_files[:2])}." if uploaded_files else ""

    word_context = ""
    if next_word["is_continuing"]:
        word_context = (
            f"The user is continuing lesson {next_word['lesson']} "
            f"({next_word['progress']}/{next_word['total']} words done). "
            f"Their NEXT word to practice is: {next_word['word']} ({next_word['pinyin']}) — '{next_word['meaning']}'. "
            f"Weave this into the greeting naturally, e.g., 'Ready for {next_word['word']}?'"
        )
    else:
        word_context = (
            f"The user is starting lesson {next_word['lesson']}. "
            f"Their FIRST word to learn is: {next_word['word']} ({next_word['pinyin']}) — '{next_word['meaning']}'. "
            f"Tease this in the greeting, e.g., 'Today we conquer {next_word['word']}!'"
        )

    prompt = (
        f"You are TARS. Greet {username} (HSK{hsk_level}, fandom: {interest}) "
        f"in ONE brief sentence. {files_tip} "
        f"Give them a nickname based on their fandom. Include 一个汉字 (pīnyīn). "
        f"{word_context} "
        f"Only the message, no explanations. Respond in Spanish."
    )

    llm_response = await asyncio.to_thread(
        lambda: openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.9,
        )
    )
    text = llm_response.choices[0].message.content.strip()

    audio_b64 = None
    try:
        audio_bytes = await get_mixed_audio_bytes(text)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.warning("[preload_message] TTS skipped: %s", e)

    return {"text": text, "audio_b64": audio_b64}


@router.get("/preload_message_roleplay")
async def get_roleplay_preload(
    tars_role: str = Query(...),
    filename: str = Query(default=""),
    current_user_id: int = Depends(get_current_user),
):
    """In-character greeting for Roleplay Mode."""
    persona = await asyncio.to_thread(fetch_persona_from_db, tars_role, None)

    if persona:
        persona_context = (
            f"You are {tars_role}. "
            f"Archetype: {persona['archetype']}. "
            f"Speech style: {persona['speech_style']}. "
            f"Traits: {persona['traits']}. "
            f"Rules: {', '.join(persona.get('rules', []))}. "
            f"Emotional anchor: {persona['emotional_anchor']}. "
        )
    else:
        persona_context = f"You are {tars_role}, a character in an immersive story. "

    prompt = (
        f"{persona_context}"
        f"Give a brief, in-character greeting (1-2 sentences) to a new conversation partner. "
        f"Stay completely in character. Reveal your name and personality naturally. "
        f"Do NOT mention being an AI or a game. End with a question. "
        f"Respond in Spanish."
    )

    llm_response = await asyncio.to_thread(
        lambda: openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.9,
        )
    )
    text = llm_response.choices[0].message.content.strip()

    audio_b64 = None
    try:
        audio_bytes = await get_mixed_audio_bytes(text)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.warning("[preload_message_roleplay] TTS skipped: %s", e)

    return {"text": text, "audio_b64": audio_b64}
