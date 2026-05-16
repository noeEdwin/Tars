"""
Conversation management for Tars.
Handles linking long-term memory (messages) to users.
"""
import logging

from psycopg2.extras import RealDictCursor

from agents.dataBase.pool import get_db_connection

logger = logging.getLogger(__name__)


def get_or_create_active_conversation(user_id: int, mode: str) -> int:
    """
    Return the most recent conversation_id for this user.
    Creates one if none exists.
    Links long-term memory (messages) to this user.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            summary_name = f"Chat: {mode}"

            cur.execute(
                "SELECT id FROM conversations WHERE user_id = %s AND summary = %s ORDER BY created_at DESC LIMIT 1",
                (user_id, summary_name)
            )
            result = cur.fetchone()

            if result:
                return result["id"]

            insert_query = """
                INSERT INTO conversations (user_id, summary)
                VALUES (%s, %s)
                RETURNING id;
            """
            cur.execute(insert_query, (user_id, summary_name))
            row = cur.fetchone()
            if not row:
                logger.error("Failed to create conversation for user %d", user_id)
                return 1
            conv_id = row["id"]
            conn.commit()
            logger.info("New semantic session %d started for user %d (%s).", conv_id, user_id, mode)
            return conv_id
    except Exception as e:
        logger.error("Error getting session for user %d: %s", user_id, e)
        return 1
