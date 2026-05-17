from agents.brain.schema import TarsState
from agents.brain.protocol_builder import ProtocolBuilder, build_lesson_introduce_protocol, build_lesson_check_protocol
from agents.brain.utils import load_lesson_json, is_phonetically_similar
from langchain_core.runnables import RunnableConfig
import logging
import time

logger = logging.getLogger(__name__)

async def lesson_prompt_node(state: TarsState, config: RunnableConfig) -> dict:
    t_n = time.time()
    logger.debug("[TIMER NODE] 1. lesson_prompt_node started")

    current_lesson = state.current_lesson
    lesson_data = load_lesson_json(current_lesson)
    vocab_list = lesson_data["vocabulary"]
    vocab_by_zh = {v["zh"]: v for v in vocab_list}

    lesson_words = [v["zh"] for v in vocab_list]
    lesson_progress = state.lesson_progress
    if lesson_progress >= len(lesson_words):
        lesson_progress = 0
    target_word = state.target_word
    if not target_word or target_word not in lesson_words:
        target_word = lesson_words[lesson_progress]

    start = max(0, lesson_progress - 2)
    end = min(len(lesson_words), lesson_progress + 3)
    nearby_words = lesson_words[start:end]
    lesson_vocab_str = ", ".join(nearby_words)
    target_info = vocab_by_zh.get(target_word, {})
    target_pinyin = target_info.get("py", "")
    target_meaning = target_info.get("es", "")

    logger.debug("[TIMER NODE] 2. Pre-RAG ready: %.2fs", time.time() - t_n)

    builder = ProtocolBuilder("tars_normal", state)
    builder.append(build_lesson_introduce_protocol(
        current_lesson=current_lesson,
        target_word=target_word,
        target_pinyin=target_pinyin,
        target_meaning=target_meaning,
        lesson_vocab_str=lesson_vocab_str,
        lesson_progress=lesson_progress,
        total_words=len(lesson_words),
    ))
    await builder.enrich_rag(current_lesson)
    builder.enrich_style("INTRODUCE")
    logger.debug("[TIMER NODE] 3. RAG completed: %.2fs", time.time() - t_n)

    logger.debug("[TIMER NODE] 4. Calling OpenAI ainvoke...")
    t_llm = time.time()
    response = await builder.invoke(config)
    logger.debug("[TIMER NODE] 5. LLM ainvoke completed: %.2fs", time.time() - t_llm)

    return {
        "messages":        [response],
        "awaiting_answer": True,
        "lesson_words":    lesson_words,
        "lesson_progress": lesson_progress,
        "target_word":     target_word,
    }

async def lesson_check_node(state: TarsState, config: RunnableConfig) -> dict:
    current_lesson = state.current_lesson
    lesson_progress = state.lesson_progress
    target_word = state.target_word or ""
    last_user_msg = (state.messages[-1].content or "").strip()

    lesson_data = load_lesson_json(current_lesson)
    vocab_list = lesson_data["vocabulary"]
    lesson_words = [v["zh"] for v in vocab_list]
    vocab_by_zh = {v["zh"]: v for v in vocab_list}

    target_info = vocab_by_zh.get(target_word, {})
    target_pinyin = target_info.get("py", "")
    target_meaning = target_info.get("es", "")

    said_it = bool(last_user_msg) and (
        target_word in last_user_msg
        or target_pinyin in last_user_msg
        or is_phonetically_similar(target_word, last_user_msg)
    )

    next_word = next_pinyin = next_meaning = ""
    if said_it:
        lesson_progress += 1
        if lesson_progress < len(lesson_words):
            next_word = lesson_words[lesson_progress]
            next_info = vocab_by_zh.get(next_word, {})
            next_pinyin = next_info.get("py", "")
            next_meaning = next_info.get("es", "")
            feedback_type = "CORRECT_NEXT"
        else:
            feedback_type = "LESSON_COMPLETE"
    else:
        next_word = target_word
        next_pinyin = target_pinyin
        next_meaning = target_meaning
        feedback_type = "RETRY"

    start = max(0, lesson_progress - 2)
    end = min(len(lesson_words), lesson_progress + 3)
    nearby_words = lesson_words[start:end]
    lesson_vocab_str = ", ".join(nearby_words)

    builder = ProtocolBuilder("tars_normal", state)
    builder.append(build_lesson_check_protocol(
        current_lesson=current_lesson,
        target_word=target_word,
        target_pinyin=target_pinyin,
        target_meaning=target_meaning,
        next_word=next_word,
        next_pinyin=next_pinyin,
        next_meaning=next_meaning,
        last_user_msg=last_user_msg,
        feedback_type=feedback_type,
        lesson_vocab_str=lesson_vocab_str,
    ))
    await builder.enrich_rag(current_lesson)
    builder.enrich_style(feedback_type)

    response = await builder.invoke(config)

    state_updates = {
        "awaiting_answer": True,
    }
    if feedback_type == "CORRECT_NEXT":
        state_updates["lesson_progress"] = lesson_progress
        state_updates["target_word"] = next_word
    elif feedback_type == "LESSON_COMPLETE":
        state_updates["lesson_progress"] = lesson_progress
        state_updates["awaiting_answer"] = False

    return {"messages": [response], **state_updates}
