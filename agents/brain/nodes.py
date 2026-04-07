import sys
import json
import os
from pathlib import Path
from thefuzz import fuzz
from dotenv import load_dotenv

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from RAG.retrieve import retrieve_knowledge, retrieve_style_examples
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection
from dataBase.persona_db import fetch_persona_from_db
from brain.identity_agent import generate_persona
from brain.schema import TarsState
from brain.chains import PROTOCOLS, get_tars_expert, actor_prompt_template

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langchain_openai import ChatOpenAI

load_dotenv()

ACTOR         = "tars_actor"
LESSON_PROMPT = "lesson_prompt"
LESSON_CHECK  = "lesson_check"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def is_phonetically_similar(target: str, user_input: str) -> bool:
    """True when fuzz ratio > 80 AND the strings share at least one character."""
    if not target or not user_input:
        return False
    # Guard: don't match if target character is completely absent
    if not any(c in user_input for c in target):
        return False
    ratio = fuzz.partial_ratio(target.lower(), user_input.lower())
    return ratio > 80


def load_lesson_json(lesson_id: int) -> dict:
    try:
        # Asegura la ruta correcta desde la raíz del proyecto
        base_path = Path(__file__).resolve().parent.parent.parent
        file_path = base_path / "data_normal_mode" / "data" / f"leccion_{lesson_id}.json"
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"vocabulary": [{"zh": "你好", "py": "nǐ hǎo", "es": "hola"}]}


def _build_rag_context(last_user_msg: str, current_lesson: int | None) -> str:
    """Return a formatted RAG context string, or empty string on error."""
    if not last_user_msg or len(last_user_msg) <= 10:
        return ""
    try:
        context_docs = retrieve_knowledge(last_user_msg, current_lesson=current_lesson)
        if not context_docs:
            return ""
        if isinstance(context_docs, list):
            formatted = []
            for item in context_docs:
                if not isinstance(item, dict):
                    continue
                if "content" in item:
                    formatted.append(f"- {item['content']}")
                elif "contenido_zh" in item:
                    zh      = item.get("contenido_zh", "")
                    pinyin  = item.get("pinyin", "")
                    trad    = item.get("traduccion_es", "")
                    pos     = item.get("pos", "")
                    grammar = item.get("grammar_ref", "")
                    s = f"- {zh} ({pinyin}) - Significado: {trad}"
                    if pos:
                        s += f", POS: {pos}"
                    if grammar:
                        s += f", Regla HSK: {grammar}"
                    formatted.append(s)
            return "\n".join(formatted)
        return str(context_docs)
    except Exception as e:
        print(f"RAG Error (Ignored): {e}")
        return ""


def _append_memory_context(user_id, last_user_msg: str, protocol_text: str) -> str:
    """Fetch user long-term memories and append to protocol_text."""
    if not user_id or len(last_user_msg) <= 5:
        return protocol_text
    try:
        from RAG.save_memory import retrieve_user_memory
        memories = retrieve_user_memory(int(user_id), last_user_msg, limit=3)
        if memories:
            memory_context = "\n=== RELEVANT PAST MEMORIES ===\n" + "\n".join(memories) + "\n==============================\n"
            protocol_text += f"\n\n{memory_context}"
    except Exception as e:
        print(f"Memory Retrieval Error: {e}")
    return protocol_text


def _append_style_examples(last_user_msg: str, feedback_type: str, protocol_text: str) -> str:
    """Append style instructions based on RAG of Personality."""
    target_emotion = "neutro"
    if feedback_type == "RETRY":
        target_emotion = "sarcástico"
    elif feedback_type == "CORRECT_NEXT" or feedback_type == "LESSON_COMPLETE":
        target_emotion = "motivacional"
    elif feedback_type == "INTRODUCE":
        target_emotion = "neutro"

    # Avoid generating embeddings for very short/empty messages
    if not last_user_msg.strip():
        last_user_msg = "hola" 

    try:
        user_vec = get_embedding(last_user_msg)
        ejemplos = retrieve_style_examples(target_emotion, user_vec, limit=3)
        
        print(f"DEBUG | Estilo: {target_emotion} | Ejemplos: {len(ejemplos)} recuperados")
        
        if ejemplos:
            style_instruction = f"\n\n### INSTRUCCIÓN DE PERSONALIDAD (MANDATORIA) ###\n"
            style_instruction += f"Tu tono actual DEBE ser {target_emotion.upper()}. "
            style_instruction += "Imita la estructura y actitud de estos diálogos reales:\n"
            style_instruction += "\n".join([f"- {ex}" for ex in ejemplos])
            style_instruction += "\n### FIN DE PERSONALIDAD ###\n"
            protocol_text += style_instruction
    except Exception as e:
        print(f"⚠️ Error en RAG de Estilo: {e}")
        
    return protocol_text


