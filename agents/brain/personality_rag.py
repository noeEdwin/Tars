# agents/brain/personality_rag.py
from RAG.retrieve import retrieve_style_examples
from RAG.utils import get_embedding
import random



EMOTION_MAP = {
    "RETRY": "directo",
    "CORRECT_NEXT": "motivacional",
    "LESSON_COMPLETE": "exclamativo",
    "INTRODUCE": "neutro",
    "DEFAULT": "neutro"
}

def append_style_examples(last_user_msg: str, feedback_type: str, protocol_text: str) -> str:
    """
    Inyecta instrucciones de personalidad (RAG) al prompt basado en el tipo de feedback,
    consultando la tabla translations_mvp.
    """
    from api import app_state
    library = app_state.get("style_library", {})
    
    # Mapeo simple: si es RETRY, dame algo sarcástico. Si es CORRECT, algo neutro/alentador.
    target_vibe = "sarcástico" if feedback_type == "RETRY" else "neutro"
    
    # Obtenemos ejemplos de la RAM 
    ejemplos = library.get(target_vibe, [])
    
    if ejemplos:
        # Elegimos 2 o 3 al azar para que Tars no sea repetitivo
        seleccion = random.sample(ejemplos, min(len(ejemplos), 3))
        
        style_instruction = "\n\n### GUÍA DE NATURALIDAD (CINE CHINO) ###\n"
        style_instruction += f"No hables como un libro. Usa el tono: {target_vibe.upper()}.\n"
        style_instruction += "Fíjate en cómo se estructuran estas frases reales:\n"
        for ex in seleccion:
            style_instruction += f"- Chino: {ex['zh']} (Significa: {ex['es']})\n"
        style_instruction += "\n### FIN DE GUÍA ###\n"
        
        return protocol_text + style_instruction
    
    return protocol_text