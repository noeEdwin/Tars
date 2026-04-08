# agents/brain/personality_rag.py
from RAG.retrieve import retrieve_style_examples
from RAG.utils import get_embedding

# Mapeo enriquecido usando las emociones de tu DB
EMOTION_MAP = {
    "RETRY": "directo",               # Cuando se equivocan, Tars es directo
    "CORRECT_NEXT": "motivacional",   # Cuando aciertan, los anima
    "LESSON_COMPLETE": "exclamativo", # Al terminar, cierra con energía
    "INTRODUCE": "neutro",            # Al presentar la lección se mantiene claro
    "DEFAULT": "neutro"
}

def append_style_examples(last_user_msg: str, feedback_type: str, protocol_text: str) -> str:
    """
    Inyecta instrucciones de personalidad (RAG) al prompt basado en el tipo de feedback,
    consultando la tabla translations_mvp.
    """
    target_emotion = EMOTION_MAP.get(feedback_type, EMOTION_MAP["DEFAULT"])

    # Evitar generar embeddings para mensajes muy cortos/vacíos
    if not last_user_msg.strip():
        last_user_msg = "hola" 

    try:
        user_vec = get_embedding(last_user_msg)
        ejemplos = retrieve_style_examples(target_emotion, user_vec, limit=3)
        
        # ⚠️ DEBUG: Lo dejamos para tu validación de QA. Luego lo borramos.
        print(f"DEBUG | Estilo: {target_emotion} | Ejemplos: {len(ejemplos)} recuperados")
        
        if ejemplos:
            style_instruction = "\n\n### INSTRUCCIÓN DE PERSONALIDAD (MANDATORIA) ###\n"
            style_instruction += f"Tu tono actual DEBE ser {target_emotion.upper()}. "
            style_instruction += "Imita la estructura y actitud de estos diálogos reales:\n"
            style_instruction += "\n".join([f"- {ex}" for ex in ejemplos])
            style_instruction += "\n### FIN DE PERSONALIDAD ###\n"
            protocol_text += style_instruction
            
    except Exception as e:
        print(f"⚠️ Error en RAG de Estilo: {e}")
        
    return protocol_text