import os
from dotenv import load_dotenv  # <-- AGREGA ESTA LÍNEA
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection

def save_memory(role: str, content: str, conversation_id: int):
    """
    Guarda el mensaje con su vector en la nueva tabla 'messages'.
    """
    conn = get_db_connection()
    try:
        vector = get_embedding(content)
        cur = conn.cursor()
        # Ahora insertamos en la tabla 'messages' usando conversation_id
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

def get_db_uri():
    load_dotenv() # Ahora ya no dará NameError
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")
    
    # Construcción para Supabase
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"