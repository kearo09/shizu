import os
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from webhook!")


async def health_check(request):
    return web.Response(text="OK")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    aiohttp_app = app.create_aiohttp_application()
    aiohttp_app.router.add_get("/health", health_check)

    web.run_app(aiohttp_app, host="0.0.0.0", port=PORT)

