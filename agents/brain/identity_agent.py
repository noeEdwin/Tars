import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.brain.chains import IDENTITY_PROFILER_PROMPT
from agents.dataBase.persona_db import insert_persona

def extract_cast_from_text(text: str, doc_id: int):
    """
    Layer A: Cast Sweep.
    Extracts the top 5 characters from the provided text (usually the start of a book)
    and generates a basic persona for each, saving them to the database.
    """
    print("🎭 Running Layer A: Cast Sweep (Identifying main characters...)")
    
    sweep_prompt = """
    Eres un analista literario. Lee el siguiente fragmento del inicio del documento y encuentra los 5 nombres propios más importantes o frecuentes que parezcan ser personajes.
    Para cada uno, genera una ficha de personalidad básica extrapolando su posible arquetipo y estilo de habla a partir del fragmento.
    
    TEXTO:
    {text}
    
    Devuelve estrictamente un JSON array de objetos, donde cada objeto tenga esta estructura:
    [
      {{
        "name": "Nombre del personaje",
        "archetype": "Arquetipo (ej: Héroe, Villano, Mentor)",
        "speech_style": "Estilo de habla",
        "traits": "Rasgos de personalidad",
        "rules": ["Regla 1", "Regla 2"],
        "knowledge_limit": "Límites de conocimiento",
        "emotional_anchor": "Ancla emocional"
      }}
    ]
    """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    prompt = ChatPromptTemplate.from_template(sweep_prompt)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"text": text})
        
        # Clean potential markdown wrapping
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        personas = json.loads(content)
        saved_count = 0
        
        for persona in personas:
            result_id = insert_persona(persona, doc_id, is_auto_generated=True)
            if result_id:
                print(f"   -> 👤 Extracted and saved base persona for: {persona.get('name')}")
                saved_count += 1
                
        return saved_count
        
    except Exception as e:
        print(f"❌ Error during Cast Sweep: {e}")
        return 0

def generate_persona(character_name: str, doc_id: int, fragments: str):
    """
    Layer B: Just-In-Time Profiler.
    Generates a persona on the fly using retrieved RAG fragments for a specific character.
    """
    print(f"🧠 Running Layer B: JIT Profiling for '{character_name}'...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    prompt = ChatPromptTemplate.from_template(IDENTITY_PROFILER_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "character_name": character_name,
            "fragments": fragments
        })
        
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        persona_data = json.loads(content)
        persona_data["name"] = character_name
        
        # Save it for next time
        insert_persona(persona_data, doc_id, is_auto_generated=True)
        print(f"   -> ✨ Synthesized and saved JIT persona for: {character_name}")
        
        return persona_data
        
    except Exception as e:
        import traceback
        print(f"❌ Error generating JIT persona for {character_name}: {e}")
        traceback.print_exc()
        return None
