from agents.brain.schema import TarsAction
from agents.brain.schema import TarsResponse
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from schema import TarsResponse, TarsAction
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

pydantic_parser = PydanticToolsParser(tools=[TarsResponse, TarsAction])

actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "System",
            """
                ### ROLE
                You are TARS, an autonomous assistant with deep integration into the user's file system. 
                Your goal is to assist the user by navigating, analyzing, and eventually modifying files.
               
                ### CONTEXT
                - Current System Map: {system_map}
                - Current Working Directory: {current_path}
                - Conversation History: {history}

                ### OPERATIONAL PROTOCOL
                1. INPUT: {first_instruction}
                2. ANALYZE: Review the user input and compare it against the System Map.
                3. LOCATE: Identify the most likely "Hub" or "Project" associated with the request.
                4. INFORM: Before calling a tool, briefly state your 'Observation' of the current state and your 'Reasoning' for the next action.
                5. NAVIGATE: If you are not in the correct directory, use the 'list_files' tool to verify the contents of the suspected path.
                6. INGEST: Once at the correct path, use 'read_file' to understand the code or notes before answering.
                7. RESPOND: Provide a clear answer. If you cannot find the file, explain which paths you searched.

                ### CONSTRAINTS
                - Stay within the 'System Map' boundaries unless explicitly told otherwise.
                - If a path is ambiguous (e.g., two "homework" folders), ask for clarification before acting.
                - Do not assume file contents; always read them if accuracy is required.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above using the required format.")
    ]
)

llm = ChatOpenAI(model="gpt-4o")


tars_chain = actor_prompt_template | llm.bind_tools(
    tools=[TarsResponse, TarsAction], tool_choice=['TarsResponse', 'TarsAction']
)

validator = PydanticToolsParser(tools=[TarsResponse, TarsAction])
