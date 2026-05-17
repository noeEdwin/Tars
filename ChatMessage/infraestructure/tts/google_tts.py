import os
import json
import shutil
import subprocess
import asyncio
import re
from google.cloud import texttospeech_v1 as texttospeech
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables to ensure GOOGLE_APPLICATION_CREDENTIALS is set if needed
load_dotenv()

VOICE_MAPPING = {
    "zh": {"name": "cmn-CN-Chirp3-HD-Algenib", "code": "cmn-CN"},
    "es": {"name": "es-ES-Chirp3-HD-Puck", "code": "es-ES"}
}
_tts_client = None



def get_credentials():
    """
    Load Google Cloud credentials from environment.

    Supports two methods (checked in order):
    1. GOOGLE_JSON_CREDENTIALS — JSON string content of the service account key
    2. GOOGLE_APPLICATION_CREDENTIALS — file path (handled automatically by Google SDK)

    Returns None if neither is set, allowing the SDK to fall back to default credentials.
    """
    json_creds = os.getenv('GOOGLE_JSON_CREDENTIALS')
    if not json_creds:
        return None

    try:
        info = json.loads(json_creds)
        return service_account.Credentials.from_service_account_info(info)
    except json.JSONDecodeError:
        print("Warning: GOOGLE_JSON_CREDENTIALS is not valid JSON.")
        return None

def is_installed(lib_name: str) -> bool:
    lib = shutil.which(lib_name)
    return lib is not None

def get_tts_client():
    global _tts_client
    if _tts_client is None:
        credentials = get_credentials()
        _tts_client = texttospeech.TextToSpeechAsyncClient(credentials=credentials)
    return _tts_client

async def get_tts_bytes_async(text: str, lang_type: str) -> bytes:
    """
    Individual async request to Google Cloud TTS.
    """
    client = get_tts_client()

    voice_conf = VOICE_MAPPING[lang_type]
    
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=voice_conf["code"],
        name=voice_conf["name"]
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    try:
        response = await client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
        return response.audio_content
    except Exception as e:
        print(f"Error en TTS ({lang_type}): {e}")
        return b""
        
async def get_mixed_audio_bytes(text: str) -> bytes:
    """
    Split text by language and fire all TTS requests to Google SIMULTANEOUSLY.
    """
    # 1. Clean text (remove pinyin in parentheses for audio output)
    clean_text = re.sub(r'\(.*?\)', '', text).replace('[', '').replace(']', '').replace('*', '')
    
    # 2. Smart split (Chinese segments vs non-Chinese)
    parts = re.split(r'([\u4e00-\u9fff，。？！"""]+)', clean_text)
    
    tasks = []
    for part in parts:
        stripped_part = part.strip()
        if not stripped_part:
            continue
            
        # 3. Build task list (not yet executed)
        if re.search(r'[\u4e00-\u9fff]', stripped_part):
            tasks.append(get_tts_bytes_async(stripped_part, "zh"))
        else:
            if re.search(r'[a-zA-Z0-9]', stripped_part):
                tasks.append(get_tts_bytes_async(stripped_part, "es"))

    if not tasks:
        return b""

    # 4. TURBO: Execute all tasks in parallel and wait for completion
    # asyncio.gather preserves result order matching the task list order
    audio_segments = await asyncio.gather(*tasks)

    # 5. Concatenate audio segments into a single byte stream
    return b"".join(audio_segments)
    

