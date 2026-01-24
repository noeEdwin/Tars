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
                1. ANALYZE: Review the user input and the current folder contents and verify it is a safe route.
                2. LOCATE: Identify the most likely "Hub" or "Project" associated with the request.
                3. SCAN (Shallow): Use 'list_files' to see what is in the current directory.
                4. DRILL (Deep): 
                   - 'list_files' ONLY shows the surface. It does NOT show contents of subfolders.
                   - If you see a relevant directory (marked [DIR]), you MUST use 'list_files' on that new path to see inside it.
                   - Example: If looking for 'chains.py' and you see '[DIR] agents', your NEXT action MUST be to LIST 'agents'.                
                5. PERSIST: Do NOT use TarsResponse to say "not found" until you have drilled down into ALL relevant subdirectories (e.g., agents/brain/, agents/tools/).
                6. READ: Only when you see the actual '[FILE] chains.py', use 'read_code'.
                7. ANSWER: Present the findings.

                ### CONSTRAINTS
                - Stay within the 'System Map' boundaries unless explicitly told otherwise.
                - If a path is ambiguous (e.g., two "homework" folders), ask for clarification before acting.
                - Do not assume file contents; always read them if accuracy is required.
                - If you are still searching, do not use TarsResponse. Continue using TarsAction until the information is found
                - When using UPDATE, be careful with 'mode'. Use 'append' for adding logs/comments, but 'overwrite' if refactoring code.
                - Do NOT use 'append' if you are providing the full file content; that will duplicate the code.
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
