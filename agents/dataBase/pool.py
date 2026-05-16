"""
Database connection pool for Tars.

Provides a centralized connection factory with thread-safe pooling.
All database modules should import from here.

Usage:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(...)
"""
import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "sslmode": "require",
}

_pool: ThreadedConnectionPool | None = None


def _get_pool() -> ThreadedConnectionPool:
    """Return the connection pool, creating it lazily on first call."""
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            **DB_CONFIG,
        )
    return _pool


@contextmanager
def get_db_connection() -> Generator:
    """
    Context manager for database connections.
    Automatically returns the connection to the pool when done.
    """
    conn = _get_pool().getconn()
    try:
        yield conn
    finally:
        _get_pool().putconn(conn)


def close_pool():
    """Close all pooled connections. Call on application shutdown."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
