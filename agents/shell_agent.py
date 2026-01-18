from langchain_community.tools import ShellTool
from langchain.agents import create_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

shell_tool = ShellTool()
tools = [shell_tool]

system_message = (
    "You are a precise technical assistant. Use the shell tool ONLY to execute "
    "commands necessary for the user's specific request. Focus on data retrieval."
)

agent = create_agent(
    model=llm, 
    tools=tools, 
    system_prompt=system_message
)

"""response = agent.invoke(
    {
    "role": "user",
    "content": (
        "Download the README here and identify the link for LangChain tutorials: "
        "https://raw.githubusercontent.com/langchain-ai/langchain/master/README.md"
    ),
})"""

for chunk in agent.stream(  
    {"messages": [{
        "role": "user",
        "content": (
        "Download the README here and identify the link for LangChain tutorials: "
        "https://raw.githubusercontent.com/langchain-ai/langchain/master/README.md"
    )}]},
    stream_mode="updates",
):
    for step, data in chunk.items():
        print(f"step: {step}")
        print(f"content: {data['messages'][-1].content_blocks}")