import os
import random
import time
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# Romantic DPs folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DP_FOLDER = os.path.join(BASE_DIR, "romantic_dps")

# Tracking
last_couple_time = {}
group_participants = {}  # {chat_id: set((user_id, full_name))}


# ✅ Track all active message senders
async def track_active_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and not user.is_bot:
        group_participants.setdefault(chat.id, set()).add((user.id, user.full_name))


# ✅ /couples command
async def couples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = chat.id

    if chat.type == "private":
        await update.message.reply_text("Ye command sirf groups me hi use kar sakte ho! 😊")
        return

    now = time.time()
    if chat_id in last_couple_time and now - last_couple_time[chat_id] < 300:
        await update.message.reply_text("Aaj ka couple already declare ho chuka hai 💘, use after 5 mins!")
        return
    last_couple_time[chat_id] = now

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_users = [(a.user.id, a.user.full_name) for a in admins if not a.user.is_bot]
        normal_users = group_participants.get(chat_id, set())

        all_users = list(set(admin_users + list(normal_users)))

        if len(all_users) < 2:
            await update.message.reply_text("Kam se kam 2 active members chahiye couple banane ke liye 💔")
            return

        couple = random.sample(all_users, 2)
        name1 = f"<a href='tg://user?id={couple[0][0]}'>{couple[0][1]}</a>"
        name2 = f"<a href='tg://user?id={couple[1][0]}'>{couple[1][1]}</a>"

        files = [f for f in os.listdir(LOCAL_DP_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not files:
            await update.message.reply_text("Koi romantic pic nahi mili 😢")
            return

        image_path = os.path.join(LOCAL_DP_FOLDER, random.choice(files))
        caption = (
            f"💖 <b>Today's Cute Couple</b> 💖\n\n"
            f"{name1} 💞 {name2}\n\n"
            "Love is in the air 💘\n\n"
            "~ From Shizu with love 💋"
        )

        with open(image_path, "rb") as photo:
            await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, parse_mode="HTML")

    except Exception as e:
        print(f"Error in /couples: {e}")
        await update.message.reply_text("Oops! Kuch galat ho gaya 😶‍🌫️")


# ✅ /crush command
async def crush(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("Yeh command sirf group me kaam karta hai 😅")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Kiski crush check karni hai? Reply karo 😜")
        return

    replied_user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_users = [(a.user.id, a.user.full_name) for a in admins if not a.user.is_bot]
        normal_users = group_participants.get(chat_id, set())

        all_users = list(set(admin_users + list(normal_users)))
        all_users = [u for u in all_users if u[0] != replied_user.id]

        if not all_users:
            await update.message.reply_text("Koi aur member nahi mila crush ke liye 😢")
            return

        crush_user = random.choice(all_users)
        crush_percent = random.randint(0, 100)

        msg = (
            f"💘 {replied_user.mention_html()} ka secret crush hai "
            f"<a href='tg://user?id={crush_user[0]}'>{crush_user[1]}</a>\n"
            f"Crush level: <b>{crush_percent}% ❤️</b>"
        )
        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        print(f"Error in /crush: {e}")
        await update.message.reply_text("Crush calculate karne me error aa gaya 😅")


# ✅ /love command
async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("Yeh command sirf group me chalega 😅")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Kiske saath love check karna hai? Reply toh karo 😘")
        return

    user1 = update.message.from_user
    user2 = update.message.reply_to_message.from_user
    love_percent = random.randint(0, 100)

    msg = (
        f"💕 Love meter report 💕\n"
        f"{user1.mention_html()} ❤️ {user2.mention_html()}\n"
        f"Love compatibility: <b>{love_percent}%</b> 🔥"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


# ✅ /look command
async def look(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("Yeh command sirf group me kaam karti hai 😅")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Kis par look rate karu? Reply toh karo 😜")
        return

    user = update.message.reply_to_message.from_user
    rating = random.randint(0, 100)
    msg = f"{user.mention_html()} ki look rating: <b>{rating}% 😍</b>"
    await update.message.reply_text(msg, parse_mode="HTML")


# ✅ /brain command
async def brain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("Yeh command sirf group me kaam karti hai 😅")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Kis ke dimaag ka scan karu? Reply toh karo 🤖")
        return

    user = update.message.reply_to_message.from_user
    iq = random.randint(0, 100)
    msg = f"IQ level of {user.mention_html()} is <b>{iq}%</b> 😎"
    await update.message.reply_text(msg, parse_mode="HTML")


# ✅ /stupid_meter command
async def stupid_meter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("Yeh command sirf group me kaam karti hai 😅")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Kiski stupidity check karu? Reply karo 😜")
        return

    user = update.message.reply_to_message.from_user
    percent = random.randint(0, 100)
    msg = f"Hmm 🤔 Stupid meter scanning...\nResult for {user.mention_html()}: <b>{percent}% 😵‍💫 stupid detected</b>"
    await update.message.reply_text(msg, parse_mode="HTML")


# ✅ /id command
async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Ye command sirf group me hi use hoti hai 😊")
        return

    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("Kisi message pe reply karke /id use karo!")
        return

    user = reply.from_user
    msg = f"👤 Replied User ID: <code>{user.id}</code>\n👥 Group ID: <code>{chat.id}</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


# ✅ /bio command
async def user_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("Kisi user ke message pe reply karo jiska bio dekhna hai 😊")
        return

    user = reply.from_user
    try:
        info = await context.bot.get_chat(user.id)
        bio = info.bio or "😶 Bio set nahi kiya hua"
        await update.message.reply_text(f"📋 Bio of {user.full_name}:\n\n{bio}")
    except Exception as e:
        print(f"Error in /bio: {e}")
        await update.message.reply_text("User ka bio laane me dikkat ho gayi 😅")


# ✅ Register all handlers
def register_fun_commands(app):
    app.add_handler(CommandHandler("couples", couples))
    app.add_handler(CommandHandler("crush", crush))
    app.add_handler(CommandHandler("love", love))
    app.add_handler(CommandHandler("look", look))
    app.add_handler(CommandHandler("brain", brain))
    app.add_handler(CommandHandler("stupid_meter", stupid_meter))
    app.add_handler(CommandHandler("id", user_id))
    app.add_handler(CommandHandler("bio", user_bio))
    # ✅ New (non-blocking, runs before others)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_active_members), group=-1)



