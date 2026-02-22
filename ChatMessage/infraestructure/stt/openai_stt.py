import sys
import queue
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
import numpy as np

# Load openai client, assumes OPENAI_API_KEY is in environment variables
client = OpenAI()

def record_and_transcribe(samplerate=16000, channels=1):
    """
    Graba audio desde el micrófono controlando el inicio y fin con la tecla 'Enter'.
    Luego transcribe el audio resultante usando OpenAI Whisper.
    """
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    try:
        print("\nPresiona Enter para hablar...", end="")
        input()
        print("Grabando... (Presiona Enter para detener)", end="")
        
        # Iniciar la grabación
        stream = sd.InputStream(samplerate=samplerate, channels=channels, callback=callback)
        with stream:
            # Esperar a que el usuario presione Enter de nuevo para detener
            input()
            
        print("Grabación detenida. Procesando audio...")
        
        audio_data = []
        while not q.empty():
            audio_data.append(q.get())
            
        if not audio_data:
            return ""
            
        audio_concat = np.concatenate(audio_data, axis=0)
        temp_filename = "temp_audio.wav"
        
        # Guardar en archivo temporal
        sf.write(temp_filename, audio_concat, samplerate)

        # Transcribir el archivo
        with open(temp_filename, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            
        return transcription.text.strip()
        
    except KeyboardInterrupt:
        return ""
    except Exception as e:
        print(f"\nError en STT: {e}")
        return ""
