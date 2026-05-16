import json
import logging
import os
from pathlib import Path

from psycopg2.extras import RealDictCursor

from agents.RAG.utils import get_embedding
from agents.dataBase.pool import get_db_connection

logger = logging.getLogger(__name__)


def retrieve_knowledge(user_query: str, current_lesson: int = 1, query_embedding: list[float] = None) -> list[dict]:
    """
    Retrieve technical knowledge (vocabulary/grammar) from base_conocimiento.
    Uses cosine similarity with explicit vector cast.
    """
    try:
        embedding = query_embedding or get_embedding(user_query)
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = r"""
                WITH ranked_knowledge AS (
                    SELECT
                        contenido_zh, pinyin, traduccion_es, nivel_hsk, pos, grammar_ref,
                        1 - (embedding::vector <=> %s::vector) AS cosine_similarity,
                        ROW_NUMBER() OVER (
                            PARTITION BY contenido_zh
                            ORDER BY 1 - (embedding::vector <=> %s::vector) DESC
                        ) as rn
                    FROM public.base_conocimiento
                    WHERE 1 - (embedding::vector <=> %s::vector) >= %s
                    AND NULLIF(regexp_replace(lesson_id::text, '\D', '', 'g'), '')::integer <= %s
                )
                SELECT contenido_zh, pinyin, traduccion_es, nivel_hsk, pos, grammar_ref, cosine_similarity
                FROM ranked_knowledge
                WHERE rn = 1
                ORDER BY cosine_similarity DESC
                LIMIT 5;
            """

            cur.execute(query, (embedding, embedding, embedding, 0.50, current_lesson))
            results = cur.fetchall()

            return [
                {
                    "contenido_zh": row["contenido_zh"],
                    "pinyin": row["pinyin"],
                    "traduccion_es": row["traduccion_es"],
                    "hsk_level": row["nivel_hsk"],
                    "pos": row["pos"],
                    "grammar_ref": row["grammar_ref"],
                    "similarity": row["cosine_similarity"],
                }
                for row in results
            ]
    except Exception as e:
        logger.error("Error retrieving knowledge: %s", e)
        return []


def retrieve_style_examples(target_emotion: str, user_query_embedding: list, limit: int = 3) -> list[str]:
    """
    Retrieve phrases from translations_mvp matching the target emotion.
    Uses ::vector cast to avoid 'operator does not exist: jsonb <=> vector' error.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT es
                    FROM translations_mvp
                    WHERE emocion = %s
                    ORDER BY embedding::vector <=> %s::vector
                    LIMIT %s;
                """

                cur.execute(query, (target_emotion, user_query_embedding, limit))
                return [row["es"] for row in cur.fetchall()]
    except Exception as e:
        logger.error("Error in style RAG (retrieve_style_examples): %s", e)
        return []


def get_lesson_plan_context(lesson_id: int) -> str:
    """Read the HSK1 map JSON file to provide context for the current lesson."""
    json_path = os.path.join(
        Path(__file__).resolve().parent.parent.parent,
        "data_normal_mode", "data", "hsk1_map_clean.json"
    )

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for lesson in data.get("lecciones", []):
            if lesson.get("lesson_id") == lesson_id:
                title_zh = lesson.get("titulo_original", "")
                title_es = lesson.get("titulo_es", "")
                vocab = ", ".join(lesson.get("vocabulario_extraido", []))
                grammar = ", ".join(lesson.get("gramatica_claves", []))

                blueprint = f"=== CURRENT LESSON BLUEPRINT (Lesson {lesson_id}) ===\n"
                blueprint += f"Target Topic: {title_zh} ({title_es})\n"
                if vocab:
                    blueprint += f"Vocabulary to Teach: {vocab}\n"
                if grammar:
                    blueprint += f"Grammar to Enforce: {grammar}\n"
                return blueprint + "======================================="
        return f"=== CURRENT LESSON BLUEPRINT (Lesson {lesson_id}) ===\n(Lesson not found)\n======================================="
    except Exception as e:
        logger.error("Error reading JSON lesson map: %s", e)
        return ""


def get_all_knowledge_for_lesson(lesson_id: int) -> str:
    """Fetch all vocabulary and grammar for a specific lesson from the database."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            query = r"""
                SELECT contenido_zh, pinyin, traduccion_es, pos, grammar_ref
                FROM public.base_conocimiento
                WHERE NULLIF(regexp_replace(lesson_id::text, '\D', '', 'g'), '')::integer = %s;
            """
            cur.execute(query, (lesson_id,))
            results = cur.fetchall()

            if not results:
                return ""

            db_context = f"\n=== DATABASE KNOWLEDGE FOR LESSON {lesson_id} ===\n"
            for row in results:
                zh = row["contenido_zh"]
                pinyin = row["pinyin"]
                trad = row["traduccion_es"]
                pos = row["pos"]
                grammar = row["grammar_ref"]
                db_context += f"- {zh} ({pinyin}) - Meaning: {trad}, POS: {pos}, Ref: {grammar}\n"
            return db_context + "=================================================\n"
    except Exception as e:
        logger.error("Error retrieving complete lesson knowledge: %s", e)
        return ""


def retrieve_character_context(character_name: str, doc_id: int = None) -> str:
    """
    Search document_store for specific book fragments
    to build a psychological profile of the character.
    """
    try:
        query_text = f"Details about {character_name}: personality, dialogues, actions, and behavior."
        query_embedding = get_embedding(query_text)

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if doc_id is not None:
                    query = """
                        WITH target_doc AS (
                            SELECT filename FROM document_store WHERE id = %s
                        )
                        SELECT content
                        FROM document_store
                        WHERE filename = (SELECT filename FROM target_doc)
                        ORDER BY embedding::vector <=> %s::vector
                        LIMIT 4;
                    """
                    cur.execute(query, (doc_id, query_embedding))
                else:
                    query = """
                        SELECT content
                        FROM document_store
                        ORDER BY embedding::vector <=> %s::vector
                        LIMIT 4;
                    """
                    cur.execute(query, (query_embedding,))

                results = cur.fetchall()

                if results:
                    return "\n...\n".join([row["content"] for row in results])

                return f"No specific details found for character {character_name} in the document."
    except Exception as e:
        logger.error("Error retrieving document context for character: %s", e)
        return "Error reading document."
