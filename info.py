import psycopg2
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from db import get_connection  # ✅ Correct DB connection import

# Track user's name and username in every message
async def track_user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        if not user or not update.effective_message:
            return

        name = (user.full_name or "").strip()
        username = (user.username or "(empty)").strip()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 1 FROM user_history 
            WHERE user_id = %s AND name = %s AND username = %s AND chat_id = %s
        """, (user.id, name, username, chat_id))

        if not cur.fetchone():
            cur.execute("""
                INSERT INTO user_history (user_id, name, username, chat_id)
                VALUES (%s, %s, %s, %s)
            """, (user.id, name, username, chat_id))
            conn.commit()

        cur.close()
        conn.close()

        print(f"👀 Tracked: {name} | @{username} in chat {chat_id}")
    except Exception as e:
        print(f"🔥 track_user_history error: {e}")


# /detail command (reply to someone's message)
async def detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to get their info.")
        return

    user = update.message.reply_to_message.from_user

    conn = get_connection()
    cur = conn.cursor()

    # Fetch distinct names from all groups
    cur.execute("""
        SELECT DISTINCT name FROM user_history
        WHERE user_id = %s
    """, (user.id,))
    names = [row[0] for row in cur.fetchall()]

    # Fetch distinct usernames from all groups
    cur.execute("""
        SELECT DISTINCT username FROM user_history
        WHERE user_id = %s
    """, (user.id,))
    usernames = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    name_text = "\n".join(f"• {n}" for n in names)
    username_text = "\n".join(f"• @{u}" if u != "(empty)" else "• (empty)" for u in usernames)

    text = f"👤 Past Names:\n{name_text or '• None'}\n\n🔰 Past Usernames:\n{username_text or '• None'}"
    await update.message.reply_text(text)


# Handlers list to import in bot.py
info_handlers = [
    CommandHandler("detail", detail_command)
]

