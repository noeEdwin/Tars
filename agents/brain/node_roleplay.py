from brain.schema import TarsState
from brain.chains import PROTOCOLS, get_tars_expert, actor_prompt_template
from dataBase.persona_db import fetch_persona_from_db
from brain.identity_agent import generate_persona
from RAG.retrieve import retrieve_knowledge
from brain.context_builders import _build_rag_context, _append_memory_context
from langchain_core.runnables import RunnableConfig

async def actor_node(state: TarsState, config: RunnableConfig) -> dict:
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
    response = await dynamic_chain.ainvoke(state, config=config)

    return {"messages": [response]}