"""Speech-to-text route."""
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File

from openai import OpenAI

logger = logging.getLogger(__name__)
router = APIRouter()
openai_client = OpenAI()

WHISPER_HALLUCINATIONS = {
    "请使用简体中文输出。",
    "这是一段简体中文对话，请使用简体中文输出。",
    "这是一段简体中文和西班牙语的双语对话。请使用简体中文和西班牙语输出。",
    "字幕by索兰娅",
}


@router.post("")
async def stt_endpoint(audio: UploadFile = File(...)):
    """Accept an audio file and transcribe it using OpenAI Whisper."""
    try:
        audio_bytes = await audio.read()
        file_tuple = (audio.filename or "audio.webm", audio_bytes)

        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=file_tuple,
            prompt="这是一段简体中文和西班牙语的双语对话。请使用简体中文和西班牙语输出。",
        )
        text = transcription.text.strip()
        logger.info("STT Output: %s, size: %d", text, len(audio_bytes))

        if text in WHISPER_HALLUCINATIONS or len(text) < 2:
            return {"text": ""}

        return {"text": text}
    except Exception as e:
        logger.error("Error in backend STT: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
