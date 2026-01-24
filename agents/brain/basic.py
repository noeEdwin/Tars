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

load_dotenv()

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
    
    if len(state["messages"]) > 15:
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

app = workflow.compile()

input_state = {
    "messages": [HumanMessage(content="Find my Tars project and tell me what's in chains.py")],
}

response = app.invoke(input_state)
print(response["messages"][-1].content)