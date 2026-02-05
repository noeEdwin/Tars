import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from RAG.utils import get_embedding
from dataBase.connection import get_db_connection

conn = get_db_connection()

def save_memory(role: str, content: str):
    """
    Save the message and its vector in the table historial_chat. 
    """
    try:
        vector = get_embedding(content)
        
        cur = conn.cursor()
        query = """
            INSERT INTO historial_chat (rol, mensaje, embedding)
            VALUES (%s, %s, %s)
        """
        cur.execute(query, (role, content, vector))
        conn.commit()
        cur.close()
        
    except Exception as e:
        print(f"❌ Error guardando memoria: {e}")

# Helper function to get DB URI
def get_db_uri():
    return f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"