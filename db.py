import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")
print("DEBUG: DATABASE_URL =", DATABASE_URL)

def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_client_encoding('UTF8')
        print("✅ DB connected")
        return conn
    except Exception as e:
        print("❌ DB connection failed:", e)
        raise

# Optional: convenient helper for getting a cursor
def get_dict_cursor():
    conn = get_connection()
    return conn.cursor(cursor_factory=RealDictCursor), conn
