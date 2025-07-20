import psycopg2
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from db import get_connection  # Apne db.py se connection function import karo

# User ka naam aur username track karne wala function
async def track_user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user:
            return

        user_id = user.id
        username = user.username or None
        full_name = user.full_name or None

        conn = get_connection()
        cur = conn.cursor()

        # Pehle check karo ki last stored username aur full_name kya the
        cur.execute(
            "SELECT username, full_name FROM user_names_history WHERE user_id = %s ORDER BY changed_at DESC LIMIT 1",
            (user_id,)
        )
        last_record = cur.fetchone()

        # Agar naya data last data se different hai to hi insert karo
        if last_record is None or last_record[0] != username or last_record[1] != full_name:
            cur.execute(
                "INSERT INTO user_names_history (user_id, username, full_name) VALUES (%s, %s, %s)",
                (user_id, username, full_name)
            )
            conn.commit()

        cur.close()
        conn.close()

    except Exception as e:
        print(f"🔥 track_user_history error: {e}")

# /detail command jo past names aur usernames show karega
async def detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /detail to see their past names and usernames.")
        return

    user = update.message.reply_to_message.from_user
    if not user:
        await update.message.reply_text("User info not found.")
        return

    user_id = user.id

    conn = get_connection()
    cur = conn.cursor()

    # Distinct full names fetch karo jahan full_name null ya empty na ho
    cur.execute("""
        SELECT DISTINCT full_name FROM user_names_history
        WHERE user_id = %s AND full_name IS NOT NULL AND full_name <> ''
    """, (user_id,))
    names = [row[0] for row in cur.fetchall()]

    # Distinct usernames fetch karo jahan username null ya empty na ho
    cur.execute("""
        SELECT DISTINCT username FROM user_names_history
        WHERE user_id = %s AND username IS NOT NULL AND username <> ''
    """, (user_id,))
    usernames = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    name_text = "\n".join(f"• {n}" for n in names) if names else "• None"
    username_text = "\n".join(f"• @{u}" for u in usernames) if usernames else "• None"

    text = f"👤 Past Names:\n{name_text}\n\n🔰 Past Usernames:\n{username_text}"
    await update.message.reply_text(text)

# Handlers list jo bot.py mein add karni hai
info_handlers = [
    CommandHandler("detail", detail_command),
    MessageHandler(filters.ALL & (~filters.COMMAND), track_user_history),
]

