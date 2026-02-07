import sys
from pathlib import Path

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add the project root to sys.path so ChatMessage can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ChatMessage.infraestructure.tts.google_tts import send_tts_request
from RAG.save_memory import save_memory, get_db_uri
from RAG.retrieve import retrieve_knowledge
from langgraph.checkpoint.postgres import PostgresSaver
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage 
from langgraph.graph import END, START, StateGraph
from tools.crawler.execute_tools import execute_tools
from schema import TarsState, TarsAction, TarsResponse
from typing import Literal
from chains import planner_chain, PROTOCOLS, get_tars_expert, actor_prompt_template
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()
ROUTER = "router"
ACTOR = "tars_actor"
EXECUTION = "execute_tools"


def router_node(state: TarsState) -> dict:
    """Analyze the user message and assign an expert."""
    last_message = state["messages"][-1].content
    decision = planner_chain.invoke(last_message)
    return {"active_expert": decision.expert}

def actor_node(state: TarsState) -> dict:
    """The dynamic brain: Uses the expert assigned by the router."""
    expert_type = state.get("active_expert", "general")
    
    # 1. Get the specific model for this expert
    llm_expert = get_tars_expert(expert_type=expert_type)
    
    # 2. Bind the tools to this specific expert model
    tools = [TarsResponse, TarsAction]
    llm_with_tools = llm_expert.bind_tools(tools)
    
    # 3. Create the dynamic chain with the correct protocol
    protocol_text = PROTOCOLS.get(expert_type, "Standard operating procedures.")
    dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_with_tools
    
    response = dynamic_chain.invoke(state)
    return {"messages": [response]}


def tools_node(state: TarsState) -> dict:
    """The hands: Executes the filesystem actions."""
    result = execute_tools(state)
    return {"messages": result["messages"]}


def should_continue(state: TarsState) -> Literal["tools", "end"]:
    """The router: Determines if we need more actions."""
    last_message = state["messages"][-1]
    
    if not last_message.tool_calls:
        return "end"
    
    return "tools"


workflow = StateGraph(TarsState)

workflow.add_node(ACTOR, actor_node)
workflow.add_node(EXECUTION, tools_node)
workflow.add_node(ROUTER, router_node)

workflow.add_edge(START, ROUTER)
workflow.add_edge(ROUTER, ACTOR)

workflow.add_conditional_edges(
    ACTOR,
    should_continue,
    {
        "tools": EXECUTION,
        "end": END
    }
)
workflow.add_edge(EXECUTION, ACTOR)

# Configuration is defined here, but app compilation moves to main block
config = {
    "configurable": {
        "thread_id": 1
    }
}

if __name__ == "__main__":
    DB_URI = get_db_uri()
    
    # Use context manager for safe connection handling
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup() # Ensure tables exist
        app = workflow.compile(checkpointer=checkpointer)
        
        # Auto-recovery: Check if the last message was a tool call that didn't get a response
        # (This happens if the user exited/crashed the script while tools were running)
        snapshot = app.get_state(config)
        if snapshot.values and "messages" in snapshot.values:
            last_msg = snapshot.values["messages"][-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                print("System: Detected interrupted session. healing connection...")
                tool_msgs = []
                for tc in last_msg.tool_calls:
                    tool_msgs.append(
                        ToolMessage(
                            content="System: The tool execution was interrupted by the user in the previous session.",
                            tool_call_id=tc["id"]
                        )
                    )
                # Update the state to "close" the open tool calls
                app.update_state(config, {"messages": tool_msgs})

        while True:
            try:
                user_input = input("User: ")
            except KeyboardInterrupt:
                break
                
            if (user_input in ["exit", "end"]):
                break
            else:
                # Get current state to calculate offset
                snapshot = app.get_state(config)
                existing_messages = snapshot.values.get("messages", []) if snapshot.values else []
                start_len = len(existing_messages)

                save_memory("user", user_input)
                messages = [HumanMessage(content=user_input)]
                similar_messages = retrieve_knowledge(user_input)
                system_message = f"To answer the user's question, use this information which is part of the past conversation as a context:\n{similar_messages}"
                messages.insert(0, SystemMessage(content=system_message))
                result = app.invoke({
                    "messages": messages
                }, config=config)

                # Slice to get only new messages
                # start_len points to where the new user message was added.
                # using start_len: gives us [UserMessage, AI_Message, ...]
                new_messages = result["messages"][start_len:]

                for msg in new_messages:
                    handled_as_final = False
                    # Check for tool calls that are actually answers (TarsResponse)
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            if tc['name'] == 'TarsResponse':
                                final_answer = tc['args'].get('message', 'No message content')
                                print(f"AI: {final_answer}")
                                save_memory("assistant", final_answer)
                                try:
                                    send_tts_request(final_answer)
                                except Exception as e:
                                    print(f"TTS Error: {e}")
                                handled_as_final = True
                    
                    if hasattr(msg, 'content') and msg.content and msg.type == 'ai':
                        print("AI: " + msg.content)
                        try:
                            send_tts_request(msg.content)
                        except Exception as e:
                            print(f"TTS Error: {e}")