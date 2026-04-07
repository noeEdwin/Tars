import psycopg2
import os

def get_db_connection():
    # Desglosamos el enlace que te dio Edwin
    conn = psycopg2.connect(
        host="aws-1-us-east-1.pooler.supabase.com",
        database="postgres",
        user="postgres.pysaqdfijktldrzjlqsm",
        password="DkoQGcMFW3dXX5QI",
        port="5432"
    )
    return conn