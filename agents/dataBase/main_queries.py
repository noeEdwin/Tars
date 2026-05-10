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

def get_user_hsk_level(user_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT hsk_level FROM users WHERE id = %s LIMIT 1", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else 1
    except Exception as e:
        print(f"Error fetching hsk_level for user {user_id}: {e}")
        return 1

def get_user_profile(user_id: int) -> dict:
    """Returns username, hsk_level, interest_area, native_language for greeting generation."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT username, hsk_level, interest_area, native_language FROM users WHERE id = %s LIMIT 1",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                "username":        row[0],
                "hsk_level":       row[1] or 1,
                "interest_area":   row[2] or "general",
                "native_language": row[3] or "en",
            }
        return {"username": "learner", "hsk_level": 1, "interest_area": "general", "native_language": "en"}
    except Exception as e:
        print(f"Error fetching profile for user {user_id}: {e}")
        return {"username": "learner", "hsk_level": 1, "interest_area": "general", "native_language": "en"}

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

def delete_document_by_filename(user_id: str, filename: str) -> bool:
    """Elimina un documento de la base de datos por su nombre y user_id."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM document_store WHERE user_id = %s AND filename = %s", (int(user_id), filename))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al eliminar el documento {filename}: {e}")
        return False
