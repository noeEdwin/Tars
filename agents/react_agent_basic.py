import datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_tavily import TavilySearch

load_dotenv()

llm = ChatOpenAI(model_name="gpt-4")

search_tool = TavilySearch(max_results=3, search_depth="basic")

@tool
def get_system_time(format: str = "%Y-%m-%d %H:%M:%S"):
    """Returns the current system time formatted according to the given format string."""
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime(format)
    return formatted_time

tools = [search_tool, get_system_time]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a specialist assistant that helps users find up-to-date information using the internet. Use the provided search tool to look up recent information as needed to answer user queries accurately.",
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "When was SpaceX's last launch and how many days ago was that?"}]}
)
"""print(response["messages"][-1].content)"""

for chunk in agent.stream(  
    {"messages": [{"role": "user", "content": "When was SpaceX's last launch and how many days ago was that?"}]},
    stream_mode="updates",
):
    for step, data in chunk.items():
        print(f"step: {step}")
        print(f"content: {data['messages'][-1].content_blocks}")