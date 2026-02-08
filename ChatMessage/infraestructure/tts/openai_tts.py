import os
from openai import OpenAI
from dotenv import load_dotenv
import shutil
import subprocess

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_installed(lib_name: str) -> bool:
    lib = shutil.which(lib_name)
    return lib is not None

def play_stream(audio_response):
    """
    Streams audio response from OpenAI TTS to ffplay.
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
        if player_process.stdin:
            for chunk in audio_response.iter_bytes(chunk_size=4096):
                if chunk:
                    try:
                        player_process.stdin.write(chunk)
                        player_process.stdin.flush()
                    except BrokenPipeError:
                        break
    except Exception as e:
        print(f"Error during streaming: {e}")
    finally:
        if player_process.stdin:
            player_process.stdin.close()
        player_process.wait()

def send_tts_request(text: str):
    """
    Generates speech from text using OpenAI TTS and streams it to the speakers.
    Uses the 'tts-1' model and a configurable voice (default: alloy).
    """
    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="alloy",
            input=text,
            response_format="mp3" # Streamable format
        )
        play_stream(response)
    except Exception as e:
        print(f"OpenAI TTS Error: {e}")

if __name__ == "__main__":
    # Test the module
    print("Testing OpenAI TTS (Chinese/Spanish check)...")
    send_tts_request("你好！我是Pingo。Hola, soy tu tutor de chino.")
