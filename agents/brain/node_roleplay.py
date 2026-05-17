from agents.brain.schema import TarsState
from agents.brain.protocol_builder import ProtocolBuilder, build_roleplay_protocol
from agents.dataBase.persona_db import fetch_persona_from_db
from agents.brain.identity_agent import generate_persona
from agents.RAG.retrieve import retrieve_character_context
from langchain_core.runnables import RunnableConfig
import logging
import re

logger = logging.getLogger(__name__)

async def actor_node(state: TarsState, config: RunnableConfig) -> dict:
    expert_type = state.user_mode

    if expert_type == "tars_roleplay":
        char_name = state.selected_role
        user_role = state.user_role
        doc_id = state.selected_source
        doc_id_int = int(doc_id) if (doc_id and str(doc_id).isdigit()) else None

        persona_data = None
        if char_name:
            if doc_id_int is not None:
                try:
                    persona_data = fetch_persona_from_db(char_name, doc_id_int)
                except ValueError:
                    pass
            else:
                persona_data = fetch_persona_from_db(char_name, None)

            if not persona_data:
                logger.warning("Persona '%s' not found in DB. Triggering JIT Profiling...", char_name)
                try:
                    char_fragments_str = retrieve_character_context(char_name, doc_id_int)
                    persona_data = generate_persona(char_name, doc_id_int, char_fragments_str)
                except Exception as e:
                    logger.error("JIT Profiling failed for %s: %s", char_name, e)
                    logger.debug("JIT Profiling traceback:", exc_info=True)

        protocol_text = build_roleplay_protocol(
            char_name=char_name or "",
            user_role=user_role or "User",
            persona_data=persona_data,
            scene_context=state.scene_context,
        )

        builder = ProtocolBuilder("tars_roleplay", state)
        builder.protocol_text = protocol_text
        builder.set_context(builder.protocol_text.replace("{context}", builder.protocol_text))

        last_user_msg = state.messages[-1].content
        current_lesson = state.current_lesson

        from agents.brain.context_builders import _build_rag_context, _append_memory_context
        from agents.RAG.utils import get_embedding

        query_embedding = get_embedding(last_user_msg) if last_user_msg and len(last_user_msg) > 10 else None
        rag_ctx = _build_rag_context(last_user_msg, current_lesson, query_embedding=query_embedding)
        protocol_text = protocol_text.replace(
            "{context}", rag_ctx or "No relevant memories found for this interaction."
        )
        protocol_text = _append_memory_context(state.user_id, last_user_msg, protocol_text, query_embedding=query_embedding)
        builder.protocol_text = protocol_text

        chain = builder.build_chain()
        truncated_state = builder.get_truncated_state()
        response = await chain.ainvoke(truncated_state, config=config)

        cleaned_content = re.sub(r'^\{.*?\}(?=\s*[\w\[])', '', response.content, flags=re.DOTALL).strip()
        if cleaned_content:
            response.content = cleaned_content

        return {"messages": [response]}

    else:
        builder = ProtocolBuilder(expert_type, state)
        await builder.enrich_rag(state.current_lesson)
        response = await builder.invoke(config)
        return {"messages": [response]}
