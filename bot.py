import os
import asyncio
import logging
import httpx
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = "/" + BOT_TOKEN

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"  # or llama3-8b-8192, gemma-7b-it etc.

# Logging
logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! I'm alive with Groq 🔥")


# 🔮 LLM reply via Groq API
async def chat_with_groq(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    json_data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data, timeout=30)
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logging.error(f"Groq Error: {e}")
            return "Kuch error ho gaya 😓"


# 💬 Handle all text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_text = update.message.text
        await update.message.chat.send_action(action="typing")
        reply = await chat_with_groq(user_text)
        await update.message.reply_text(reply)


# Health check
async def health_check(request):
    return web.Response(text="OK", status=200)


# Webhook route
async def telegram_webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, request.app["bot"].bot)
    await request.app["bot"].update_queue.put(update)
    return web.Response(text="OK")


# Main async function
async def main():
    if not BOT_TOKEN or not WEBHOOK_URL or not GROQ_API_KEY:
        raise Exception("BOT_TOKEN, WEBHOOK_URL, and GROQ_API_KEY must be set!")

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app_bot.initialize()
    await app_bot.start()
    await app_bot.bot.set_webhook(WEBHOOK_URL)

    app = web.Application()
    app["bot"] = app_bot
    app.router.add_post(WEBHOOK_PATH, telegram_webhook_handler)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info(f"🚀 Bot running on port {PORT} | Webhook set to {WEBHOOK_URL}")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())

