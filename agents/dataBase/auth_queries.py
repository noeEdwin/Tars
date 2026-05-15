"""
Database queries for the Tars authentication system.

Table `users` schema (Supabase):
    id              SERIAL PRIMARY KEY
    username        TEXT UNIQUE
    email           TEXT UNIQUE
    hashed_password TEXT
    first_name      TEXT
    last_name       TEXT
    hsk_level       INTEGER DEFAULT 1
    native_language TEXT    DEFAULT 'es'
"""
from psycopg2.extras import RealDictCursor

from dataBase.pool import get_db_connection


def get_user_by_username(username: str) -> dict | None:
    """
    Look up a user by username.
    Includes hashed_password — only use during login for verification.
    """
    sql = """
        SELECT id, username, first_name, last_name, email,
               hashed_password, hsk_level, native_language, learning_goals, interests
        FROM users
        WHERE username = %s
        LIMIT 1;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    """Look up a user by email. Used to verify uniqueness during registration."""
    sql = "SELECT id, username FROM users WHERE email = %s LIMIT 1;"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_username_simple(username: str) -> dict | None:
    """Check if a username already exists (for registration). No sensitive data returned."""
    sql = "SELECT id, username FROM users WHERE username = %s LIMIT 1;"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
            return dict(row) if row else None


def create_user(
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    hashed_password: str,
    hsk_level: int = 1,
    native_language: str = "es",
    learning_goals: str = "Travel",
    interests: str = "",
) -> dict:
    """
    Insert a new user into the database.
    Returns the newly created record (without hashed_password).

    Raises:
        psycopg2.errors.UniqueViolation if username or email already exist.
    """
    sql = """
        INSERT INTO users (username, first_name, last_name, email, hashed_password,
                           hsk_level, native_language, learning_goals, interests)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, username, first_name, last_name, email,
                  hsk_level, native_language, learning_goals, interests;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                username, first_name, last_name, email, hashed_password,
                hsk_level, native_language, learning_goals, interests,
            ))
            conn.commit()
            row = cur.fetchone()
            return dict(row)


def get_user_by_id(user_id: int) -> dict | None:
    """Get all public/profile data for a user by ID."""
    sql = """
        SELECT id, username, first_name, last_name, email,
               hsk_level, native_language, learning_goals, interests
        FROM users
        WHERE id = %s
        LIMIT 1;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def update_user_profile(
    user_id: int,
    first_name: str,
    last_name: str,
    hsk_level: int,
    native_language: str,
    learning_goals: str,
    interests: str,
) -> dict | None:
    """Update an existing user's profile."""
    sql = """
        UPDATE users
        SET first_name = %s,
            last_name = %s,
            hsk_level = %s,
            native_language = %s,
            learning_goals = %s,
            interests = %s
        WHERE id = %s
        RETURNING id, username, first_name, last_name, email,
                  hsk_level, native_language, learning_goals, interests;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                first_name, last_name, hsk_level, native_language,
                learning_goals, interests, user_id
            ))
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
