import os
import json
import shutil
import subprocess
import asyncio
import re
from google.cloud import texttospeech_v1 as texttospeech
from google.oauth2 import service_account  # Nuevo: Para manejar el JSON directamente
from dotenv import load_dotenv

# Load environment variables to ensure GOOGLE_APPLICATION_CREDENTIALS is set if needed
load_dotenv()

VOICE_MAPPING = {
    "zh": {"name": "cmn-CN-Chirp3-HD-Algenib", "code": "cmn-CN"},
    "es": {"name": "es-ES-Chirp3-HD-Puck", "code": "es-ES"}
}
def get_credentials():
    """
    Load the credentials from a json content string in env var GOOGLE_JSON_CREDENTIALS.
    Returns None if not found, allowing fallback to GOOGLE_APPLICATION_CREDENTIALS file path.
    """
    json_creds = os.getenv('GOOGLE_JSON_CREDENTIALS')
    if not json_creds:
        # Fallback: Check if we have a local file and set GOOGLE_APPLICATION_CREDENTIALS if not set
        credentials_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../tars.json'))
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        return None
    
    try:
        info = json.loads(json_creds)
        return service_account.Credentials.from_service_account_info(info)
    except json.JSONDecodeError:
        print("Warning: GOOGLE_JSON_CREDENTIALS is not valid JSON. Trying file-based auth.")
        return None

def is_installed(lib_name: str) -> bool:
    lib = shutil.which(lib_name)
    return lib is not None


async def get_tts_bytes_async(text: str, lang_type: str) -> bytes:
    """
    Petición individual asíncrona a Google Cloud TTS.
    """
    credentials = get_credentials()
    client = texttospeech.TextToSpeechAsyncClient(credentials=credentials)

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
    Divide el texto y dispara todas las peticiones a Google SIMULTÁNEAMENTE.
    """
    # 1. Limpieza de texto (quitamos Pinyin entre paréntesis para el audio)
    clean_text = re.sub(r'\(.*?\)', '', text).replace('[', '').replace(']', '').replace('*', '')
    
    # 2. Split inteligente (Chino vs Resto)
    parts = re.split(r'([\u4e00-\u9fff，。？！“”]+)', clean_text)
    
    tasks = []
    for part in parts:
        stripped_part = part.strip()
        if not stripped_part:
            continue
            
        # 3. Creamos la lista de "Tareas" (sin ejecutarlas aún)
        if re.search(r'[\u4e00-\u9fff]', stripped_part):
            tasks.append(get_tts_bytes_async(stripped_part, "zh"))
        else:
            if re.search(r'[a-zA-Z0-9]', stripped_part):
                tasks.append(get_tts_bytes_async(stripped_part, "es"))

    if not tasks:
        return b""

    # 4. EL TURBO: Ejecutamos todas las tareas en paralelo y esperamos a que terminen
    # asyncio.gather mantiene el orden de los resultados igual al de la lista 'tasks'
    audio_segments = await asyncio.gather(*tasks)

    # 5. Concatenamos los fragmentos de audio en uno solo
    return b"".join(audio_segments)
    

