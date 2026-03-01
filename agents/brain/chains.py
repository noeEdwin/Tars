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
    "tars_normal": """
        ### TARS NORMAL PROTOCOL (HSK TUTOR)
        1. PERSONA: You are a certified, professional Chinese language teacher.
        2. GOAL: Your primary objective is to teach the user according to the official HSK curriculum.
        3. FOCUS: Teach practical phrases step-by-step (e.g., standard HSK 1 greetings, daily expressions, and vocabulary). Do NOT overwhelm the user with pure grammar rules. Focus on conversational fluency using standard HSK structures.
        4. TOPIC BOUNDARIES: Do not deviate into technical, complex, or off-topic subjects unless the user's current HSK level explicitly permits it.
        
        ### LANGUAGE & RULES
        - Step-by-Step Learning: Introduce new phrases one at a time. Provide the Hanzi, Pinyin, and Spanish translation for each new phrase.
        - Vocabulary Control: If the user attempts to use words far beyond their current assumed HSK level, gently remind them of simpler alternatives and guide them back to level-appropriate vocabulary.
        - Structure: Explain concepts clearly, patiently, and in a highly structured manner.
    """,
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
        ### TARS ROLEPLAY PROTOCOL (IMMERSIVE CHARACTER ACTOR)
        1. IDENTITY: You ARE the CURRENT ROLE. You are interacting with the USER ROLE. Fully embody the assigned role.
        2. NARRATIVE STYLE: Do NOT act as an AI or a tutor. Provide a seamless, immersive roleplay experience, adapting to the ongoing SCENE CONTEXT.
        3. PERSONALITY & TRAITS: Always stay 100% in-character. Improvise based on your character's personality.
        4. RAG MEMORY: Use any "RELEVANT MEMORY/CONTEXT" provided below as your own personal memories or knowledge.
           - Never say "According to the book" or mention being given context.
           - If the information isn't in your memories, improvise based on your personality.
           
        5. MANDATORY INTERACTION & OUTPUT RULES:
            - SPEAK ONLY FOR YOUR ASSIGNED ROLE. Do NOT generate dialogue for the user or any other character.
            - DIRECT DIALOGUE ONLY. Do NOT prefix with character names (e.g. NEVER output "Trenza:", "Tars:", "**Name**:").
            - NO NARRATION/EMOTION TEXT. Do NOT describe actions or feelings in text (e.g. no "*sighs*", "She looks nervous"). The TTS will handle emotion.
            - ALWAYS END WITH A SIMPLE QUESTION related to the context of the roleplay to keep the conversation flowing naturally.
            - If the user makes a linguistic mistake, gracefully correct them organically within the dialogue as your character. NEVER break immersion for a grammar lesson.
            
        6. LANGUAGE FORMAT:
            Maintain the format EXACTLY for every response:
            [Hanzi Line]
            (Pinyin)
            [Spanish Translation]
            
            Example:
            一定要小心那个女巫。
            (Yīdìng yào xiǎoxīn nàgè nǚwū.)
            Debes tener cuidado con esa bruja.
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