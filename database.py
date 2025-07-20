import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# ✅ Get or create user
def get_user(user_id: int, username: str, full_name: str):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM economy WHERE user_id = %s", (user_id,))
            user = cur.fetchone()

            if user is None:
                cur.execute("""
                    INSERT INTO economy (user_id, username, full_name, balance, last_active)
                    VALUES (%s, %s, %s, 0, %s)
                    RETURNING *;
                """, (user_id, username, full_name, datetime.utcnow()))
                user = cur.fetchone()
            else:
                cur.execute("""
                    UPDATE economy SET username = %s, full_name = %s, last_active = %s WHERE user_id = %s
                """, (username, full_name, datetime.utcnow(), user_id))

    conn.close()
    return user

# ✅ Update user balance
def update_user_balance(user_id: int, amount: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE economy SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
    conn.close()

# ✅ Get user balance
def get_balance(user_id: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT balance FROM economy WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
    conn.close()
    return result['balance'] if result else 0

# ✅ Transfer balance from one user to another
def transfer_balance(from_user: int, to_user: int, amount: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE economy SET balance = balance - %s WHERE user_id = %s", (amount, from_user))
            cur.execute("UPDATE economy SET balance = balance + %s WHERE user_id = %s", (amount, to_user))
    conn.close()

# ✅ Set protection date
def set_protection(user_id: int, until: datetime):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE economy SET protected_until = %s WHERE user_id = %s", (until, user_id))
    conn.close()

# ✅ Check if user is protected
def is_protected(user_id: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT protected_until FROM economy WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
    conn.close()
    if result and result['protected_until']:
        return datetime.utcnow() < result['protected_until']
    return False

# ✅ Get top 10 richest users
def get_top_richest():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, full_name, balance FROM economy
                ORDER BY balance DESC LIMIT 10
            """)
            results = cur.fetchall()
    conn.close()
    return results

# ✅ Reset all balances
def reset_all_balances():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE economy SET balance = 0")
    conn.close()

# ✅ Get user rank
def get_user_rank(user_id: int):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, RANK() OVER (ORDER BY balance DESC) as rank FROM economy
            """)
            rows = cur.fetchall()
    conn.close()
    for row in rows:
        if row["user_id"] == user_id:
            return row["rank"]
    return None
