from psycopg2.extras import RealDictCursor

from agents.RAG.filter import normalize_text, contains_chinese, should_embed
from agents.RAG.utils import get_embedding
from dataBase.pool import get_db_connection


def save_long_term_memory(conversation_id: int, role: str, content: str, embedding: list[float] = None):
    with get_db_connection() as conn:
        try:
            normalized = normalize_text(content)
            has_zh = contains_chinese(content)

            if not should_embed(content):
                return

            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM messages WHERE normalized_text = %s LIMIT 1",
                (normalized,)
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE messages SET last_used_timestamp = NOW() WHERE id = %s",
                    (existing[0],)
                )
                conn.commit()
                return

            vector = embedding or get_embedding(content)
            query = """
                INSERT INTO messages (conversation_id, role, content, embedding,
                                      normalized_text, has_chinese, access_count)
                VALUES (%s, %s, %s, %s, %s, %s, 0)
            """
            cur.execute(query, (conversation_id, role, content, vector, normalized, has_zh))
            conn.commit()
        except Exception as e:
            print(f"Error saving message: {e}")


def retrieve_user_memory(user_id: int, query_text: str, limit: int = 5, query_embedding: list[float] = None) -> list[str]:
    past_memories = []
    with get_db_connection() as conn:
        try:
            query_vector = query_embedding or get_embedding(query_text)

            cur = conn.cursor()
            query = """
                SELECT m.id, m.role, m.content
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = %s
                ORDER BY m.embedding <-> %s::vector
                LIMIT %s;
            """
            cur.execute(query, (user_id, query_vector, limit))
            results = cur.fetchall()

            for row in results:
                msg_id, role, content = row
                past_memories.append(f"[{role}]: {content}")
                cur.execute(
                    "UPDATE messages SET access_count = access_count + 1 WHERE id = %s",
                    (msg_id,)
                )

            conn.commit()
        except Exception as e:
            print(f"Error retrieving memory for user {user_id}: {e}")

    return past_memories


def get_db_uri() -> str:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
