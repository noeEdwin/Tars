import asyncio
from openai import OpenAI
import os

client = OpenAI()

async def test():
    with open("temp_audio.wav", "rb") as f:
        audio_bytes = f.read()
        
    print(f"File size: {len(audio_bytes)}")
    
    file_tuple = ("audio.wav", audio_bytes)
    
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=file_tuple,
        prompt="这是一段简体中文对话，请使用简体中文输出。"
    )
    print("Transcription:", transcription.text)

asyncio.run(test())
