import os
import requests
from dotenv import load_dotenv
import subprocess
import shutil
import time

# brew install portaudio

# Load environment variables
load_dotenv()

# Set your Deepgram API Key and desired voice model
DG_API_KEY = os.getenv("DEEPGRAM_API_KEY")
MODEL_NAME = "aura-2-luciano-es"  # Valid Deepgram Aura model

def is_installed(lib_name: str) -> bool:
    lib = shutil.which(lib_name)
    return lib is not None

def play_stream(audio_stream, use_ffmpeg=True):
    player = "ffplay"
    if not is_installed(player):
        raise ValueError(f"{player} not found, necessary to stream audio.")
    
    player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
    player_process = subprocess.Popen(
        player_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for chunk in audio_stream:
        if chunk:
            player_process.stdin.write(chunk)  # type: ignore
            player_process.stdin.flush()  # type: ignore
    
    if player_process.stdin:
        player_process.stdin.close()
    player_process.wait()

def send_tts_request(text):
    DEEPGRAM_URL = f"https://api.deepgram.com/v1/speak?model={MODEL_NAME}"
    
    headers = {
        "Authorization": f"Token {DG_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text
    }
    
    player = "ffplay"
    if not is_installed(player):
        raise ValueError(f"{player} not found, necessary to stream audio.")
    
    # ffplay with -autoexit and -nodisp. 
    # Since we are not specifying format, ffplay will auto-detect from the stream (likely mp3).
    player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
    player_process = subprocess.Popen(
        player_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    start_time = time.time()  # Record the time before sending the request
    first_byte_time = None  # Initialize a variable to store the time when the first byte is received
    
    with requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload) as r:
        if r.status_code != 200:
            print(f"Error: {r.status_code} - {r.text}")
            return

        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                if first_byte_time is None:  # Check if this is the first chunk received
                    first_byte_time = time.time()  # Record the time when the first byte is received
                    ttfb = int((first_byte_time - start_time)*1000)  # Calculate the time to first byte
                    print(f"Time to First Byte (TTFB): {ttfb}ms")
                
                # Write each chunk to the player's stdin immediately
                if player_process.stdin:
                    try:
                        player_process.stdin.write(chunk)
                        player_process.stdin.flush()
                    except BrokenPipeError:
                        print("Player process closed unexpectedly.")
                        break

    # Close the player's stdin and wait for the process to finish
    if player_process.stdin:
        player_process.stdin.close()
    player_process.wait()
