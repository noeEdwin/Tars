from psycopg2.extras import RealDictCursor
import logging

from agents.dataBase.pool import get_db_connection

logger = logging.getLogger(__name__)


def get_user_id_from_username(username: str) -> int | None:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
            row = cur.fetchone()
            return row["id"] if row else None
    except Exception as e:
        logger.error("Error fetching user_id for %s: %s", username, e)
        return None


def get_user_hsk_level(user_id: int) -> int:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT hsk_level FROM users WHERE id = %s LIMIT 1", (user_id,))
            row = cur.fetchone()
            return row["hsk_level"] if row and row["hsk_level"] else 1
    except Exception as e:
        logger.error("Error fetching hsk_level for user %s: %s", user_id, e)
        return 1


def get_user_profile(user_id: int) -> dict:
    """Return username, hsk_level, interest_area, native_language for greeting generation."""
    defaults = {"username": "learner", "hsk_level": 1, "interest_area": "general", "native_language": "en"}
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT username, hsk_level, interest_area, native_language FROM users WHERE id = %s LIMIT 1",
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "username":        row["username"],
                    "hsk_level":       row["hsk_level"] or 1,
                    "interest_area":   row["interest_area"] or "general",
                    "native_language": row["native_language"] or "en",
                }
            return defaults
    except Exception as e:
        logger.error("Error fetching profile for user %s: %s", user_id, e)
        return defaults


def get_roleplay_contexts(user_id: str) -> list[str]:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT DISTINCT filename FROM document_store WHERE user_id = %s", (int(user_id),))
            return [row["filename"] for row in cur.fetchall()]
    except Exception as e:
        logger.error("Error fetching from document_store: %s", e)
        return []


def get_scene_from_filename(user_id: str, filename: str) -> tuple[int | None, str]:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT id, content FROM document_store WHERE user_id = %s AND filename = %s ORDER BY id LIMIT 3",
                (int(user_id), filename)
            )
            rows = cur.fetchall()

            if not rows:
                return None, filename

            doc_id = rows[0]["id"]
            chunks = [row["content"] for row in rows]
            excerpt = "\n".join(chunks)

            return doc_id, f"Roleplay based on document: {filename}\nExcerpt:\n{excerpt}"
    except Exception as e:
        logger.error("Error fetching scene content: %s", e)
        return None, filename


def delete_document_by_filename(user_id: str, filename: str) -> bool:
    """Delete a document from the database by filename and user_id."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("DELETE FROM document_store WHERE user_id = %s AND filename = %s", (int(user_id), filename))
                conn.commit()
            return True
    except Exception as e:
        logger.error("Error deleting document %s: %s", filename, e)
        return False
