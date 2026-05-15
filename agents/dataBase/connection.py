"""
Database connection factory for Tars.

Opens a new psycopg2 connection using environment variables.
Required env vars: DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT (optional, default 5432)
"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create and return a new database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=int(os.getenv("DB_PORT", "5432")),
        sslmode="require",
    )