# ─────────────────────────────────────────────────────────────────────────────
# Routing
# ─────────────────────────────────────────────────────────────────────────────

def route_lesson(state: TarsState) -> str:
    """Route to the correct node based on mode and lesson phase."""
    if state.get("user_mode") != "tars_normal":
        return ACTOR
    if state.get("awaiting_answer"):
        return LESSON_CHECK
    return LESSON_PROMPT


# ─────────────────────────────────────────────────────────────────────────────
# Lesson node — Phase 1: Introduce the target word
# ─────────────────────────────────────────────────────────────────────────────

def lesson_prompt_node(state: TarsState) -> dict:
    """
    Runs when awaiting_answer is False.
    Loads the lesson words if needed, then asks the user to say the target word.
    Sets awaiting_answer = True before returning so the next turn goes to lesson_check_node.
    """
    llm_expert      = get_tars_expert(expert_type="tars_normal")
    current_lesson  = state.get("current_lesson", 1)
    lesson_words    = state.get("lesson_words")
    lesson_progress = state.get("lesson_progress", 0)
    target_word     = state.get("target_word")

    # Load the authoritative lesson data (always, so we have pinyin / meaning)
    lesson_data = load_lesson_json(current_lesson)
    vocab_list  = lesson_data["vocabulary"]
    vocab_by_zh = {v["zh"]: v for v in vocab_list}

    state_updates: dict = {}

    # First turn for this lesson: initialise from the JSON
    if not lesson_words:
        lesson_words    = [v["zh"] for v in vocab_list]
        lesson_progress = 0
        target_word     = lesson_words[0]
        state_updates.update({
            "lesson_words":    lesson_words,
            "lesson_progress": lesson_progress,
            "target_word":     target_word,
        })

    lesson_vocab_str = ", ".join(lesson_words)
    target_info      = vocab_by_zh.get(target_word, {})
    target_pinyin    = target_info.get("py", "")
    target_meaning   = target_info.get("es", "")

    protocol_text = PROTOCOLS.get("tars_normal", "Standard operating procedures.")
    protocol_text = protocol_text.replace("{context}", "No relevant context for this turn.")
    protocol_text += f"""

### LECCIÓN EN CURSO — ACCIÓN: INTRODUCIR PALABRA
Lección {current_lesson} | Vocabulario completo: {lesson_vocab_str}
Progreso: {lesson_progress}/{len(lesson_words)} palabras completadas
Palabra objetivo actual: **{target_word}** ({target_pinyin}) — "{target_meaning}"

INSTRUCCIÓN DEL SISTEMA (obligatoria):
1. Primero pregunta brevemente "¿Estás listo?" o "¿Comenzamos?".
2. Luego presenta únicamente la palabra **{target_word}** ({target_pinyin}) que significa "{target_meaning}".
3. Pide al usuario que repita esa palabra en voz alta o que la escriba.
4. NO avances a la siguiente palabra. Espera su respuesta.
"""

    last_user_msg = (state["messages"][-1].content
                     if state.get("messages") else "")
    protocol_text = _append_memory_context(state.get("user_id"), last_user_msg, protocol_text)
    protocol_text = _append_style_examples(last_user_msg, "INTRODUCE", protocol_text)

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    response = dynamic_chain.invoke(state)

    return {
        "messages":        [response],
        "awaiting_answer": True,
        **state_updates,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Lesson node — Phase 2: Validate user's answer
# ─────────────────────────────────────────────────────────────────────────────

def lesson_check_node(state: TarsState) -> dict:
    """
    Runs when awaiting_answer is True.
    Deterministically checks whether the user said the target word,
    then generates a natural-language reaction via the LLM.
    """
    llm_expert      = get_tars_expert(expert_type="tars_normal")
    current_lesson  = state.get("current_lesson", 1)
    lesson_words    = state.get("lesson_words", [])
    lesson_progress = state.get("lesson_progress", 0)
    target_word     = state.get("target_word", "")
    last_user_msg   = (state["messages"][-1].content or "").strip()

    # Load vocab for pinyin / meaning on all words
    lesson_data = load_lesson_json(current_lesson)
    vocab_list  = lesson_data["vocabulary"]
    vocab_by_zh = {v["zh"]: v for v in vocab_list}

    target_info    = vocab_by_zh.get(target_word, {})
    target_pinyin  = target_info.get("py", "")
    target_meaning = target_info.get("es", "")

    # ── Deterministic validation ──────────────────────────────────────────────
    # Require a non-trivial response (filter empty / Whisper hallucinations)
    said_it = bool(last_user_msg) and (
        target_word in last_user_msg
        or is_phonetically_similar(target_word, last_user_msg)
    )

    state_updates: dict = {}
    next_word = next_pinyin = next_meaning = ""

    if said_it:
        lesson_progress += 1
        if lesson_progress < len(lesson_words):
            next_word     = lesson_words[lesson_progress]
            next_info     = vocab_by_zh.get(next_word, {})
            next_pinyin   = next_info.get("py", "")
            next_meaning  = next_info.get("es", "")
            feedback_type = "CORRECT_NEXT"
            state_updates = {
                "lesson_progress": lesson_progress,
                "target_word":     next_word,
                "awaiting_answer": True,   # keep waiting for the next word
            }
        else:
            feedback_type = "LESSON_COMPLETE"
            state_updates = {
                "lesson_progress": lesson_progress,
                "awaiting_answer": False,
            }
    else:
        next_word     = target_word
        next_pinyin   = target_pinyin
        next_meaning  = target_meaning
        feedback_type = "RETRY"
        state_updates = {"awaiting_answer": True}  # still waiting

    # ── Build protocol text for LLM ───────────────────────────────────────────
    lesson_vocab_str = ", ".join(lesson_words)
    protocol_text    = PROTOCOLS.get("tars_normal", "Standard operating procedures.")
    protocol_text    = protocol_text.replace("{context}", "No relevant context for this turn.")

    protocol_text += f"""

### RESULTADO DE VALIDACIÓN
Vocabulario de la lección: {lesson_vocab_str}
Palabra que el usuario debía decir: **{target_word}** ({target_pinyin}) — "{target_meaning}"
Lo que respondió el usuario: "{last_user_msg}"
Resultado del sistema: **{feedback_type}**
"""

    if feedback_type == "CORRECT_NEXT":
        protocol_text += f"""
INSTRUCCIÓN: Felicita brevemente al usuario por haber dicho correctamente **{target_word}**.
Luego presenta la siguiente palabra: **{next_word}** ({next_pinyin}) — "{next_meaning}".
Pídele que la repita. NO avances hasta que lo diga.
"""
    elif feedback_type == "RETRY":
        protocol_text += f"""
INSTRUCCIÓN: El usuario no dijo la palabra correcta. Anímalo con amabilidad.
Repite la palabra objetivo: **{target_word}** ({target_pinyin}) — "{target_meaning}".
Pídele que lo intente de nuevo. NO avances.
"""
    elif feedback_type == "LESSON_COMPLETE":
        protocol_text += """
INSTRUCCIÓN: ¡El usuario completó todas las palabras de la lección! Felicítalo con entusiasmo.
"""

    rag_ctx = _build_rag_context(last_user_msg, current_lesson)
    if rag_ctx:
        protocol_text += f"\n\n### CONTEXTO ADICIONAL\n{rag_ctx}"

    protocol_text = _append_memory_context(state.get("user_id"), last_user_msg, protocol_text)
    protocol_text = _append_style_examples(last_user_msg, feedback_type, protocol_text)

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    response = dynamic_chain.invoke(state)

    return {"messages": [response], **state_updates}


# ─────────────────────────────────────────────────────────────────────────────
# General actor node (non-lesson modes: roleplay, etc.)
# ─────────────────────────────────────────────────────────────────────────────

def actor_node(state: TarsState) -> dict:
    """The dynamic brain for non-lesson modes."""
    expert_type   = state.get("user_mode", "tars_roleplay")
    llm_expert    = get_tars_expert(expert_type=expert_type)
    protocol_text = PROTOCOLS.get(expert_type, "Standard operating procedures.")

    if expert_type == "tars_roleplay":
        char_name  = state.get("selected_role")
        user_role  = state.get("user_role", "User")
        doc_id     = state.get("selected_source")
        doc_id_int = int(doc_id) if (doc_id and str(doc_id).isdigit()) else None

        if char_name:
            persona_data = None
            if doc_id_int is not None:
                try:
                    persona_data = fetch_persona_from_db(char_name, doc_id_int)
                except ValueError:
                    pass
            else:
                persona_data = fetch_persona_from_db(char_name, None)

            if not persona_data:
                print(f"⚠️ Persona '{char_name}' not found in DB. Triggering JIT Profiling...")
                try:
                    char_fragments = retrieve_knowledge(
                        f"Who is {char_name}? Describe their personality and how they speak."
                    )
                    if char_fragments and isinstance(char_fragments, list):
                        char_fragments_str = "\n".join(
                            item.get("content", "") for item in char_fragments if isinstance(item, dict)
                        )
                    else:
                        char_fragments_str = "No specific fragments found. Rely on general knowledge."
                    persona_data = generate_persona(char_name, doc_id_int, char_fragments_str)
                except Exception as e:
                    import traceback
                    print(f"JIT Profiling failed for {char_name}: {e}")
                    traceback.print_exc()

            fmt_kwargs = dict(
                selected_role=char_name,
                user_role=user_role,
                context="{context}",
            )
            if persona_data:
                fmt_kwargs.update(
                    persona_style=persona_data.get("speech_style", "Normal"),
                    persona_traits=persona_data.get("traits", "Neutral"),
                    knowledge_limit=persona_data.get("knowledge_limit", "None"),
                    emotional_anchor=persona_data.get("emotional_anchor", "None"),
                    interaction_rules=", ".join(persona_data.get("rules", [])),
                )
            else:
                fmt_kwargs.update(
                    persona_style="Adapts to context naturally",
                    persona_traits="Follows the script",
                    knowledge_limit="General knowledge only",
                    emotional_anchor="Solving the current scene",
                    interaction_rules="Stay in character, always end with a question",
                )
            protocol_text = PROTOCOLS.get(expert_type).format(**fmt_kwargs)

        if state.get("scene_context"):
            protocol_text += f"\nSCENE CONTEXT: {state.get('scene_context')}"

    last_user_msg  = state["messages"][-1].content
    current_lesson = state.get("current_lesson")

    rag_ctx = _build_rag_context(last_user_msg, current_lesson)
    protocol_text = protocol_text.replace(
        "{context}", rag_ctx or "No relevant memories found for this interaction."
    )
    protocol_text = _append_memory_context(state.get("user_id"), last_user_msg, protocol_text)

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    response = dynamic_chain.invoke(state)

    return {"messages": [response]}


# ─────────────────────────────────────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────────────────────────────────────

workflow = StateGraph(TarsState)

workflow.add_node(ACTOR,         actor_node)
workflow.add_node(LESSON_PROMPT, lesson_prompt_node)
workflow.add_node(LESSON_CHECK,  lesson_check_node)

workflow.add_conditional_edges(START, route_lesson, {
    ACTOR:         ACTOR,
    LESSON_PROMPT: LESSON_PROMPT,
    LESSON_CHECK:  LESSON_CHECK,
})

workflow.add_edge(ACTOR,         END)
workflow.add_edge(LESSON_PROMPT, END)
workflow.add_edge(LESSON_CHECK,  END)

config = {
    "configurable": {
        "thread_id": 1
    }
}
