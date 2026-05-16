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
import logging

import psycopg2
from psycopg2.extras import RealDictCursor

from agents.dataBase.pool import get_db_connection
from agents.errors import DatabaseError, AuthenticationError

logger = logging.getLogger(__name__)


def get_user_by_username(username: str) -> dict | None:
    """
    Look up a user by username.
    Includes hashed_password — only use during login for verification.
    Returns None if user does not exist.
    """
    sql = """
        SELECT id, username, first_name, last_name, email,
               hashed_password, hsk_level, native_language, learning_goals, interests
        FROM users
        WHERE username = %s
        LIMIT 1;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (username,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("Error fetching user by username %s: %s", username, e)
        raise DatabaseError.QueryError(f"Failed to fetch user '{username}'", original=e) from e


def get_user_by_email(email: str) -> dict | None:
    """Look up a user by email. Used to verify uniqueness during registration. Returns None if not found."""
    sql = "SELECT id, username FROM users WHERE email = %s LIMIT 1;"
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (email,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("Error fetching user by email %s: %s", email, e)
        raise DatabaseError.QueryError(f"Failed to fetch user by email '{email}'", original=e) from e


def get_user_by_username_simple(username: str) -> dict | None:
    """Check if a username already exists (for registration). No sensitive data returned. Returns None if not found."""
    sql = "SELECT id, username FROM users WHERE username = %s LIMIT 1;"
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (username,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("Error checking username %s: %s", username, e)
        raise DatabaseError.QueryError(f"Failed to check username '{username}'", original=e) from e


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
        AuthenticationError.DuplicateUser if username or email already exist.
        DatabaseError.QueryError on other database failures.
    """
    sql = """
        INSERT INTO users (username, first_name, last_name, email, hashed_password,
                           hsk_level, native_language, learning_goals, interests)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, username, first_name, last_name, email,
                  hsk_level, native_language, learning_goals, interests;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (
                    username, first_name, last_name, email, hashed_password,
                    hsk_level, native_language, learning_goals, interests,
                ))
                conn.commit()
                row = cur.fetchone()
                if not row:
                    raise DatabaseError.QueryError("User creation returned no row")
                return dict(row)
    except psycopg2.errors.UniqueViolation as e:
        logger.error("Duplicate user creation attempt for %s: %s", username, e)
        raise AuthenticationError.DuplicateUser(
            f"Username '{username}' or email '{email}' is already in use", original=e
        ) from e
    except psycopg2.Error as e:
        logger.error("Error creating user %s: %s", username, e)
        raise DatabaseError.QueryError(f"Failed to create user '{username}'", original=e) from e


def get_user_by_id(user_id: int) -> dict | None:
    """Get all public/profile data for a user by ID. Returns None if not found."""
    sql = """
        SELECT id, username, first_name, last_name, email,
               hsk_level, native_language, learning_goals, interests
        FROM users
        WHERE id = %s
        LIMIT 1;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("Error fetching user by id %d: %s", user_id, e)
        raise DatabaseError.QueryError(f"Failed to fetch user id {user_id}", original=e) from e


def update_user_profile(
    user_id: int,
    first_name: str,
    last_name: str,
    hsk_level: int,
    native_language: str,
    learning_goals: str,
    interests: str,
) -> dict | None:
    """Update an existing user's profile. Returns None if user does not exist."""
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
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (
                    first_name, last_name, hsk_level, native_language,
                    learning_goals, interests, user_id
                ))
                conn.commit()
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("Error updating profile for user %d: %s", user_id, e)
        raise DatabaseError.QueryError(f"Failed to update profile for user {user_id}", original=e) from e
