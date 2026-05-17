import uuid
import time
import traceback
from typing import Optional

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from agents.RAG.filter import COMMON_GREETINGS
from agents.dataBase.pool import get_db_connection


def _update_job(
    conn: connection,
    job_id: uuid.UUID,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    current_stage: Optional[str] = None,
    stats: Optional[dict] = None,
    error_log: Optional[str] = None,
) -> None:
    parts = []
    values = []
    if status is not None:
        parts.append("status = %s")
        values.append(status)
    if progress is not None:
        parts.append("progress = %s")
        values.append(progress)
    if current_stage is not None:
        parts.append("current_stage = %s")
        values.append(current_stage)
    if stats is not None:
        parts.append("stats = %s")
        values.append(stats)
    if error_log is not None:
        parts.append("error_log = %s")
        values.append(error_log)
    parts.append("updated_at = NOW()")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            f"UPDATE vacuum_jobs SET {', '.join(parts)} WHERE job_id = %s",
            values + [str(job_id)]
        )
        conn.commit()


def _get_job_stats(conn: connection, job_id: uuid.UUID) -> dict:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT stats FROM vacuum_jobs WHERE job_id = %s", (str(job_id),))
        row = cur.fetchone()
        return dict(row["stats"]) if row and row["stats"] else {}


def stage_a_dedup(conn: connection, job_id: uuid.UUID) -> int:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT a.id AS id_a, b.id AS id_b, a.access_count AS acc_a, b.access_count AS acc_b
            FROM messages a
            JOIN messages b ON a.id < b.id
            WHERE a.embedding IS NOT NULL
              AND b.embedding IS NOT NULL
              AND (a.embedding <=> b.embedding) < 0.05
              AND a.normalized_text != b.normalized_text
        """)
        pairs = cur.fetchall()

    to_delete = set()
    for row in pairs:
        id_a, id_b, acc_a, acc_b = row["id_a"], row["id_b"], row["acc_a"], row["acc_b"]
        if id_a in to_delete or id_b in to_delete:
            continue
        if acc_a >= acc_b:
            to_delete.add(id_b)
        else:
            to_delete.add(id_a)

    deleted = 0
    if to_delete:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "DELETE FROM messages WHERE id = ANY(%s)",
                (list(to_delete),)
            )
            deleted = cur.rowcount
            conn.commit()

    return deleted


def stage_b_quality_filter(conn: connection, job_id: uuid.UUID) -> int:
    greeting_list = ", ".join(f"'{g.replace(chr(39), chr(39)+chr(39))}'" for g in COMMON_GREETINGS)
    query = f"""
        DELETE FROM messages
        WHERE id IN (
            SELECT id FROM messages
            WHERE (
                (char_length(content) < 10 AND has_chinese = FALSE)
                OR lower(regexp_replace(content, '[^[:alnum:][:space:]]', '', 'g')) IN ({greeting_list})
            )
            AND embedding IS NOT NULL
        )
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        deleted = cur.rowcount
        conn.commit()
    return deleted


def stage_c_utility_decay(conn: connection, job_id: uuid.UUID) -> int:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            DELETE FROM messages
            WHERE access_count = 0
              AND created_at < NOW() - INTERVAL '30 days'
              AND embedding IS NOT NULL
        """)
        deleted = cur.rowcount
        conn.commit()
    return deleted


def stage_d_n_limit(conn: connection, job_id: uuid.UUID, n: int = 500) -> int:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            DELETE FROM messages
            WHERE id IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at DESC) as rn
                    FROM messages
                    WHERE embedding IS NOT NULL
                ) ranked
                WHERE rn > %s
            )
        """, (n,))
        deleted = cur.rowcount
        conn.commit()
    return deleted


def stage_e_db_optimization(conn: connection) -> None:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("VACUUM ANALYZE messages")
        conn.commit()


def run_vacuum_job(job_id: uuid.UUID, n_limit: int = 500) -> None:
    with get_db_connection() as conn:
        stats: dict = {}
        try:
            _update_job(conn, job_id, status="in_progress", progress=0, current_stage="dedup")

            t0 = time.time()

            _update_job(conn, job_id, current_stage="dedup", progress=10)
            stats["stage_a_dedup_deleted"] = stage_a_dedup(conn, job_id)
            _update_job(conn, job_id, stats=stats, progress=30, current_stage="quality_filter")

            stats["stage_b_quality_deleted"] = stage_b_quality_filter(conn, job_id)
            _update_job(conn, job_id, stats=stats, progress=50, current_stage="utility_decay")

            stats["stage_c_utility_deleted"] = stage_c_utility_decay(conn, job_id)
            _update_job(conn, job_id, stats=stats, progress=70, current_stage="n_limit")

            stats["stage_d_n_limit_deleted"] = stage_d_n_limit(conn, job_id, n=n_limit)
            _update_job(conn, job_id, stats=stats, progress=85, current_stage="db_optimization")

            stage_e_db_optimization(conn)
            stats["duration_seconds"] = round(time.time() - t0, 2)

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT pg_total_relation_size('messages') AS size")
                row = cur.fetchone()
                if row:
                    stats["messages_table_size_bytes"] = row["size"]

            _update_job(conn, job_id, status="completed", progress=100, current_stage=None, stats=stats)
        except Exception as e:
            _update_job(conn, job_id, status="failed", error_log=traceback.format_exc(), stats=stats)


def create_vacuum_job() -> uuid.UUID:
    job_id = uuid.uuid4()
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO vacuum_jobs (job_id, status) VALUES (%s, 'pending')",
                (str(job_id),)
            )
            conn.commit()
    return job_id


def get_vacuum_job_status(job_id: uuid.UUID) -> dict | None:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT job_id, status, progress, current_stage, stats, error_log, created_at, updated_at "
                "FROM vacuum_jobs WHERE job_id = %s",
                (str(job_id),)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "job_id": str(row["job_id"]),
                "status": row["status"],
                "progress": row["progress"],
                "current_stage": row["current_stage"],
                "stats": dict(row["stats"]) if row["stats"] else {},
                "error_log": row["error_log"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
