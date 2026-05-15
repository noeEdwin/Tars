"""
Deprecated: Use dataBase.pool.get_db_connection() context manager instead.

This shim exists for gradual migration and will be removed in Phase 2.
It returns a raw connection that the caller must close manually (legacy behavior).
"""
from dataBase.pool import get_db_connection as _pool_get_conn


def get_db_connection():
    """
    Legacy: returns a raw connection (caller must close manually).
    Prefer: with pool.get_db_connection() as conn:
    """
    return _pool_get_conn().__enter__()
