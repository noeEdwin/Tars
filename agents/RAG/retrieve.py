import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection

def retrieve_knowledge(user_query: str, current_lesson: int = 1) -> list[dict]:
    """
    Retrieves the most relevant knowledge from the 'public.knowledge_base' table using vector similarity.
    Filters the results to only include knowledge from the current lesson or earlier.
    Returns a list of dictionaries containing the content and metadata.
    """
    try:
        # 1. Generar el embedding para la consulta del usuario
        user_question_embedding = get_embedding(user_query)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 2. Ejecutar búsqueda de similitud con nombres de columnas actualizados (Supabase)
        query = r"""
            WITH ranked_knowledge AS (
                SELECT 
                    contenido_zh,
                    pinyin,
                    traduccion_es,
                    nivel_hsk,
                    pos,
                    grammar_ref,
                    1 - (embedding <=> %s::vector) AS cosine_similarity,
                    ROW_NUMBER() OVER (
                        PARTITION BY contenido_zh 
                        ORDER BY 1 - (embedding <=> %s::vector) DESC
                    ) as rn
                FROM public.base_conocimiento
                WHERE 1 - (embedding <=> %s::vector) >= %s
                AND NULLIF(regexp_replace(lesson_id::text, '\D', '', 'g'), '')::integer <= %s
            )
            SELECT contenido_zh, pinyin, traduccion_es, nivel_hsk, pos, grammar_ref, cosine_similarity
            FROM ranked_knowledge 
            WHERE rn = 1 
            ORDER BY cosine_similarity DESC
            LIMIT 5;
        """
        
        cur.execute(query, (
            user_question_embedding,
            user_question_embedding,
            user_question_embedding,
            0.50, # Umbral de similitud ajustable
            current_lesson
        ))
        
        results = cur.fetchall()
        cur.close()
        conn.close()

        # 3. Formatear resultados para el agente
        knowledge_list = []
        for row in results:
            knowledge_list.append({
                "contenido_zh": row[0],
                "pinyin": row[1],
                "traduccion_es": row[2],
                "hsk_level": row[3],
                "pos": row[4],
                "grammar_ref": row[5],
                "similarity": row[6]
            })
            
        return knowledge_list

    except Exception as e:
        # Este print te avisará si falta alguna columna en la tabla de Supabase
        print(f"⚠️ Error retrieving knowledge: {e}")
        return []

import json
import os

def get_lesson_plan_context(lesson_id: int) -> str:
    """
    Reads the static HSK1 map JSON file and returns the blueprint for the given lesson.
    """
    json_path = os.path.join(
        Path(__file__).resolve().parent.parent.parent, 
        "data_normal_mode", "data", "hsk1_map_clean.json"
    )
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for lesson in data.get("lecciones", []):
            if lesson.get("lesson_id") == lesson_id:
                title_zh = lesson.get("titulo_original", "")
                title_es = lesson.get("titulo_es", "")
                vocab = ", ".join(lesson.get("vocabulario_extraido", []))
                grammar = ", ".join(lesson.get("gramatica_claves", []))
                
                blueprint = f"=== CURRENT LESSON BLUEPRINT (Lesson {lesson_id}) ===\n"
                blueprint += f"Target Topic: {title_zh} ({title_es})\n"
                if vocab:
                    blueprint += f"Vocabulary to Teach: {vocab}\n"
                if grammar:
                    blueprint += f"Grammar to Enforce: {grammar}\n"
                return blueprint + "======================================="
                
        return f"=== CURRENT LESSON BLUEPRINT (Lesson {lesson_id}) ===\n(No specific blueprint found)\n======================================="
    except Exception as e:
        print(f"⚠️ Error reading JSON lesson map: {e}")
        return ""

def get_all_knowledge_for_lesson(lesson_id: int) -> str:
    """
    Retrieves all vocabulary and grammar rows from the 'base_conocimiento' table 
    that belong strictly to the provided lesson_id.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = r"""
            SELECT contenido_zh, pinyin, traduccion_es, pos, grammar_ref
            FROM public.base_conocimiento
            WHERE NULLIF(regexp_replace(lesson_id::text, '\D', '', 'g'), '')::integer = %s;
        """
        
        cur.execute(query, (lesson_id,))
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if not results:
            return ""
            
        db_context = f"\n=== DATABASE KNOWLEDGE FOR LESSON {lesson_id} ===\n"
        for row in results:
            zh, pinyin, trad, pos, grammar = row
            entry = f"- {zh} ({pinyin}) - Significado: {trad}"
            if pos:
                 entry += f", POS: {pos}"
            if grammar:
                 entry += f", Regla HSK (grammar_ref): {grammar}"
            db_context += entry + "\n"
            
        db_context += "=================================================\n"
        return db_context
        
    except Exception as e:
        print(f"⚠️ Error retrieving complete lesson knowledge from DB: {e}")
        return ""