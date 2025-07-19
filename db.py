import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")
print("DEBUG: DATABASE_URL =", DATABASE_URL)

def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)  # without cursor_factory here
        with conn.cursor() as cur:
            cur.execute("SET client_encoding TO 'UTF8';")  # set encoding explicitly
        print("✅ DB connected")
        return conn
    except Exception as e:
        print("DB connection failed:", e)
        raise
