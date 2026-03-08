import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection

def retrieve_knowledge(user_query: str) -> list[dict]:
    """
    Retrieves the most relevant knowledge from the 'public.knowledge_base' table using vector similarity.
    Returns a list of dictionaries containing the content and metadata.
    """
    try:
        # 1. Generar el embedding para la consulta del usuario
        user_question_embedding = get_embedding(user_query)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 2. Ejecutar búsqueda de similitud con nombres de columnas actualizados (Supabase)
        query = """
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
            0.50 # Umbral de similitud ajustable
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