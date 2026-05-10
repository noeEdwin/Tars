from RAG.retrieve import retrieve_knowledge
from RAG.save_memory import retrieve_user_memory

def _build_rag_context(last_user_msg: str, current_lesson: int | None, query_embedding: list[float] = None) -> str:
    """Return a formatted RAG context string, or empty string on error."""
    if not last_user_msg or len(last_user_msg) <= 10:
        return ""
    try:
        context_docs = retrieve_knowledge(last_user_msg, current_lesson=current_lesson, query_embedding=query_embedding)
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

def _append_memory_context(user_id, last_user_msg: str, protocol_text: str, query_embedding: list[float] = None) -> str:
    """Fetch user long-term memories and append to protocol_text."""
    if not user_id or len(last_user_msg) <= 5:
        return protocol_text
    try:
        memories = retrieve_user_memory(int(user_id), last_user_msg, limit=3, query_embedding=query_embedding)
        if memories:
            memory_context = "\n=== RELEVANT PAST MEMORIES ===\n" + "\n".join(memories) + "\n==============================\n"
            protocol_text += f"\n\n{memory_context}"
    except Exception as e:
        print(f"Memory Retrieval Error: {e}")
    return protocol_text
