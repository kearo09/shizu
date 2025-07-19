import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/" + BOT_TOKEN  # Telegram will send updates here
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourapp.onrender.com/<token>
PORT = int(os.getenv("PORT", 8080))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from webhook!")


async def health_check(request):
    return web.Response(text="OK", status=200)


async def telegram_webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, request.app["bot"].bot)
    await request.app["bot"].update_queue.put(update)
    return web.Response(text="OK")


async def main():
    # Step 1: Create Telegram Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.start()

    # Step 2: Create aiohttp web server
    app = web.Application()
    app["bot"] = application
    app.router.add_post(WEBHOOK_PATH, telegram_webhook_handler)
    app.router.add_get("/health", health_check)

    # Step 3: Set webhook to tell Telegram where to send updates
    await application.bot.set_webhook(WEBHOOK_URL)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Bot running on port {PORT} | Webhook set to {WEBHOOK_URL}")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())

