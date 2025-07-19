import os
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from webhook!")


# Ye health check handler banate hain jo UptimeRobot ke GET requests ko 200 OK dega
async def health_check(request):
    return web.Response(text="OK", status=200)


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # Webhook ke liye aiohttp app nikal lete hain
    aiohttp_app = app.create_aiohttp_application()

    # /health endpoint add karo jo GET accept kare
    aiohttp_app.router.add_get("/health", health_check)

    # Run webhook with custom aiohttp app with extra route
    web.run_app(
        aiohttp_app,
        host="0.0.0.0",
        port=PORT,
    )
