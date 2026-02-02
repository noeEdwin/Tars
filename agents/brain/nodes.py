import sys
from pathlib import Path

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from tools.crawler.execute_tools import execute_tools
from schema import TarsState, TarsAction, TarsResponse
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from chains import planner_chain, PROTOCOLS, get_tars_expert, actor_prompt_template

load_dotenv()

sqlite_conn = sqlite3.connect("checkpoint.sqlite", check_same_thread=False )

memory = SqliteSaver(sqlite_conn)


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
    llm_expert = get_tars_expert()
    
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

app = workflow.compile(checkpointer=memory)

config = {
    "configurable": {
        "thread_id":1
    }
}


if __name__ == "__main__":
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
            result = app.invoke({
                "messages":[HumanMessage(content=user_input)]
            }, config=config)


            for msg in result["messages"]:
                if hasattr(msg, 'content') and msg.content and msg.type == 'ai':
                    print("AI: " + msg.content)
                
                # Check for tool calls that are actually answers (TarsResponse)
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc['name'] == 'TarsResponse':
                            print(f"AI: {tc['args'].get('message', 'No message content')}")