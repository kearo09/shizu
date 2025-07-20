from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from db import get_connection  # Async version
import logging

# User ka naam aur username track karne wala function
async def track_user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user:
            return

        user_id = user.id
        username = user.username or None
        full_name = user.full_name or None

        conn = await get_connection()
        async with conn.acquire() as connection:
            last_record = await connection.fetchrow("""
                SELECT username, full_name FROM user_names_history 
                WHERE user_id = $1 
                ORDER BY changed_at DESC LIMIT 1
            """, user_id)

            if last_record is None or last_record["username"] != username or last_record["full_name"] != full_name:
                await connection.execute("""
                    INSERT INTO user_names_history (user_id, username, full_name) 
                    VALUES ($1, $2, $3)
                """, user_id, username, full_name)

    except Exception as e:
        logging.error(f"🔥 track_user_history error: {e}")

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

    conn = await get_connection()
    async with conn.acquire() as connection:
        names_rows = await connection.fetch("""
            SELECT DISTINCT full_name FROM user_names_history
            WHERE user_id = $1 AND full_name IS NOT NULL AND full_name <> ''
        """, user_id)

        usernames_rows = await connection.fetch("""
            SELECT DISTINCT username FROM user_names_history
            WHERE user_id = $1 AND username IS NOT NULL AND username <> ''
        """, user_id)

    names = [row["full_name"] for row in names_rows]
    usernames = [row["username"] for row in usernames_rows]

    name_text = "\n".join(f"• {n}" for n in names) if names else "• None"
    username_text = "\n".join(f"• @{u}" for u in usernames) if usernames else "• None"

    text = f"👤 Past Names:\n{name_text}\n\n🔰 Past Usernames:\n{username_text}"
    await update.message.reply_text(text)

# Handlers list jo bot.py mein add karni hai
info_handlers = [
    CommandHandler("detail", detail_command),
    MessageHandler(filters.ALL & (~filters.COMMAND), track_user_history),
]

