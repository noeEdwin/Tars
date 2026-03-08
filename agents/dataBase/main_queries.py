from dataBase.connection import get_db_connection

def get_user_id_from_username(username: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error fetching user_id for {username}: {e}")
        return None

def get_roleplay_contexts(user_id: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Get distinct filenames
        cur.execute("SELECT DISTINCT filename FROM document_store WHERE user_id = %s", (int(user_id),))
        docs = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return docs
    except Exception as e:
        print(f"Error fetching from document_store: {e}")
        return []

def get_scene_from_filename(user_id: str, filename: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, content FROM document_store WHERE user_id = %s AND filename = %s ORDER BY id LIMIT 3", (int(user_id), filename))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        doc_id = rows[0][0] if rows else None
        chunks = [row[1] for row in rows]
        excerpt = "\n".join(chunks)
        
        return doc_id, f"Roleplay based on document: {filename}\nExcerpt:\n{excerpt}"
    except Exception as e:
        print(f"Error fetching scene content: {e}")
        return None, filename
