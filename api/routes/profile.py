"""Profile routes: user profile, greeting, preload message."""
import asyncio
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException

from openai import OpenAI

from agents.dataBase.main_queries import get_user_profile, get_roleplay_contexts
from auth.security import get_current_user
from auth.schemas import UserProfile, ProfileUpdateRequest
from agents.dataBase.auth_queries import get_user_by_id, update_user_profile
from ChatMessage.infraestructure.tts.google_tts import get_mixed_audio_bytes

logger = logging.getLogger(__name__)
router = APIRouter()
openai_client = OpenAI()

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
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
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
        raise HTTPException(status_code=500, detail="Error al actualizar el perfil")
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
        f"Generate ONE short greeting (1-2 sentences, ≤ 20 words) for a returning user. "
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


@router.get("/preload_message")
async def get_preload_message(current_user_id: int = Depends(get_current_user)):
    """Fast personalised TARS greeting for Normal Mode."""
    profile, uploaded_files = await asyncio.gather(
        asyncio.to_thread(get_user_profile, current_user_id),
        asyncio.to_thread(get_roleplay_contexts, current_user_id),
    )

    username = profile["username"]
    hsk_level = profile["hsk_level"]
    interest = profile["interest_area"]
    files_tip = f"Tiene escenarios: {', '.join(uploaded_files[:2])}." if uploaded_files else ""

    prompt = (
        f"Eres TARS. Saluda a {username} (HSK{hsk_level}, fandom: {interest}) "
        f"en UNA oración breve. {files_tip} "
        f"Dale un apodo basado en su fandom. Incluye 一个汉字 (pīnyīn). "
        f"Solo el mensaje, sin explicaciones."
    )

    llm_response = await asyncio.to_thread(
        lambda: openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=55,
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
