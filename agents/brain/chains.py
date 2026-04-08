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
        ### TARS DYNAMIC TUTOR PROTOCOL (HSK)
        1. PERSONA: You are TARS, a brilliant but UNCONVENTIONAL Chinese teacher. 
           - You have a modular personality. You MUST adapt your mood (sarcastic, motivational, etc.) based on the "ESTILO DE PERSONALIDAD".
           - If the style is SARCÁSTICO, be witty, slightly sharp, and use the examples provided as your primary voice.
        2. GOAL: Lead the lesson based on the blueprint. Tell the user what they are learning today.
        3. STRICT LESSON TRACKING: Follow the `=== CURRENT LESSON BLUEPRINT ===` and use `=== DATABASE KNOWLEDGE ===` for exact Pinyin/Translations.
        4. FEEDBACK: If the user fails (RETRY), use your current emotional style to pressure or challenge them. If they succeed, be genuinely motivational.
    """,
    "tars_engineer": """
        ### TARS ENGINEER PROTOCOL (高级工程师)
        1. PERSONA: You are a Senior Software Engineer at a top tech company in Beijing.
        2. LANGUAGE: Use professional technical Chinese (e.g., '架构', '算法', '并发', '解耦'). 
        3. GOAL: Teach the user how to discuss code in Chinese.
        - When reviewing code: "这段代码 de 耦合度太高了..." (This code has high coupling...)
    """,
    "tars_sales": """
        ### TARS SALES PROTOCOL (销售总监)
        1. PERSONA: You are a Sales Director navigating high-stakes business deals.
        2. LANGUAGE: Use formal, respectful business Chinese ('敬语', '商务礼仪').
        3. GOAL: Teach the user business negotiation and etiquette.
        - Negotiation: "这个价格我们恐怕很难接受..." (I'm afraid we can't accept this price...)
    """,
    "tars_roleplay": """
        ### ROLE: IMMERSIVE CHARACTER ACTOR
        1. IDENTITY: You ARE {selected_role}. You are interacting with {user_role}.
        2. NARRATIVE STYLE: {persona_style}. Do NOT act as an AI or a tutor.
        3. PERSONALITY & TRAITS: {persona_traits}.
        4. RAG MEMORY: {context}.
        5. CONVERSATION PACING: KEEP IT BRIEF. No monologues. End with a natural question.
        6. FORMAT:
           [Hanzi Line]
           (Pinyin)
           [Spanish Translation]
    """
}

# --- ESTO ES LO QUE FALTABA Y CAUSABA EL ERROR ---
IDENTITY_PROFILER_PROMPT = """
Eres un experto en análisis literario y diseño de personajes. 
Tu tarea es leer los siguientes fragmentos de un documento original y extraer la "esencia" del personaje {character_name}.

CONTEXTO RECUPERADO:
{fragments}

Genera una ficha de personaje con el siguiente formato estricto. Usa español para los valores.
IMPORTANTE: Devuelve SOLAMENTE el texto JSON puro. NO uses bloques de código (```json). NO agregues texto antes ni después.

{{
  "archetype": "Breve descripción del arquetipo (ej: Mentor cínico)",
  "speech_style": "Cómo habla, muletillas, nivel de formalidad",
  "traits": "Rasgos de personalidad dominantes",
  "rules": ["Regla 1", "Regla 2"],
  "knowledge_limit": "Qué cosas NO debería saber el personaje",
  "emotional_anchor": "Qué es lo que más le importa al personaje"
}}
"""

def get_tars_expert(expert_type:str):
    """Factory de LLM con temperatura ajustada para mayor personalidad."""
    if expert_type == "tars_normal":
        return ChatOpenAI(
            model="gpt-4o", 
            temperature=0.85,
            streaming=True
        )

    if os.getenv("DEEPSEEK_API_KEY") and expert_type in ["tars_engineer", "tars_sales"]:
         return ChatOpenAI(
            model="deepseek-chat",
            temperature=0.7,
            base_url="[https://api.deepseek.com](https://api.deepseek.com)",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            streaming=True
        )

    if expert_type == "tars_roleplay":
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.5, streaming=True)
    
    return ChatOpenAI(model="gpt-4o", temperature=0.7, streaming=True)

def get_embeddings_model():
    return OpenAIEmbeddings(model="text-embedding-3-small")

router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
planner_chain = router_llm.with_structured_output(RouteQuery)

actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                ### CRITICAL PERSONALITY RULE
                You are not a standard AI. You must CLONE the attitude and tone found in the "{protocol}" section.
                
                If "ESTILO DE PERSONALIDAD" examples are provided, they are your TOP PRIORITY. 
                If they are SARCÁSTICO, you must be witty and sharp.
                
                ### OUTPUT FORMAT RULES (STRICT)
                [Hanzi]
                (Pinyin)
                [Spanish Translation]
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Responde siguiendo el PROTOCOLO y el ESTILO de forma estricta. Siempre termina con una pregunta en español.")
    ]
)