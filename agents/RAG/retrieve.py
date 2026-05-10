import sys
import json
import os
from pathlib import Path

# Configuración de rutas para importaciones
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection

def retrieve_knowledge(user_query: str, current_lesson: int = 1, query_embedding: list[float] = None) -> list[dict]:
    """
    Recupera conocimiento técnico (vocabulario/gramática) de 'base_conocimiento'.
    Usa similitud de coseno con cast explícito a vector.
    """
    try:
        user_question_embedding = query_embedding or get_embedding(user_query)
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = r"""
            WITH ranked_knowledge AS (
                SELECT 
                    contenido_zh, pinyin, traduccion_es, nivel_hsk, pos, grammar_ref,
                    1 - (embedding::vector <=> %s::vector) AS cosine_similarity,
                    ROW_NUMBER() OVER (
                        PARTITION BY contenido_zh 
                        ORDER BY 1 - (embedding::vector <=> %s::vector) DESC
                    ) as rn
                FROM public.base_conocimiento
                WHERE 1 - (embedding::vector <=> %s::vector) >= %s
                AND NULLIF(regexp_replace(lesson_id::text, '\D', '', 'g'), '')::integer <= %s
            )
            SELECT contenido_zh, pinyin, traduccion_es, nivel_hsk, pos, grammar_ref, cosine_similarity
            FROM ranked_knowledge 
            WHERE rn = 1 
            ORDER BY cosine_similarity DESC
            LIMIT 5;
        """
        
        cur.execute(query, (user_question_embedding, user_question_embedding, user_question_embedding, 0.50, current_lesson))
        results = cur.fetchall()
        
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
        
        cur.close()
        conn.close()
        return knowledge_list
    except Exception as e:
        print(f"⚠️ Error retrieving knowledge: {e}")
        return []

def retrieve_style_examples(target_emotion: str, user_query_embedding: list, limit: int = 3) -> list[str]:
    """
    Recupera frases de 'translations_mvp' que coincidan con la emoción.
    Incluye cast ::vector para evitar el error 'operator does not exist: jsonb <=> vector'.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # El cast ::vector en el ORDER BY es vital para Supabase
        query = """
            SELECT es
            FROM translations_mvp
            WHERE emocion = %s
            ORDER BY embedding::vector <=> %s::vector
            LIMIT %s;
        """
        
        cur.execute(query, (target_emotion, user_query_embedding, limit))
        results = [row[0] for row in cur.fetchall()]
        
        cur.close()
        return results
    except Exception as e:
        print(f"⚠️ Error en RAG de Estilo (retrieve_style_examples): {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_lesson_plan_context(lesson_id: int) -> str:
    """
    Lee el archivo JSON del mapa HSK1 para dar contexto de la lección actual.
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
                if vocab: blueprint += f"Vocabulary to Teach: {vocab}\n"
                if grammar: blueprint += f"Grammar to Enforce: {grammar}\n"
                return blueprint + "======================================="
        return f"=== CURRENT LESSON BLUEPRINT (Lesson {lesson_id}) ===\n(No lección encontrada)\n======================================="
    except Exception as e:
        print(f"⚠️ Error reading JSON lesson map: {e}")
        return ""

def get_all_knowledge_for_lesson(lesson_id: int) -> str:
    """
    Trae todo el vocabulario y gramática de una lección específica desde la DB.
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
        
        if not results: return ""
            
        db_context = f"\n=== DATABASE KNOWLEDGE FOR LESSON {lesson_id} ===\n"
        for row in results:
            zh, pinyin, trad, pos, grammar = row
            db_context += f"- {zh} ({pinyin}) - Significado: {trad}, POS: {pos}, Ref: {grammar}\n"
        return db_context + "=================================================\n"
    except Exception as e:
        print(f"⚠️ Error retrieving complete lesson knowledge: {e}")
        return ""
    
def retrieve_character_context(character_name: str, doc_id: int = None) -> str:
    """
    Busca en 'document_store' fragmentos específicos del libro 
    para armar el perfil psicológico del personaje.
    """
    try:
        # 1. Creamos el vector de lo que queremos saber del personaje
        query_text = f"Detalles sobre {character_name}: personalidad, diálogos, acciones y forma de ser."
        query_embedding = get_embedding(query_text)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if doc_id is not None:
            # 2. Truco pro: Si doc_id es solo un "pedazo" del libro, buscamos su 'filename' 
            # para buscar contexto en TODO el libro, no solo en ese pedazo.
            query = """
                WITH target_doc AS (
                    SELECT filename FROM document_store WHERE id = %s
                )
                SELECT content
                FROM document_store
                WHERE filename = (SELECT filename FROM target_doc)
                ORDER BY embedding::vector <=> %s::vector
                LIMIT 4;
            """
            cur.execute(query, (doc_id, query_embedding))
        else:
            # Búsqueda general si no hay documento específico
            query = """
                SELECT content
                FROM document_store
                ORDER BY embedding::vector <=> %s::vector
                LIMIT 4;
            """
            cur.execute(query, (query_embedding,))
            
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if results:
            # Unimos los 4 fragmentos más relevantes del libro
            return "\n...\n".join([row[0] for row in results])
        
        return "No se encontraron detalles específicos del personaje en el documento."
        
    except Exception as e:
        print(f"⚠️ Error recuperando contexto del documento para el personaje: {e}")
        return "Error al leer el documento."