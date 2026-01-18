from typing import Annotated, Sequence
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from chains import generation_chain, reflection_chain
from typing_extensions import TypedDict

load_dotenv()

class builderState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

builder = StateGraph(builderState)

REFLECT = "reflect"
GENERATE = "generate"

def generate_node(state):
    response = generation_chain.invoke({
        "messages":state["messages"]
    })
    return {"messages":[response]}

def reflect_node(state: builderState):
    response = reflection_chain.invoke({
        "messages":state["messages"]
    })
    return {"messages":[HumanMessage(content=response.content)]}

def should_continue(state):
    if(len(state["messages"]) > 10):
        return False
    return True

builder.add_node(GENERATE, generate_node)
builder.add_node(REFLECT, reflect_node)

builder.add_edge(START, GENERATE)
builder.add_conditional_edges(
    GENERATE, 
    should_continue, 
    {
        True: REFLECT, 
        False: END          
    }
)
builder.add_edge(REFLECT, GENERATE)

app = builder.compile()

print(app.get_graph().draw_mermaid())
app.get_graph().print_ascii()
input_state = {"messages": [HumanMessage(content="Write a tweet about how amazing China is")]}
response = app.invoke(input_state)

print(response["messages"])