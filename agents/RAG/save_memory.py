import os
from dotenv import load_dotenv
from agents.RAG.utils import get_embedding
from dataBase.connection import get_db_connection

def save_long_term_memory(conversation_id: int, role: str, content: str):
    """
    Guarda el mensaje con su vector en la tabla 'messages'.
    Esto es para RAG a largo plazo.
    """
    conn = get_db_connection()
    try:
        vector = get_embedding(content)
        cur = conn.cursor()
        query = """
            INSERT INTO messages (conversation_id, role, content, embedding)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(query, (conversation_id, role, content, vector))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"❌ Error guardando mensaje: {e}")
    finally:
        conn.close()

def retrieve_user_memory(user_id: int, query_text: str, limit: int = 5) -> list[str]:
    """
    Recupera los mensajes pasados semánticamente similares 
    solo del usuario actual aislando por user_id.
    """
    conn = get_db_connection()
    past_memories = []
    try:
        # Obtenemos el embedding de la pregunta actual
        query_vector = get_embedding(query_text)
        
        cur = conn.cursor()
        # Query: Buscar en 'messages' aislando por 'user_id' de 'conversations'
        # Usamos <-> (L2 distance) de pgvector para buscar similitud.
        query = """
            SELECT m.role, m.content
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = %s
            ORDER BY m.embedding <-> %s::vector
            LIMIT %s;
        """
        cur.execute(query, (user_id, query_vector, limit))
        results = cur.fetchall()
        
        for row in results:
            role, content = row
            past_memories.append(f"[{role}]: {content}")
            
        cur.close()
    except Exception as e:
        print(f"❌ Error recuperando memoria para usuario {user_id}: {e}")
    finally:
        conn.close()
        
    return past_memories

def get_db_uri():
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"