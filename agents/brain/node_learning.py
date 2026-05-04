from brain.schema import TarsState
from brain.chains import PROTOCOLS, get_tars_expert, actor_prompt_template
from brain.utils import load_lesson_json, is_phonetically_similar
from brain.context_builders import _build_rag_context, _append_memory_context
from brain.personality_rag import append_style_examples
from langchain_core.runnables import RunnableConfig

async def lesson_prompt_node(state: TarsState, config: RunnableConfig) -> dict:
    import time
    t_n = time.time()
    print(f"[TIMER NODE] 1. lesson_prompt_node started")
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

    last_user_msg = (state["messages"][-1].content if state.get("messages") else "")
    print(f"[TIMER NODE] 2. Pre-RAG listo: {time.time() - t_n:.2f}s")
    
    import asyncio
    mem_ctx = await asyncio.to_thread(_append_memory_context, state.get("user_id"), last_user_msg, "")
    protocol_text += mem_ctx
    
    protocol_text = append_style_examples(last_user_msg, "INTRODUCE", protocol_text)
    print(f"[TIMER NODE] 3. RAG finalizado: {time.time() - t_n:.2f}s")

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    print(f"[TIMER NODE] 4. Llamando a OpenAI ainvoke...")
    t_llm = time.time()
    response = await dynamic_chain.ainvoke(state, config=config)
    print(f"[TIMER NODE] 5. Fin LLM ainvoke: {time.time() - t_llm:.2f}s")

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

    import asyncio
    rag_task = asyncio.to_thread(_build_rag_context, last_user_msg, current_lesson)
    mem_task = asyncio.to_thread(_append_memory_context, state.get("user_id"), last_user_msg, "")
    rag_ctx, mem_ctx = await asyncio.gather(rag_task, mem_task)
    
    if rag_ctx:
        protocol_text += f"\n\n### CONTEXTO ADICIONAL\n{rag_ctx}"
    protocol_text += mem_ctx
    protocol_text = append_style_examples(last_user_msg, feedback_type, protocol_text)

    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    response = await dynamic_chain.ainvoke(state, config=config)

    return {"messages": [response], **state_updates}