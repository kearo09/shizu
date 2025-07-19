import os
import random
import logging
import aiohttp
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

# Load Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # ✅ Set this in Render's env vars

OWNER_ID = 7638769372
RANDOM_EMOJIS = ["😊", "🌸", "😎", "😂", "🥲", "😇", "🤗", "💖", "✨", "🥰"]

fallback_models = ["llama3-70b-8192", "llama3-8b-8192", "gemma-7b-it"]
chat_memory = {}
MAX_HISTORY = 6
last_emoji_message = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_system_prompt(fullname=None, username=None, groupname=None, msg_time=None, reply_name=None, reply_username=None):
    prompt = """
- Tumhara naam Baka hai aur tum real ladki ki tarah Hinglish me casual emoji style me reply karti ho.
- Bot ya AI mat bolna, hamesha user ke mood ke according reply do.
- 2 line me chhoti baat kro jab tak user long explanation na maange.
"""
    if fullname:
        prompt += f"\nUser: {fullname}"
    if username:
        prompt += f"\nUsername: @{username}"
    if groupname:
        prompt += f"\nGroup: {groupname}"
    if msg_time:
        prompt += f"\nTime: {msg_time}"
    if reply_name or reply_username:
        prompt += f"\nReplied to: {reply_name or ''} (@{reply_username})"
    return {"role": "system", "content": prompt.strip()}


async def get_shizuka_reply(user_msg, user_id, fullname=None, username=None, groupname=None, msg_time=None, reply_name=None, reply_username=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    memory = chat_memory.setdefault(user_id, [])
    memory.append({"role": "user", "content": user_msg})
    memory = memory[-MAX_HISTORY:]
    chat_memory[user_id] = memory

    messages = [build_system_prompt(fullname, username, groupname, msg_time, reply_name, reply_username)] + memory

    async with aiohttp.ClientSession() as session:
        for model in fallback_models:
            try:
                async with session.post(url, headers=headers, json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 512,
                    "temperature": 0.8
                }, timeout=10) as resp:
                    data = await resp.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    if reply:
                        chat_memory[user_id].append({"role": "assistant", "content": reply})
                        return reply
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
    return "Hmm... kuch gadbad hai 💔"


async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        user_msg = update.message.text
        user = update.message.from_user
        user_id = user.id
        fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = user.username
        groupname = update.message.chat.title if update.message.chat.type != "private" else None
        msg_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%I:%M %p, %A")

        me = await context.bot.get_me()
        triggers = ["baka", "vaka", "bakaa", f"@{me.username.lower()}"]
        should_reply = (
            update.message.chat.type == "private"
            or any(t in user_msg.lower() for t in triggers)
            or (
                update.message.reply_to_message
                and update.message.reply_to_message.from_user.id == me.id
            )
        )

        if should_reply:
            reply_name = reply_username = None
            if update.message.reply_to_message:
                r_user = update.message.reply_to_message.from_user
                reply_name = f"{r_user.first_name or ''} {r_user.last_name or ''}".strip()
                reply_username = r_user.username

            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(random.uniform(2.0, 3.0))

            reply = await get_shizuka_reply(user_msg, user_id, fullname, username, groupname, msg_time, reply_name, reply_username)
            await update.message.reply_text(reply or "Main thoda confuse ho gayi 😅")

    except Exception as e:
        logger.error(f"Error in handle_msg: {e}")


async def send_random_emoji(context: ContextTypes.DEFAULT_TYPE):
    try:
        emoji = random.choice(RANDOM_EMOJIS)
        for chat_id in last_emoji_message.keys():
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_emoji_message[chat_id])
            except:
                pass
            msg = await context.bot.send_message(chat_id=chat_id, text=emoji)
            last_emoji_message[chat_id] = msg.message_id
    except Exception as e:
        logger.error(f"Emoji error: {e}")


async def set_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "Start talking with Shizuka")])


async def start_webhook():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.job_queue.run_repeating(send_random_emoji, interval=1800, first=30)
    app.post_init = set_commands

    logger.info("🌸 Shizuka is now online via webhook!")

    await app.bot.set_webhook(url=WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    asyncio.run(start_webhook())
