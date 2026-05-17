import json
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from agents.dataBase.pool import get_db_connection
from agents.errors import DatabaseError

logger = logging.getLogger(__name__)


def fetch_persona_from_db(name: str, doc_id: int) -> dict | None:
    """Fetch a character persona from the database by name and associated document ID. Returns None if not found."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if doc_id is None:
                    query = """
                        SELECT archetype, speech_style, traits, rules, knowledge_limit, emotional_anchor
                        FROM character_personas
                        WHERE lower(name) = lower(%s) AND document_id IS NULL
                    """
                    cur.execute(query, (name,))
                else:
                    query = """
                        SELECT archetype, speech_style, traits, rules, knowledge_limit, emotional_anchor
                        FROM character_personas
                        WHERE lower(name) = lower(%s) AND document_id = %s
                    """
                    cur.execute(query, (name, doc_id))

                row = cur.fetchone()

                if row:
                    return {
                        "archetype": row["archetype"],
                        "speech_style": row["speech_style"],
                        "traits": row["traits"],
                        "rules": row["rules"],
                        "knowledge_limit": row["knowledge_limit"],
                        "emotional_anchor": row["emotional_anchor"],
                    }
                return None
    except psycopg2.Error as e:
        logger.error("Error fetching persona for %s: %s", name, e)
        raise DatabaseError.QueryError(f"Failed to fetch persona '{name}'", original=e) from e


def insert_persona(data: dict, doc_id: int, is_auto_generated: bool = True) -> int | None:
    """
    Insert a newly generated character persona into the database.
    Returns the new persona id, or None if already exists.

    Expected data structure:
    {
        "name": "...",
        "archetype": "...",
        "speech_style": "...",
        "traits": "...",
        "rules": ["...", "..."],
        "knowledge_limit": "...",
        "emotional_anchor": "..."
    }
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                rules_json = json.dumps(data.get("rules", []))

                if doc_id is None:
                    query = """
                        INSERT INTO character_personas
                        (document_id, name, archetype, speech_style, traits, rules, knowledge_limit, emotional_anchor, is_auto_generated)
                        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM character_personas
                            WHERE lower(name) = lower(%s) AND document_id IS NULL
                        )
                        RETURNING id
                    """
                    cur.execute(query, (
                        doc_id,
                        data.get("name"),
                        data.get("archetype"),
                        data.get("speech_style"),
                        data.get("traits"),
                        rules_json,
                        data.get("knowledge_limit"),
                        data.get("emotional_anchor"),
                        is_auto_generated,
                        data.get("name"),
                    ))
                else:
                    query = """
                        INSERT INTO character_personas
                        (document_id, name, archetype, speech_style, traits, rules, knowledge_limit, emotional_anchor, is_auto_generated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (document_id, name) DO NOTHING
                        RETURNING id
                    """
                    cur.execute(query, (
                        doc_id,
                        data.get("name"),
                        data.get("archetype"),
                        data.get("speech_style"),
                        data.get("traits"),
                        rules_json,
                        data.get("knowledge_limit"),
                        data.get("emotional_anchor"),
                        is_auto_generated,
                    ))

                result = cur.fetchone()
                conn.commit()

                return result["id"] if result else None
    except psycopg2.Error as e:
        logger.error("Error inserting persona %s: %s", data.get('name'), e)
        raise DatabaseError.QueryError(f"Failed to insert persona '{data.get('name')}'", original=e) from e
