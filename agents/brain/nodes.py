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
from tools.crawler.execute_tools import execute_tools
from schema import TarsState, TarsAction, TarsResponse
from typing import Literal
from chains import planner_chain, PROTOCOLS, get_tars_expert, actor_prompt_template
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_openai import ChatOpenAI

load_dotenv()
ROUTER = "router"
ACTOR = "tars_actor"
EXECUTION = "execute_tools"
TRANSLATOR = "translator_node"


def router_node(state: TarsState) -> dict:
    """Analyze the user message and assign an expert."""
    # 1. Explicit Mode Check (from Frontend)
    user_mode = state.get("user_mode")
    if user_mode and user_mode in PROTOCOLS:
        return {"active_expert": user_mode}

    # 2. Sticky Routing (Stay in Tars modes unless exit)
    current_expert = state.get("active_expert", "")
    last_content = state["messages"][-1].content.lower()
    
    # Simple exit keywords to break the sticky mode
    exit_keywords = ["exit", "quit", "menu", "stop", "change mode", "salir", "menu"]
    
    if current_expert in ["tars_roleplay", "tars_engineer", "tars_sales"]:
        if not any(keyword in last_content for keyword in exit_keywords):
            return {"active_expert": current_expert}
        
    # 3. Default Router (LLM)
    decision = planner_chain.invoke(last_content)
    
    expert = decision.expert
        
    return {"active_expert": expert}

def actor_node(state: TarsState) -> dict:
    """The dynamic brain: Uses the expert assigned by the router."""
    expert_type = state.get("active_expert", "general")
    
    # 1. Get the specific model for this expert
    llm_expert = get_tars_expert(expert_type=expert_type)
    
    # 2. Bind the tools to this specific expert model
    # LATENCY OPTIMIZATION: Tars Roleplay should just chat. Tools add overhead.
    if expert_type in ["tars_roleplay", "tars_engineer", "tars_sales"]:
        llm_with_tools = llm_expert # No tools
    else:
        tools = [TarsResponse, TarsAction]
        llm_with_tools = llm_expert.bind_tools(tools)
    
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

    # Inject User Info constraints if available
    user_info = state.get("user_info")
    if user_info:
        protocol_text += f"\n\n### USER PROFILE\n"
        protocol_text += f"You are the Chinese tutor for {user_info.get('username', 'the user')}. "
        protocol_text += f"Adjust your language to an HSK {user_info.get('hsk_level', 1)} level. "
        protocol_text += f"The user is interested in {user_info.get('interest_area', 'general topics')}, try to use related examples."


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
        
    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_with_tools
    
    response = dynamic_chain.invoke(state)
    
    # 4. Asynchronous TTS (Fire and Forget)
    # We use the new mixed-language support
    # 4. Asynchronous TTS (Fire and Forget)
    # We use the new mixed-language support
    if response.content:
        import threading
        # We no longer filter for just Chinese. We want the full response with mixed voices.
        threading.Thread(target=speak_mixed_text, args=(response.content,)).start()
    
    # Also handle TarsResponse tool calls if present
    messages_to_return = [response]
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc.get("name") == "TarsResponse":
                msg = tc.get("args", {}).get("message")
                if msg:
                     import threading
                     threading.Thread(target=speak_mixed_text, args=(msg,)).start()
                # Inject a dummy ToolMessage to satisfy OpenAI API for the next turn
                messages_to_return.append(
                    ToolMessage(
                        content="TarsResponse executed successfully.",
                        tool_call_id=tc["id"]
                    )
                )

    return {"messages": messages_to_return}


def tools_node(state: TarsState) -> dict:
    """The hands: Executes the filesystem actions."""
    result = execute_tools(state)
    return {"messages": result["messages"]}


def translator_node(state: TarsState) -> dict:
    """
    Post-processes TARS output to ensure it follows the format:
    Hanzi (Pinyin) 
    Translation (Spanish)
    """
    last_message = state["messages"][-1]
    
    # Only process legitimate text responses (not tool calls)
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
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
        
    return {}


def should_continue(state: TarsState) -> Literal["tools", "translator", "end"]:
    """The router: Determines if we need more actions."""
    last_message = state["messages"][-1]
    active_expert = state.get("active_expert", "")
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Check if it's TarsResponse (Final Answer)
        for tc in last_message.tool_calls:
            if tc.get("name") == "TarsResponse":
                # If we were in Tars Roleplay, we are done (formatting is done by actor)
                if active_expert.startswith("tars_"):
                    return "end"
                return "end" # Or translator? Usually general -> end

        return "tools"
    
    # If done, determine output path
    active_expert = state.get("active_expert", "")
    
    # LATENCY OPTIMIZATION:
    if active_expert.startswith("tars_"):
        return "end"
        
    return "end"


workflow = StateGraph(TarsState)

workflow.add_node(ACTOR, actor_node)
workflow.add_node(EXECUTION, tools_node)
workflow.add_node(ROUTER, router_node)
workflow.add_node(TRANSLATOR, translator_node)

workflow.add_edge(START, ROUTER)
workflow.add_edge(ROUTER, ACTOR)

workflow.add_conditional_edges(
    ACTOR,
    should_continue,
    {
        "tools": EXECUTION,
        "translator": TRANSLATOR,
        "end": END
    }
)
workflow.add_edge(EXECUTION, ACTOR)
workflow.add_edge(TRANSLATOR, END)

# Configuration is defined here, but app compilation moves to main block
config = {
    "configurable": {
        "thread_id": 1
    }
}
