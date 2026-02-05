from schema import TarsAction, TarsResponse
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # Added OpenAIEmbeddings
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from dotenv import load_dotenv
from tools.crawler.maping_computer import build_system_map
import os
from typing import Literal
from pydantic import BaseModel, Field

load_dotenv()

class RouteQuery(BaseModel):
    """Route a user query to the most appropriate expert."""
    expert: Literal["coder", "linguist", "analyst", "general"] = Field(
        description="The expert best suited to handle the user's request."
    )

home = os.path.expanduser("~")
my_map = build_system_map(home)

PROTOCOLS = {
    "coder": """
        ### CODER PROTOCOL
        1. INVESTIGATE & ANALYZE
            Action: Use TarsAction.READ (for code) or TarsAction.READ_DOC (for documentation) to ingest the target file.
            Logic: Look for missing imports (e.g., shutil, fitz), syntax errors, or logical flaws (like the missing content argument in your previous execute_command call).
            Environment: If dependencies are suspect, use TarsAction.EXECUTE with pip list or python --version to verify the environment.

        2. REFACTOR (ATOMIZED UPDATES)
            Action: Use TarsAction.UPDATE with mode='overwrite'.
            Constraint: Do not just fix the error; improve the robustness. Ensure all try/except blocks are specific.
            Safety: Before overwriting, ensure hands._is_safe(path) returns true (handled by the tool, but be aware of the blacklist).
        3. VERIFY & TEST
            Action: Use TarsAction.EXECUTE to run the script via terminal.
            Command: python3 path/to/file.py.
            Evaluation: Analyze STDOUT and STDERR. If STDERR is not empty, loop back to Step 1.

        4. DOCUMENT & SYNC
            Action: Call TarsResponse with a detailed content_report.
            Validation: Specifically fill the identified_paths argument to confirm the file exists on disk after the changes.
            Summary: List specifically what was added, deleted, or fixed in plain language for the user.
    """,
    "linguist": """
        ### 1. DECONSTRUCT & ANALYZE (拆解与分析)
            Linguistic Breakdown: For every sentence, provide the Character (Simplified/Traditional), Pinyin (with tone marks), and Literal vs. Idiomatic English Translation.
            Grammar Spotlight: Identify HSK-level grammar patterns. If a sentence uses "把" (bǎ) or "被" (bèi) structures, explain the logic of the word order.
            Vocabulary Tiering: Separate vocabulary into "Essential" (high frequency) and "Flavor" (specific to the text, e.g., cultivation terms in Lord of the Mysteries).
        2. CULTURAL & LITERARY CONTEXT (文化背景)
            World-Building Context: If analyzing Lord of the Mysteries, explain terms within the "Beyonder" (超凡者 - chāofánzhě) system. Relate them to Western fantasy tropes vs. Chinese "Xianxia" influences.
            Etymology: Briefly explain the "radical" (部首) of a key character if it helps retention (e.g., why "魔" for Demon contains the radical for "ghost" 鬼).
            Implicit Meaning: Explain "Face" (面子), social hierarchy, or specific honorifics used between characters in the text.

        3. IMMERSION & APPLICATION (沉浸与应用)
            Shadowing (跟读): Provide a "Chunking Guide"—breaking long sentences into natural breath groups for the user to practice aloud.
            Role-Play (角色扮演): Design a scenario based on the current chapter.
            Example: "You are Klein Moretti trying to buy a potion ingredient at the Black Market. Use '多少钱' and '便宜一点'."
            Tool Integration: Use TarsAction.CREATE to generate a markdown "Flashcard" file in the user's directory containing the day's key phrases.
    """,
    "analyst": """
        ### DOCUMENT ANALYST PROTOCOL
        1. INGESTION & MAPPING (摄入与映射)
            Action: Use TarsAction.LIST to identify relevant files, followed by TarsAction.READ_DOC (for PDF/DOCX) or TarsAction.READ (for plain text).
            Validation: Before processing, TARS must confirm the document's encoding and integrity. If read_document returns an error, he must attempt a fallback to read_code if the extension allows.
            Hierarchical Check: If the document is large, TARS should first map the "Table of Contents" or headers to create a mental index before full extraction.

        2. SYNTHESIS & METADATA (综合与元数据)
            Entity Extraction: Automatically isolate Key Stakeholders, Dates, Legal Jurisdictions, and Financial Figures.
            Contextual Summarization: Create a "Level-1 Summary" (Executive Overview) and a "Level-2 Summary" (Detailed Breakdown by section).
            Action: Use TarsAction.CREATE to save a .json or .md "Summary Report" in the project directory for the user’s future reference.

        3. GROUNDED RAG & VERIFICATION (验证与问答)
            Strict Source Attribution: Every claim made by TARS must be followed by a source locator (e.g., "[Page 4, Paragraph 2]").
            Conflict Detection: If the document contains internal contradictions (e.g., two different dates for the same deadline), TARS must flag this as a "High Priority Risk."
            The "No-Inference" Rule: If a user asks a question not covered in the text, TARS must explicitly state: "Information not found in the provided document," rather than hallucinating based on general knowledge.
    """
}

def get_tars_expert(expert_type:str):
    if expert_type == "linguist":
        return ChatOpenAI(
            model="deepseek-chat", # DeepSeek-V3
            temperature=0.3,
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
    elif expert_type == "coder":
         return ChatOpenAI(
            model="deepseek-reasoner", # DeepSeek-R1 
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
    return ChatOpenAI(model="gpt-4o")

def get_embeddings_model():
    """
    Centralized factory for the embedding model.
    Using 'text-embedding-3-small' for efficiency and low cost.
    """
    return OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

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

                ### PROTOCOL
                    {protocol}
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


router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
planner_chain = router_llm.with_structured_output(RouteQuery)
