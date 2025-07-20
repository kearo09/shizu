import asyncpg
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import datetime, timedelta
import os

OWNER_ID = 7638769371  # change if needed

# ✅ Connect pool from db.py
from database import connect_db
db_pool = None

async def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await connect_db()

# ✅ Ensure user exists
async def ensure_user(user_id: int, username: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username) 
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET username = $2;
        """, user_id, username)

# ✅ Get balance
async def get_balance(user_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT total FROM users WHERE user_id = $1", user_id)
        return row["total"] if row else 0

# ✅ /mbalance
async def mbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    await init_db_pool()
    user = update.effective_user
    await ensure_user(user.id, user.username)
    balance = await get_balance(user.id)
    await update.message.reply_text(f"💰 Your balance: ${balance}")

# ✅ /give
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    await init_db_pool()
    user = update.effective_user
    reply_to = update.message.reply_to_message
    args = context.args

    if not reply_to or not args or not args[0].lstrip("$").isdigit():
        return await update.message.reply_text("Usage: /give <amount> (reply to user)")

    receiver = reply_to.from_user
    amount = int(args[0].lstrip("$"))

    if amount <= 0:
        return await update.message.reply_text("Amount must be greater than 0.")

    await ensure_user(user.id, user.username)
    await ensure_user(receiver.id, receiver.username)

    sender_balance = await get_balance(user.id)
    if sender_balance < amount:
        return await update.message.reply_text("❌ You don't have enough balance!")

    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE users SET total = total - $1 WHERE user_id = $2", amount, user.id)
            await conn.execute("UPDATE users SET total = total + $1 WHERE user_id = $2", amount, receiver.id)

    await update.message.reply_text(f"✅ Sent ${amount} to {receiver.first_name}.")

# ✅ /rob
async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    await init_db_pool()
    user = update.effective_user
    reply_to = update.message.reply_to_message
    if not reply_to:
        return await update.message.reply_text("Reply to someone to rob them.")

    victim = reply_to.from_user
    await ensure_user(user.id, user.username)
    await ensure_user(victim.id, victim.username)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT total, protection_until FROM users WHERE user_id = $1", victim.id)
        if not row or row["total"] <= 0:
            return await update.message.reply_text("Victim has no money.")
        if row["protection_until"] and row["protection_until"] > datetime.utcnow():
            return await update.message.reply_text("🛡️ Victim is protected!")

        rob_amount = min(100, row["total"])
        await conn.execute("UPDATE users SET total = total - $1 WHERE user_id = $2", rob_amount, victim.id)
        await conn.execute("UPDATE users SET total = total + $1 WHERE user_id = $2", rob_amount, user.id)

    await update.message.reply_text(f"💸 You robbed ${rob_amount} from {victim.first_name}!")

# ✅ /protect
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    await init_db_pool()
    user = update.effective_user
    await ensure_user(user.id, user.username)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT total FROM users WHERE user_id = $1", user.id)
        if not row or row["total"] < 1000:
            return await update.message.reply_text("❌ You need $1000 for 1 day protection.")

        new_protection = datetime.utcnow() + timedelta(days=1)
        await conn.execute("""
            UPDATE users 
            SET total = total - 1000, protection_until = $1
            WHERE user_id = $2
        """, new_protection, user.id)

    await update.message.reply_text("🛡️ You are protected from robbery for 1 day.")

# ✅ /toprich
async def toprich(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    await init_db_pool()
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, username, total FROM users ORDER BY total DESC LIMIT 10")

    text = "🏆 Top 10 Richest Users:\n\n"
    for i, row in enumerate(rows, 1):
        user_link = f"<a href='tg://user?id={row['user_id']}'>@{row['username'] or 'unknown'}</a>"
        text += f"{i}. {user_link} – ${row['total']}\n"

    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)

# ✅ /resetbalance
async def resetbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await init_db_pool()
    user = update.effective_user
    if user.id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can use this.")

    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET total = 0")

    await update.message.reply_text("🔄 All balances have been reset.")

# ✅ /economy help
async def economy_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    text = (
        "💰 <b>Economy Commands</b>:\n"
        "/mbalance - Show your balance\n"
        "/give $<amount> (reply) - Send money\n"
        "/rob (reply) - Rob someone (max $100)\n"
        "/protect - 1 day robbery protection ($1000)\n"
        "/toprich - Top 10 richest users\n"
        "/resetbalance - Reset balances (owner only)"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# ✅ Handlers to register in bot.py
def get_economy_handlers():
    return [
        CommandHandler("mbalance", mbalance),
        CommandHandler("give", give),
        CommandHandler("rob", rob),
        CommandHandler("protect", protect),
        CommandHandler("toprich", toprich),
        CommandHandler("resetbalance", resetbalance),
        CommandHandler("economy", economy_help),
    ]
