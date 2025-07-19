# db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
DATABASE_URL = os.getenv("DATABASE_URL")  # yahan sahi se hona chahiy
def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        print("✅ DB connected")
        with conn.cursor() as cur:
            cur.execute("SHOW client_encoding;")
            enc = cur.fetchone()
            print("Client encoding from DB:", enc)
        return conn
    except Exception as e:
        print("DB connection failed:", e)
        raise
