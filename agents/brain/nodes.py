import sys
from pathlib import Path

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from chains import tars_chain
from tools.crawler.execute_tools import execute_tools
from schema import TarsState
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()

sqlite_conn = sqlite3.connect("checkpoint.sqlite", check_same_thread=False )

memory = SqliteSaver(sqlite_conn)

ACTOR = "tars_actor"
EXECUTION = "execute_tools"

def actor_node(state: TarsState) -> dict:
    """The brain: Decides what to do next."""
    response = tars_chain.invoke(state)
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

workflow.add_edge(START, ACTOR)


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
    user_input = input("User: ")
    if (user_input in ["exit", "end"]):
        break
    else:
        result = app.invoke({
            "messages":[HumanMessage(content=user_input)]
        }, config=config)

        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content and msg.type == 'ai':
                print("AI: " + msg.content)