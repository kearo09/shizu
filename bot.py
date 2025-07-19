import os
import asyncio
import telegram
import logging

print("python-telegram-bot version:", telegram.__version__)

from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# Setup logging for debugging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG  # DEBUG level for max detail
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text("Hello from webhook!")

async def start_webhook():
    logger.info("Starting webhook setup...")

    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.info("ApplicationBuilder created")

        app.add_handler(CommandHandler("start", start))
        logger.info("Added /start handler")

        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        await app.bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook set successfully")

        logger.info(f"Running webhook on port {PORT}...")
        await app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
    except Exception as e:
        logger.error(f"Exception during webhook setup: {e}")
        raise

if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(start_webhook())

