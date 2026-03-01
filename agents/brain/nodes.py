import sys
from pathlib import Path

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add the project root to sys.path so ChatMessage can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ChatMessage.infraestructure.tts.google_tts import speak_mixed_text
from RAG.retrieve import retrieve_knowledge
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
TRANSLATOR = "translator_node"


def actor_node(state: TarsState) -> dict:
    """The dynamic brain: Uses the expert assigned by the user."""
    expert_type = state.get("user_mode", "tars_roleplay")
    
    # 1. Get the specific model for this expert
    llm_expert = get_tars_expert(expert_type=expert_type)
    

    # 3. Create the dynamic chain with the correct protocol
    protocol_text = PROTOCOLS.get(expert_type, "Standard operating procedures.")
    
    # Inject selected role if in roleplay mode
    if expert_type == "tars_roleplay":
        if state.get("selected_role"):
            protocol_text += f"\n\nCURRENT ROLE: {state.get('selected_role')}"
        if state.get("user_role"):
            protocol_text += f"\nUSER ROLE: {state.get('user_role')}"
        if state.get("scene_context"):
            protocol_text += f"\nSCENE CONTEXT: {state.get('scene_context')}"


    # RAG INTEGRATION (Conditional to save latency)
    last_user_msg = state["messages"][-1].content
    # Only retrieve if message is substantial (not just "ok" or "hello")
    if len(last_user_msg) > 10:
        try:
            # We assume retrieve_knowledge handles the vector store query
            context_docs = retrieve_knowledge(last_user_msg)
            if context_docs:
                protocol_text += f"\n\n### RELEVANT MEMORY/CONTEXT:\n{context_docs}\n(Use this information if relevant to the user's query)"
        except Exception as e:
            print(f"RAG Error (Ignored): {e}")
        
    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
    
    response = dynamic_chain.invoke(state)
    
    if response.content:
        import threading
        # We no longer filter for just Chinese. We want the full response with mixed voices.
        threading.Thread(target=speak_mixed_text, args=(response.content,)).start()
    

    return {"messages": [response]}


def translator_node(state: TarsState) -> dict:
    """
    Post-processes TARS output to ensure it follows the format:
    Hanzi (Pinyin) 
    Translation (Spanish)
    """
    last_message = state["messages"][-1]
    

    original_text = last_message.content
    if not original_text:
        return {}
            
    # Use a fast model for this pure formatting task
    translator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    system_prompt = """
    You are a linguistic formatter. Your job is to take the input text (which may be Chinese, English, or mixed) and format it for a Spanish speaker learning Chinese.
        
        RULES:
        1. If the text contains Chinese sentences:
           - Provide the original Hanzi.
           - Provide the Pinyin (with tone marks) below it.
           - Provide the Spanish translation below that.
        2. If the text is purely English/Spanish or Code:
           - Leave it mostly as is, but ensure any explained terms have Pinyin/Spanish.
        3. OUTPUT FORMAT:
           [Hanzi]
           (Pinyin)
           [Spanish Translation]
           
        4. Do NOT verify the facts, just format the language.
    """
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=original_text)
    ]
        
    response = translator_llm.invoke(messages)
        
        # Overwrite the previous message to avoid duplication in history/frontend
        # We use the same ID as the last message so LangGraph's add_messages strategy updates it.
    new_msg = AIMessage(id=last_message.id, content=response.content)
        
    return {"messages": [new_msg]}



workflow = StateGraph(TarsState)

workflow.add_node(ACTOR, actor_node)
workflow.add_node(TRANSLATOR, translator_node)

workflow.add_edge(START, ACTOR)
workflow.add_edge(ACTOR, TRANSLATOR)
workflow.add_edge(TRANSLATOR, END)

# Configuration is defined here, but app compilation moves to main block
config = {
    "configurable": {
        "thread_id": 1
    }
}
