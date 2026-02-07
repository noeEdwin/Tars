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

def send_tts_request(text: str):
    """
    Generates speech from text using Google Cloud TTS and streams it to the speakers.
    Defaults to a Chinese male voice (cmn-CN-Neural2-C) for the Pingo persona.
    """
    credentials = get_credentials()
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    voice_name = "cmn-CN-Chirp3-HD-Charon" 
    language_code = "cmn-CN"
    
    streaming_config = texttospeech.StreamingSynthesizeConfig(
        voice=texttospeech.VoiceSelectionParams(
            name=voice_name,
            language_code=language_code,
        ),
        streaming_audio_config=texttospeech.StreamingAudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
        )
    )

    def request_generator(text_input):
        # 1. First request: Config only
        yield texttospeech.StreamingSynthesizeRequest(
            streaming_config=streaming_config
        )

        yield texttospeech.StreamingSynthesizeRequest(
            input=texttospeech.StreamingSynthesisInput(text=text_input)
        )

    try:
        responses = client.streaming_synthesize(request_generator(text))
        play_stream(responses)
    except Exception as e:
        print(f"Google TTS Error: {e}")

if __name__ == "__main__":
    # Test the module
    print("Testing Google TTS (Chinese Voice)...")
    send_tts_request("你好！我是Pingo。Hola, soy tu tutor de chino.")