import sys
import json
from pathlib import Path
from dataBase.connection import get_db_connection

def fetch_persona_from_db(name: str, doc_id: int):
    """
    Fetches a character persona from the database by name and associated document ID.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
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
        
        cur.close()
        conn.close()
        
        if row:
            return {
                "archetype": row[0],
                "speech_style": row[1],
                "traits": row[2],
                "rules": row[3], # Expected to come out as list/dict if jsonb is parsed
                "knowledge_limit": row[4],
                "emotional_anchor": row[5]
            }
        return None
    except Exception as e:
        print(f"Error fetching persona for {name}: {e}")
        return None

def insert_persona(data: dict, doc_id: int, is_auto_generated: bool = True):
    """
    Inserts a newly generated character persona into the database.
    
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
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verify JSON list formatting for rules
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
        else:
            query = """
                INSERT INTO character_personas 
                (document_id, name, archetype, speech_style, traits, rules, knowledge_limit, emotional_anchor, is_auto_generated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, name) DO NOTHING
                RETURNING id
            """
        
        if doc_id is None:
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
                data.get("name") # Included for the lower(name) in WHERE NOT EXISTS
            ))
        else:
            cur.execute(query, (
                doc_id,
                data.get("name"),
                data.get("archetype"),
                data.get("speech_style"),
                data.get("traits"),
                rules_json,
                data.get("knowledge_limit"),
                data.get("emotional_anchor"),
                is_auto_generated
            ))
        
        result_id = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if result_id:
            return result_id[0]
        return None
            
    except Exception as e:
        print(f"Error inserting persona {data.get('name')}: {e}")
        return None
