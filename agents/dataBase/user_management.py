import os
from dataBase.connection import get_db_connection

def create_user(username: str, password_hash: str, hsk_level: int = 1, interest_area: str = "General", native_language: str = "es"):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
        result = cur.fetchone()
        
        if not result:
            insert_query = """
                INSERT INTO users (username, password, hsk_level, interest_area, native_language)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """
            cur.execute(insert_query, (username, password_hash, hsk_level, interest_area, native_language))
            new_id = cur.fetchone()[0]
            conn.commit()
            print(f"✅ Usuario {username} creado exitosamente con ID {new_id}.")
        else:
            pass
            
        cur.close()
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
    finally:
        conn.close()

def get_user_data(username: str) -> dict:
    conn = get_db_connection()
    user_info = {}
    try:
        cur = conn.cursor()
        query = """
            SELECT id, username, hsk_level, interest_area, native_language 
            FROM users 
            WHERE username = %s 
            LIMIT 1
        """
        cur.execute(query, (username,))
        result = cur.fetchone()
        
        if result:
            user_info = {
                "id": result[0],
                "username": result[1],
                "hsk_level": result[2],
                "interest_area": result[3],
                "native_language": result[4]
            }
        
        cur.close()
    except Exception as e:
        print(f"❌ Error al obtener datos de usuario: {e}")
    finally:
        conn.close()
        
    return user_info

def ensure_conversation_exists(conversation_id: int, user_id: int, summary: str = "Nueva Conversación"):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM conversations WHERE id = %s LIMIT 1", (conversation_id,))
        result = cur.fetchone()
        
        if not result:
            insert_query = """
                INSERT INTO conversations (id, user_id, summary)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """
            cur.execute(insert_query, (conversation_id, user_id, summary))
            conn.commit()
            print(f"✅ Conversación {conversation_id} iniciada.")
            
        cur.close()
    except Exception as e:
        print(f"❌ Error comprobando conversación: {e}")
    finally:
        conn.close()

def get_or_create_active_conversation(user_id: int, mode: str) -> int:
    """
    Returns the most recent conversation_id for this user. 
    If none exists, it creates one.
    This safely links long term memory (messages) to this user.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Buscar la conversación más reciente de este usuario
        # (Para modo Normal vs Roleplay podríamos crear distintas)
        summary_name = f"Chat: {mode}"
        
        cur.execute("SELECT id FROM conversations WHERE user_id = %s AND summary = %s ORDER BY created_at DESC LIMIT 1", (user_id, summary_name))
        result = cur.fetchone()
        
        if result:
            conv_id = result[0]
        else:
            # Crear nueva
            insert_query = """
                INSERT INTO conversations (user_id, summary)
                VALUES (%s, %s)
                RETURNING id;
            """
            cur.execute(insert_query, (user_id, summary_name))
            conv_id = cur.fetchone()[0]
            conn.commit()
            print(f"✅ Nueva sesión semántica {conv_id} iniciada para usuario {user_id} ({mode}).")
            
        cur.close()
        return conv_id
    except Exception as e:
        print(f"❌ Error obteniendo sesión: {e}")
        return 1  # Fallback
    finally:
        conn.close()
