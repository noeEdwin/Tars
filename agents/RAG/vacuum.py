import uuid
import time

from psycopg2.extras import RealDictCursor

from agents.RAG.filter import COMMON_GREETINGS
from agents.dataBase.pool import get_db_connection


def _update_job(conn, job_id, status=None, progress=None, current_stage=None, stats=None, error_log=None):
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
    cur = conn.cursor()
    cur.execute(
        f"UPDATE vacuum_jobs SET {', '.join(parts)} WHERE job_id = %s",
        values + [str(job_id)]
    )
    conn.commit()
    cur.close()


def _get_job_stats(conn, job_id):
    cur = conn.cursor()
    cur.execute("SELECT stats FROM vacuum_jobs WHERE job_id = %s", (str(job_id),))
    row = cur.fetchone()
    cur.close()
    return dict(row[0]) if row and row[0] else {}


def stage_a_dedup(conn, job_id) -> int:
    cur = conn.cursor()

    cur.execute("""
        SELECT a.id, b.id, a.access_count, b.access_count
        FROM messages a
        JOIN messages b ON a.id < b.id
        WHERE a.embedding IS NOT NULL
          AND b.embedding IS NOT NULL
          AND (a.embedding <=> b.embedding) < 0.05
          AND a.normalized_text != b.normalized_text
    """)
    pairs = cur.fetchall()

    to_delete = set()
    for id_a, id_b, acc_a, acc_b in pairs:
        if id_a in to_delete or id_b in to_delete:
            continue
        if acc_a >= acc_b:
            to_delete.add(id_b)
        else:
            to_delete.add(id_a)

    deleted = 0
    if to_delete:
        cur.execute(
            "DELETE FROM messages WHERE id = ANY(%s)",
            (list(to_delete),)
        )
        deleted = cur.rowcount
        conn.commit()

    cur.close()
    return deleted


def stage_b_quality_filter(conn, job_id) -> int:
    cur = conn.cursor()

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
    cur.execute(query)
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    return deleted


def stage_c_utility_decay(conn, job_id) -> int:
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM messages
        WHERE access_count = 0
          AND created_at < NOW() - INTERVAL '30 days'
          AND embedding IS NOT NULL
    """)
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    return deleted


def stage_d_n_limit(conn, job_id, n=500) -> int:
    cur = conn.cursor()
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
    cur.close()
    return deleted


def stage_e_db_optimization(conn):
    cur = conn.cursor()
    cur.execute("VACUUM ANALYZE messages")
    conn.commit()
    cur.close()


def run_vacuum_job(job_id, n_limit=500):
    with get_db_connection() as conn:
        stats = {}
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

            cur = conn.cursor()
            cur.execute("SELECT pg_total_relation_size('messages')")
            stats["messages_table_size_bytes"] = cur.fetchone()[0]
            cur.close()

            _update_job(conn, job_id, status="completed", progress=100, current_stage=None, stats=stats)
        except Exception as e:
            import traceback
            _update_job(conn, job_id, status="failed", error_log=traceback.format_exc(), stats=stats)


def create_vacuum_job() -> uuid.UUID:
    job_id = uuid.uuid4()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO vacuum_jobs (job_id, status) VALUES (%s, 'pending')",
            (str(job_id),)
        )
        conn.commit()
        cur.close()
    return job_id


def get_vacuum_job_status(job_id: uuid.UUID) -> dict | None:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT job_id, status, progress, current_stage, stats, error_log, created_at, updated_at "
            "FROM vacuum_jobs WHERE job_id = %s",
            (str(job_id),)
        )
        row = cur.fetchone()
        cur.close()
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
