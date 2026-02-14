import os
import json
import shutil
import subprocess
from google.cloud import texttospeech
from google.oauth2 import service_account  # Nuevo: Para manejar el JSON directamente
from dotenv import load_dotenv

# Load environment variables to ensure GOOGLE_APPLICATION_CREDENTIALS is set if needed
load_dotenv()

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

def play_stream(audio_generator):
    """
    Streams audio responses from Google TTS to ffplay.
    """
    player = "ffplay"
    if not is_installed(player):
        raise ValueError(f"{player} not found, necessary to stream audio.")
    
    # ffplay command: -autoexit to close when done, -nodisp to hide window, - (stdin)
    player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
    
    player_process = subprocess.Popen(
        player_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        for response in audio_generator:
            if response.audio_content:
                if player_process.stdin:
                    try:
                        player_process.stdin.write(response.audio_content)
                        player_process.stdin.flush()
                    except BrokenPipeError:
                        # Player closed
                        break
    except Exception as e:
        print(f"Error during streaming: {e}")
    finally:
        if player_process.stdin:
            player_process.stdin.close()
        player_process.wait()

# Constants for Voices
VOICE_MAPPING = {
    "zh": {
        "name": "cmn-CN-Chirp3-HD-Algenib", # or cmn-CN-Neural2-C
        "code": "cmn-CN"
    },
    "es": {
        "name": "es-ES-Chirp3-HD-Puck", # Chirp 3 HD is required for streaming
        "code": "es-ES" 
    }
}

def send_tts_request(text: str, voice_name: str = None, language_code: str = None):
    """
    Generates speech from text using Google Cloud TTS and streams it.
    Allows overriding voice/language for mixed-language support.
    """
    credentials = get_credentials()
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    # Defaults to Chinese if not specified (Legacy behavior)
    if not voice_name:
        voice_name = VOICE_MAPPING["zh"]["name"]
    if not language_code:
        language_code = VOICE_MAPPING["zh"]["code"]
    
    streaming_config = texttospeech.StreamingSynthesizeConfig(
        voice=texttospeech.VoiceSelectionParams(
            name=voice_name,
            language_code=language_code,
        ),
        streaming_audio_config=texttospeech.StreamingAudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
        )
    )

    def chunk_text(text, max_chars=100):
        """Splits text into chunks of max_chars, respecting sentence boundaries."""
        chunks = []
        current_chunk = ""
        # Split by common sentence delimiters (Chinese & Spanish)
        sentences = text.replace('。', '。|').replace('！', '！|').replace('？', '？|').replace('.', '.|').replace('!', '!|').replace('?', '?|').split('|')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chars:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def request_generator(text_input):
        # 1. First request: Config only
        yield texttospeech.StreamingSynthesizeRequest(
            streaming_config=streaming_config
        )

        # 2. Iterate over chunks
        chunks = chunk_text(text_input)
        for chunk in chunks:
            if chunk.strip():
                yield texttospeech.StreamingSynthesizeRequest(
                    input=texttospeech.StreamingSynthesisInput(text=chunk)
                )

    try:
        responses = client.streaming_synthesize(request_generator(text))
        play_stream(responses)
    except Exception as e:
        print(f"Google TTS Error: {e}")

def speak_mixed_text(text: str):
    """
    Intelligently switches voices based on text content (Hanzi vs Latin).
    """
    import re
    
    # Regex to split: Captures Chinese sequences. 
    # Everything else (Latin/Spanish/Numbers) is considered 'other' -> Spanish Voice
    # Pattern explanation: 
    # ([\u4e00-\u9fff，。？！“”]+) captures chunks of Chinese + punctuation.
    # ([\u4e00-\u9fff，。？！“”]+) captures chunks of Chinese + punctuation.
    parts = re.split(r'([\u4e00-\u9fff，。？！“”]+)', text)
    
    for part in parts:
        if not part.strip():
            continue
            
        # Check if this part is Chinese
        if re.search(r'[\u4e00-\u9fff]', part):
            # Use Chinese Voice
            send_tts_request(
                part, 
                voice_name=VOICE_MAPPING["zh"]["name"], 
                language_code=VOICE_MAPPING["zh"]["code"]
            )
        else:
            # Use Spanish Voice (for Pinyin/Spanish/English)
            if re.search(r'[a-zA-Z0-9]', part):
                send_tts_request(
                    part, 
                    voice_name=VOICE_MAPPING["es"]["name"], 
                    language_code=VOICE_MAPPING["es"]["code"]
                )

if __name__ == "__main__":
    # Test the module
    print("Testing Google TTS (Chinese Voice)...")
    send_tts_request("你好！我是Pingo。Hola, soy tu tutor de chino.")