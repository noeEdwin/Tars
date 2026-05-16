from agents.brain.schema import TarsState
from agents.brain.chains import PROTOCOLS, get_tars_expert, actor_prompt_template
from agents.brain.utils import load_lesson_json, is_phonetically_similar
from agents.brain.context_builders import _build_rag_context, _append_memory_context
from agents.brain.personality_rag import append_style_examples
from agents.brain.history import truncate_messages
from agents.RAG.utils import get_embedding
from langchain_core.runnables import RunnableConfig
import logging
import time

logger = logging.getLogger(__name__)

async def lesson_prompt_node(state: TarsState, config: RunnableConfig) -> dict:
    t_n = time.time()
    logger.debug("[TIMER NODE] 1. lesson_prompt_node started")
    llm_expert      = get_tars_expert(expert_type="tars_normal")
    current_lesson  = state.get("current_lesson", 1)

    lesson_data = load_lesson_json(current_lesson)
    vocab_list  = lesson_data["vocabulary"]
    vocab_by_zh = {v["zh"]: v for v in vocab_list}

    state_updates: dict = {}

    
    lesson_words    = [v["zh"] for v in vocab_list]
    lesson_progress = state.get("lesson_progress", 0)
    if lesson_progress >= len(lesson_words):
        lesson_progress = 0
    target_word = state.get("target_word")
    if not target_word or target_word not in lesson_words:
        target_word = lesson_words[lesson_progress]
    state_updates.update({
            "lesson_words":    lesson_words,
            "lesson_progress": lesson_progress,
            "target_word":     target_word,
    })

    start = max(0, lesson_progress - 2)
    end = min(len(lesson_words), lesson_progress + 3)
    nearby_words = lesson_words[start:end]
    lesson_vocab_str = ", ".join(nearby_words)
    target_info      = vocab_by_zh.get(target_word, {})
    target_pinyin    = target_info.get("py", "")
    target_meaning   = target_info.get("es", "")

    protocol_text = PROTOCOLS.get("tars_normal", "Standard operating procedures.")
    protocol_text = protocol_text.replace("{context}", "No relevant context for this turn.")
    protocol_text += f"""

### 🔴 REGLA OBLIGATORIA: ESTRUCTURA DE 3 PALABRAS
NO pidas la palabra aislada "{target_word}". DEBES crear una frase de 3 palabras usando:
- Si es PRONOMBRE: Sujeto + 是 + [Rol] → Ej: 我是老师
- Si es SUSTANTIVO: 这是 + [Objeto] → Ej: 这是书
- Si es NÚMERO: [Sujeto] + 有 + [Número] + 个 → Ej: 我有三个
- Si es VERBO: Sujeto + Verbo + Objeto → Ej: 我喝茶

### LECCIÓN EN CURSO — ACCIÓN: INTRODUCIR PALABRA
Lección {current_lesson} | Vocabulario: {lesson_vocab_str}
Progreso: {lesson_progress}/{len(lesson_words)} palabras completadas
Palabra objetivo: **{target_word}** ({target_pinyin}) — "{target_meaning}"

INSTRUCCIÓN OBLIGATORIA:
1. Primero pregunta brevemente "¿Estás listo?" o "¿Comenzamos?".
2. Crea una frase de 3 palabras con **{target_word}** siguiendo la REGLA OBLIGATORIA arriba.
3. Presenta la frase completa y pide al usuario que la repita.
4. NO avances hasta que el usuario diga la frase completa.
"""

    last_user_msg = (state["messages"][-1].content if state.get("messages") else "")
    logger.debug("[TIMER NODE] 2. Pre-RAG ready: %.2fs", time.time() - t_n)

    import asyncio
    query_embedding = get_embedding(last_user_msg) if last_user_msg and len(last_user_msg) > 10 else None
    mem_ctx = await asyncio.to_thread(_append_memory_context, state.get("user_id"), last_user_msg, "", query_embedding)
    protocol_text += mem_ctx
    
    protocol_text = append_style_examples(last_user_msg, "INTRODUCE", protocol_text)
    logger.debug("[TIMER NODE] 3. RAG completed: %.2fs", time.time() - t_n)

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    logger.debug("[TIMER NODE] 4. Calling OpenAI ainvoke...")
    t_llm = time.time()
    truncated_state = {**state, "messages": truncate_messages(state["messages"])}
    response = await dynamic_chain.ainvoke(truncated_state, config=config)
    logger.debug("[TIMER NODE] 5. LLM ainvoke completed: %.2fs", time.time() - t_llm)

    return {
        "messages":        [response],
        "awaiting_answer": True,
        **state_updates,
    }

async def lesson_check_node(state: TarsState, config: RunnableConfig) -> dict:
    llm_expert      = get_tars_expert(expert_type="tars_normal")
    current_lesson  = state.get("current_lesson", 1)
    lesson_progress = state.get("lesson_progress", 0)
    target_word     = state.get("target_word", "")
    last_user_msg   = (state["messages"][-1].content or "").strip()

    lesson_data = load_lesson_json(current_lesson)
    vocab_list  = lesson_data["vocabulary"]
    lesson_words = [v["zh"] for v in vocab_list]  
    vocab_by_zh = {v["zh"]: v for v in vocab_list}

    target_info    = vocab_by_zh.get(target_word, {})
    target_pinyin  = target_info.get("py", "")
    target_meaning = target_info.get("es", "")

    said_it = bool(last_user_msg) and (
        target_word in last_user_msg
        or target_pinyin in last_user_msg
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
                "awaiting_answer": True,
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
        state_updates = {"awaiting_answer": True}

    start = max(0, lesson_progress - 2)
    end = min(len(lesson_words), lesson_progress + 3)
    nearby_words = lesson_words[start:end]
    lesson_vocab_str = ", ".join(nearby_words)
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
Luego crea una frase de 3 palabras con la siguiente palabra: **{next_word}** ({next_pinyin}) — "{next_meaning}".
Usa la regla de 3 palabras del PROTOCOL. Pídele que repita la frase completa. NO avances hasta que lo diga.
"""
    elif feedback_type == "RETRY":
        protocol_text += f"""
INSTRUCCIÓN: El usuario no dijo la palabra correctamente. Anímalo con amabilidad.
Crea nuevamente una frase de 3 palabras con: **{target_word}** ({target_pinyin}) — "{target_meaning}".
Pídele que repita la frase completa. NO avances.
"""
    elif feedback_type == "LESSON_COMPLETE":
        protocol_text += """
INSTRUCCIÓN: ¡El usuario completó todas las palabras de la lección! Felicítalo con entusiasmo.
"""

    import asyncio
    query_embedding = get_embedding(last_user_msg) if last_user_msg and len(last_user_msg) > 10 else None
    rag_task = asyncio.to_thread(_build_rag_context, last_user_msg, current_lesson, query_embedding)
    mem_task = asyncio.to_thread(_append_memory_context, state.get("user_id"), last_user_msg, "", query_embedding)
    rag_ctx, mem_ctx = await asyncio.gather(rag_task, mem_task)
    
    if rag_ctx:
        protocol_text += f"\n\n### CONTEXTO ADICIONAL\n{rag_ctx}"
    protocol_text += mem_ctx
    protocol_text = append_style_examples(last_user_msg, feedback_type, protocol_text)

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    truncated_state = {**state, "messages": truncate_messages(state["messages"])}
    response = await dynamic_chain.ainvoke(truncated_state, config=config)

    return {"messages": [response], **state_updates}