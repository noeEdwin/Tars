import sys
from pathlib import Path

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add the project root to sys.path so ChatMessage can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ChatMessage.infraestructure.tts.google_tts import speak_mixed_text
from RAG.retrieve import retrieve_knowledge
from dataBase.persona_db import fetch_persona_from_db
from brain.identity_agent import generate_persona
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END, START, StateGraph
from brain.schema import TarsState
from brain.chains import PROTOCOLS, get_tars_expert, actor_prompt_template
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_openai import ChatOpenAI

load_dotenv()
ACTOR = "tars_actor"


def actor_node(state: TarsState) -> dict:
    """The dynamic brain: Uses the expert assigned by the user."""
    expert_type = state.get("user_mode", "tars_roleplay")
    
    # 1. Get the specific model for this expert
    llm_expert = get_tars_expert(expert_type=expert_type)
    

    # 3. Create the dynamic chain with the correct protocol
    protocol_text = PROTOCOLS.get(expert_type, "Standard operating procedures.")
    
    # Inject selected role if in roleplay mode
    if expert_type == "tars_roleplay":
        char_name = state.get("selected_role")
        user_role = state.get("user_role", "User")
        doc_id = state.get("selected_source")
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
            
            # If not in DB, use JIT Profiling (Identity Agent)
            if not persona_data:
                print(f"⚠️ Persona '{char_name}' not found in DB. Triggering JIT Profiling...")
                try:
                    # Retrieve fragments for this specific character
                    char_fragments = retrieve_knowledge(f"Who is {char_name}? Describe their personality and how they speak.")
                    
                    if char_fragments and isinstance(char_fragments, list):
                        char_fragments_str = "\n".join([item.get('content', '') for item in char_fragments if isinstance(item, dict)])
                    else:
                        char_fragments_str = "No specific fragments found in the database. Rely on your general knowledge about this character."
                    
                    persona_data = generate_persona(char_name, doc_id_int, char_fragments_str)
                except Exception as e:
                    import traceback
                    print(f"JIT Profiling failed for {char_name} (doc_id={doc_id}): {e}")
                    traceback.print_exc()
            
            if persona_data:
                # Format the protocol using the persona variables
                protocol_text = PROTOCOLS.get(expert_type).format(
                    selected_role=char_name,
                    user_role=user_role,
                    persona_style=persona_data.get("speech_style", "Normal"),
                    persona_traits=persona_data.get("traits", "Neutral"),
                    context="{context}", # Filled later by regular RAG
                    knowledge_limit=persona_data.get("knowledge_limit", "None"),
                    emotional_anchor=persona_data.get("emotional_anchor", "None"),
                    interaction_rules=", ".join(persona_data.get("rules", []))
                )
            else:
                # Fallback if DB and JIT both fail
                protocol_text = PROTOCOLS.get(expert_type).format(
                    selected_role=char_name,
                    user_role=user_role,
                    persona_style="Adapts to context naturally",
                    persona_traits="Follows the script",
                    context="{context}",
                    knowledge_limit="General knowledge only",
                    emotional_anchor="Solving the current scene",
                    interaction_rules="Stay in character, always end with a question"
                )
                
        if state.get("scene_context"):
            protocol_text += f"\nSCENE CONTEXT: {state.get('scene_context')}"


    # RAG INTEGRATION (Conditional to save latency)
    last_user_msg = state["messages"][-1].content
    user_id = state.get("user_id")
    current_lesson = state.get("current_lesson", 1)
    
    # 4. Inject Static JSON Lesson Map ONLY for Normal Mode
    if expert_type == "tars_normal":
        from RAG.retrieve import get_lesson_plan_context, get_all_knowledge_for_lesson
        
        lesson_blueprint = get_lesson_plan_context(current_lesson)
        if lesson_blueprint:
            protocol_text += f"\n\n{lesson_blueprint}"
            
        lesson_db_knowledge = get_all_knowledge_for_lesson(current_lesson)
        if lesson_db_knowledge:
            protocol_text += f"\n{lesson_db_knowledge}"

    # LONG-TERM VECTOR MEMORY (Isolated by user)
    memory_context = ""
    if user_id and len(last_user_msg) > 5:
        from RAG.save_memory import retrieve_user_memory
        try:
            memories = retrieve_user_memory(int(user_id), last_user_msg, limit=3)
            if memories:
                memory_context = "\n=== RELEVANT PAST MEMORIES ===\n" + "\n".join(memories) + "\n==============================\n"
        except Exception as e:
            print(f"Memory Retrieval Error: {e}")

    # Only retrieve if message is substantial (not just "ok" or "hello")
    if len(last_user_msg) > 10:
        try:
            # We assume retrieve_knowledge handles the vector store query
            context_docs = retrieve_knowledge(last_user_msg, current_lesson=current_lesson)
            if context_docs:
                if isinstance(context_docs, list):
                    formatted_docs = []
                    for item in context_docs:
                        if isinstance(item, dict):
                            # Default handler for generic nodes
                            if 'content' in item:
                                formatted_docs.append(f"- {item.get('content', '')}")
                            # New handler for HSK Grammar Base
                            elif 'contenido_zh' in item:
                                zh = item.get('contenido_zh', '')
                                pinyin = item.get('pinyin', '')
                                trad = item.get('traduccion_es', '')
                                pos = item.get('pos', '')
                                grammar = item.get('grammar_ref', '')
                                
                                node_str = f"- {zh} ({pinyin}) - Significado: {trad}"
                                if pos:
                                    node_str += f", POS: {pos}"
                                if grammar:
                                    node_str += f", Regla HSK: {grammar}"
                                    
                                formatted_docs.append(node_str)
                                
                    context_docs = "\n".join(formatted_docs)
                protocol_text = protocol_text.replace("{context}", context_docs)
            else:
                protocol_text = protocol_text.replace("{context}", "No relevant memories found for this interaction.")
        except Exception as e:
            print(f"RAG Error (Ignored): {e}")
            
    if memory_context:
        protocol_text += f"\n\n{memory_context}"
        
    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    
    response = dynamic_chain.invoke(state)
    
    if response.content:
        import threading
        # We no longer filter for just Chinese. We want the full response with mixed voices.
        threading.Thread(target=speak_mixed_text, args=(response.content,)).start()
    

    return {"messages": [response]}


workflow = StateGraph(TarsState)

workflow.add_node(ACTOR, actor_node)

workflow.add_edge(START, ACTOR)
workflow.add_edge(ACTOR, END)

# Configuration is defined here, but app compilation moves to main block
config = {
    "configurable": {
        "thread_id": 1
    }
}
