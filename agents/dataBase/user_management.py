import os
from dataBase.connection import get_db_connection

def create_user(username: str, password_hash: str, hsk_level: int = 1, interest_area: str = "General", native_language: str = "es"):
    """
    Registra al usuario si no existe en la base de datos.
    Como requiere un módulo pgcrypto instalado o encriptación, para este MVP
    insertamos el string directamente o usamos el que nos provean.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Primero ver si existe
        cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
        result = cur.fetchone()
        
        if not result:
            # Crear
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
            # print(f"Usuario {username} ya existe.")
            pass
            
        cur.close()
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
    finally:
        conn.close()

def get_user_data(username: str) -> dict:
    """
    Obtiene la información principal del usuario.
    """
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
    """
    Asegura que exista el ID de conversación en la base de datos para este usuario.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Verificar si la conversacion existe
        cur.execute("SELECT id FROM conversations WHERE id = %s LIMIT 1", (conversation_id,))
        result = cur.fetchone()
        
        if not result:
            # Insertar con un ID especifico (si se permite identity overrite, 
            # de lo contrario tendriamos que lidiar con sequences)
            # Asumiremos la tabla 'conversations' permite mandar el ID manual si no es conflictivo
            # o que generamos nuevos IDs. En el payload del usuario pidio forzar `current_conv_id = 2`
            
            # Vamos a intentar insertar el conversation_id de forma explicita si no existe.
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
