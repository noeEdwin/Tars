import json

from psycopg2.extras import RealDictCursor

from dataBase.pool import get_db_connection


def fetch_persona_from_db(name: str, doc_id: int) -> dict | None:
    """Fetch a character persona from the database by name and associated document ID."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

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
    except Exception as e:
        print(f"Error fetching persona for {name}: {e}")
        return None


def insert_persona(data: dict, doc_id: int, is_auto_generated: bool = True) -> int | None:
    """
    Insert a newly generated character persona into the database.

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
            cur = conn.cursor(cursor_factory=RealDictCursor)

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
    except Exception as e:
        print(f"Error inserting persona {data.get('name')}: {e}")
        return None
