"""
dataBase/auth_queries.py
Consultas de base de datos exclusivas para el sistema de autenticación de Tars.
Usa psycopg2 directamente (mismo patrón que el resto del proyecto).

Estructura real de la tabla `users` (Supabase):
    id              SERIAL PRIMARY KEY  (Integer autoincremental)
    username        TEXT UNIQUE
    email           TEXT UNIQUE
    hashed_password TEXT
    first_name      TEXT
    last_name       TEXT
    hsk_level       INTEGER DEFAULT 1
    native_language TEXT    DEFAULT 'es'
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def _get_conn():
    """Abre una conexión usando las variables de entorno existentes."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=int(os.getenv("DB_PORT", 5432)),
        sslmode="require",
    )


def get_user_by_username(username: str) -> dict | None:
    """
    Busca un usuario por su nombre de usuario.
    Incluye hashed_password — solo usar durante el login para verificación.
    id es Integer (SERIAL), no UUID.
    """
    sql = """
        SELECT id, username, first_name, last_name, email,
               hashed_password, hsk_level, native_language, learning_goals, interests
        FROM users
        WHERE username = %s
        LIMIT 1;
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    """
    Busca un usuario por email.
    Usado para verificar unicidad durante el registro.
    """
    sql = "SELECT id, username FROM users WHERE email = %s LIMIT 1;"
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_username_simple(username: str) -> dict | None:
    """
    Verifica si un username ya existe (para el registro).
    No devuelve datos sensibles.
    """
    sql = "SELECT id, username FROM users WHERE username = %s LIMIT 1;"
    with _get_conn() as conn:
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
    Inserta un nuevo usuario en la base de datos.
    Retorna el registro recién creado (sin hashed_password).
    id es generado automáticamente por la secuencia SERIAL de PostgreSQL.

    Raises:
        psycopg2.errors.UniqueViolation si username o email ya existen.
    """
    sql = """
        INSERT INTO users (username, first_name, last_name, email, hashed_password,
                           hsk_level, native_language, learning_goals, interests)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, username, first_name, last_name, email,
                  hsk_level, native_language, learning_goals, interests;
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                username, first_name, last_name, email, hashed_password,
                hsk_level, native_language, learning_goals, interests,
            ))
            conn.commit()
            row = cur.fetchone()
            return dict(row)


def get_user_by_id(user_id: int) -> dict | None:
    """
    Obtiene todos los datos públicos/perfil de un usuario por su ID.
    """
    sql = """
        SELECT id, username, first_name, last_name, email,
               hsk_level, native_language, learning_goals, interests
        FROM users
        WHERE id = %s
        LIMIT 1;
    """
    with _get_conn() as conn:
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
    """
    Actualiza el perfil de un usuario existente.
    """
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
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (
                first_name, last_name, hsk_level, native_language,
                learning_goals, interests, user_id
            ))
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
