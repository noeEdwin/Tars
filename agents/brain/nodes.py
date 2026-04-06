import sys
import json
import os
from pathlib import Path
from thefuzz import fuzz
from dotenv import load_dotenv

# Configuración de rutas
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Importaciones de Tars
from RAG.retrieve import retrieve_knowledge, retrieve_style_examples
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection
from dataBase.persona_db import fetch_persona_from_db
from brain.identity_agent import generate_persona
from brain.schema import TarsState
from brain.chains import PROTOCOLS, get_tars_expert, actor_prompt_template

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

load_dotenv()
ACTOR = "tars_actor"

def is_phonetically_similar(target: str, user_input: str) -> bool:
    ratio = fuzz.partial_ratio(target.lower(), user_input.lower())
    return ratio > 80

def load_lesson_json(lesson_id: int):
    try:
        # Asegura la ruta correcta desde la raíz del proyecto
        base_path = Path(__file__).resolve().parent.parent.parent
        file_path = base_path / "data_normal_mode" / "data" / f"leccion_{lesson_id}.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"vocabulary": [{"zh": "你好", "py": "nǐ hǎo", "es": "hola"}]}

def actor_node(state: TarsState) -> dict:
    """Nodo Actor: Gestiona lógica de lecciones, RAG técnico y RAG de personalidad."""
    expert_type = state.get("user_mode", "tars_normal")
    llm_expert = get_tars_expert(expert_type=expert_type)
    protocol_text = PROTOCOLS.get(expert_type, "Standard operating procedures.")
    
    last_user_msg = state["messages"][-1].content
    lesson_state_updates = {}
    feedback_type = "NONE"
    current_lesson = state.get("current_lesson", 1)

    # 1. ── LÓGICA DE LECCIONES (Modo Normal) ──
    if expert_type == "tars_normal":
        lesson_words = state.get("lesson_words")
        lesson_progress = state.get("lesson_progress", 0)
        target_word = state.get("target_word")

        if not lesson_words:
            lesson_data = load_lesson_json(current_lesson)
            lesson_words = [v["zh"] for v in lesson_data["vocabulary"]]
            lesson_progress = 0
            target_word = lesson_words[0]
            feedback_type = "INTRODUCE"
        elif target_word:
            said_it = (target_word in last_user_msg or is_phonetically_similar(target_word, last_user_msg))
            if said_it:
                lesson_progress += 1
                if lesson_progress < len(lesson_words):
                    target_word = lesson_words[lesson_progress]
                    feedback_type = "CORRECT_NEXT"
                else:
                    feedback_type = "LESSON_COMPLETE"
            else:
                feedback_type = "RETRY"
        
        # Guardamos actualizaciones para el estado
        lesson_state_updates = {
            "lesson_words": lesson_words,
            "lesson_progress": lesson_progress,
            "target_word": target_word,
            "feedback_type": feedback_type
        }

        # Inyectamos el estado técnico en el protocolo
        protocol_text += f"\n\n### SISTEMA DE VALIDACIÓN HSK ###\n- Feedback: {feedback_type}\n- Objetivo: {target_word}\n"

    # 2. ── RAG DE ESTILO (Personalidad) ──
    target_emotion = "neutro"
    if feedback_type == "RETRY":
        target_emotion = "sarcástico"
    elif feedback_type == "CORRECT_NEXT" or feedback_type == "LESSON_COMPLETE":
        target_emotion = "motivacional"

    try:
        user_vec = get_embedding(last_user_msg)
        ejemplos = retrieve_style_examples(target_emotion, user_vec, limit=3)
        
        # Log para consola de Uvicorn
        print(f"DEBUG | Estilo: {target_emotion} | Ejemplos: {len(ejemplos)} recuperados")
        
        if ejemplos:
            style_instruction = f"\n\n### INSTRUCCIÓN DE PERSONALIDAD (MANDATORIA) ###\n"
            style_instruction += f"Tu tono actual DEBE ser {target_emotion.upper()}. "
            style_instruction += "Imita la estructura y actitud de estos diálogos reales:\n"
            style_instruction += "\n".join([f"- {ex}" for ex in ejemplos])
            style_instruction += "\n### FIN DE PERSONALIDAD ###\n"
            # Ponemos el estilo al final del protocolo para que tenga más peso
            protocol_text += style_instruction
    except Exception as e:
        print(f"⚠️ Error en RAG de Estilo: {e}")

    # 3. ── RAG TÉCNICO (Conocimiento de Chino) ──
    context_str = "Usa tu conocimiento base de HSK1."
    if len(last_user_msg) > 5:
        try:
            docs = retrieve_knowledge(last_user_msg, current_lesson=current_lesson)
            if docs:
                formatted = [f"- {d['contenido_zh']} ({d['pinyin']}) -> {d['traduccion_es']}" for d in docs]
                context_str = "\n".join(formatted)
        except Exception as e:
            print(f"⚠️ RAG Técnico Error: {e}")

    # Reemplazamos el placeholder del protocolo
    protocol_text = protocol_text.replace("{context}", context_str)

    # 4. ── GENERACIÓN Y RETORNO ──
    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    response = dynamic_chain.invoke(state)
    
    return {"messages": [response], **lesson_state_updates}

# --- CONFIGURACIÓN DEL GRAFO ---
workflow = StateGraph(TarsState)
workflow.add_node(ACTOR, actor_node)
workflow.add_edge(START, ACTOR)
workflow.add_edge(ACTOR, END)
config = {"configurable": {"thread_id": 1}}