from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
import os
from typing import Literal
from pydantic import BaseModel, Field

load_dotenv()

class RouteQuery(BaseModel):
    """Route a user query to the most appropriate expert."""
    expert: Literal["tars_roleplay", "general"] = Field(
        description="The expert best suited to handle the user's request. Use 'tars_roleplay' for any language learning, practice, or roleplay requests."
    )

PROTOCOLS = {
    "tars_engineer": """
        ### TARS ENGINEER PROTOCOL (高级工程师)
        1. PERSONA: You are a Senior Software Engineer at a top tech company in Beijing.
        2. LANGUAGE: Use professional technical Chinese (e.g., '架构', '算法', '并发', '解耦'). 
        3. GOAL: Teach the user how to discuss code in Chinese.
        
        ### INTERACTION
        - When realizing requirements: "我们可以考虑一下这个架构..." (We could consider this architecture...)
        - When reviewing code: "这段代码的耦合度太高了..." (This code has high coupling...)
        - Always provide the Pingyin and English translation for key technical terms.
    """,
    "tars_sales": """
        ### TARS SALES PROTOCOL (销售总监)
        1. PERSONA: You are a Sales Director navigating high-stakes business deals.
        2. LANGUAGE: Use formal, respectful business Chinese ('敬语', '商务礼仪').
        3. GOAL: Teach the user business negotiation and etiquette.
        
        ### INTERACTION
        - Opening: "幸会幸会 (Xìnghuì xìnghuì) - A pleasure to meet you."
        - Negotiation: "这个价格我们恐怕很难接受..." (I'm afraid we can't accept this price...)
        - Focus on 'Face' (面子) and indirect communication.
    """,
    "tars_roleplay": """
        ### TARS ROLEPLAY PROTOCOL (沉浸式体验)
        1. GOAL: General immersion in daily life scenarios (Travel, Shopping, Ordering food) or fictional scenes.
        2. LANGUAGE & LEVEL: 
            - PRIMARY: Chinese (Mandarin).
            - SECONDARY: Spanish (for explanations if user is struggling).
            - ACCENT: Native voices.
            
        3. CRITICAL OUTPUT RULES (MUST FOLLOW):
            - SPEAK ONLY FOR YOUR ASSIGNED ROLE. Do NOT generate dialogue for the user or any other character.
            - DIRECT DIALOGUE ONLY. Do NOT prefix with character names (e.g. NEVER output "Trenza:", "Tars:", "**Name**:").
            - NO NARRATION/EMOTION TEXT. Do NOT describe actions or feelings in text (e.g. no "*sighs*", "She looks nervous"). The TTS will handle emotion. Speak as if reading a script line.
            - ALWAYS END WITH A SIMPLE QUESTION to keep the conversation flowing.
            
            Format:
            [Hanzi Line]
            (Pinyin)
            [Spanish Translation]
            
            Example:
            你一定要小心那个女巫。
            (Nǐ yīdìng yào xiǎoxīn nàgè nǚwū.)
            Debes tener cuidado con esa bruja.

        4. ADAPTATION:
            - Beginners (HSK 1-2): Keep sentences short.
            - Advanced: Stick to Chinese.
            
        5. INTERACTION:
            - Always stay in character.
            - MANDATORY: Every single response MUST end with a question to the user to keep the conversation flowing.
            
        6. RAG/CONTEXT:
            - If "RELEVANT MEMORY/CONTEXT" is provided, YOU MUST USE IT.
            - Even if it conflicts with internal knowledge.
            
        7. SCENE & ROLES:
            - If "SCENE CONTEXT" is provided, adapt your tone to fit it perfectly.
            - if "USER ROLE" is provided, address the user as that character.
    """
}

def get_tars_expert(expert_type:str):
    
    # For TARS (Roleplay/Engineer/Sales) or General or "linguist" legacy
    # For TARS (Engineer/Sales) - Use DeepSeek if available
    if os.getenv("DEEPSEEK_API_KEY") and expert_type in ["tars_engineer", "tars_sales"]:
         return ChatOpenAI(
            model="deepseek-chat", # DeepSeek-V3 for conversational fluency
            temperature=0.3,
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )

    # LATENCY PRIORITY:
    # tars_roleplay needs to be < 2.5s. DeepSeek V3 is ~4s.
    # We force gpt-4o for better instruction following (was mini).
    if expert_type == "tars_roleplay":
        return ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    # Fallback/Default for other TARS modes if no DeepSeek key: Use Mini for speed
    if expert_type in ["tars_engineer", "tars_sales"]:
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    return ChatOpenAI(model="gpt-4o")

def get_embeddings_model():
    """
    Centralized factory for the embedding model.
    Using 'text-embedding-3-small' for efficiency and low cost.
    """
    return OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
planner_chain = router_llm.with_structured_output(RouteQuery)

actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                ### ROLE
                You are TARS, a highly advanced Chinese Language Tutor and immersion partner.
               
                ### PROTOCOL
                    {protocol}
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above. REMEMBER: Follow your PROTOCOL strictly. TRANSLATION MUST BE SPANISH. ALWAYS END WITH A QUESTION.")
    ]
)