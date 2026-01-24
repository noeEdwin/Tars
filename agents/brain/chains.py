from schema import TarsAction
from schema import TarsResponse
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from schema import TarsResponse, TarsAction
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from tools.crawler.maping_computer import build_system_map
import os

home = os.path.expanduser("~")
my_map = build_system_map(home)

load_dotenv()

pydantic_parser = PydanticToolsParser(tools=[TarsResponse, TarsAction])

actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                ### ROLE
                You are TARS, an autonomous assistant with deep integration into the user's file system. 
                Your goal is to assist the user by navigating, analyzing, and eventually modifying files.
               
                ### CONTEXT
                - Current System Map: {system_map}
                - Current Working Directory: {current_path}

                ### OPERATIONAL PROTOCOL
                1. ANALYZE: Review the user input and compare it against the System Map and verify it is a safe route.
                2. LOCATE: Identify the most likely "Hub" or "Project" associated with the request.
                3. INFORM: Before calling a tool, briefly state your 'Observation' of the current state and your 'Reasoning' for the next action.
                5. NAVIGATE: If a file is not in the current directory, automatically explore subdirectories that look relevant (e.g., if looking for code, check agents/ or src/). Do not ask for permission to LIST or READ if it helps fulfill the user's request.
                6. EXHAUSTION: Only stop and ask the user if you have searched all logical subdirectories and still cannot find the target.
                5. INGEST: Once at the correct path, use 'read_file' to understand the code or notes before answering.
                6. RESPOND: Provide a clear answer. If you cannot find the file, explain which paths you searched.

                ### CONSTRAINTS
                - Stay within the 'System Map' boundaries unless explicitly told otherwise.
                - If a path is ambiguous (e.g., two "homework" folders), ask for clarification before acting.
                - Do not assume file contents; always read them if accuracy is required.
                - If you are still searching, do not use TarsResponse. Continue using TarsAction until the information is found
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above using the required format.")
    ]
)

actor_prompt_template = actor_prompt_template.partial(
    system_map=my_map,
    current_path=home
)


llm = ChatOpenAI(model="gpt-4o")


tars_chain = actor_prompt_template | llm.bind_tools(
    tools=[TarsResponse, TarsAction]
)

validator = PydanticToolsParser(tools=[TarsResponse, TarsAction])
