from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
import random
import asyncio

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            name = member.first_name or "Dost"
            welcome_messages = [
                f"Hey {name} 👋, Welcome to the group!",
                f"{name} is here! Welcome welcome 💖",
                f"Yay! {name} joined 🥳",
                f"Hii {name} 😇 Welcome to our cute little family!",
                f"Welcome {name} 🌸 Welcome to our little cute home! ",
                f"Welcome {name} 🌸 Hoii ",
                f"Yay! {name} joined 🥳 How’s everything going?",
                f"Woohoo! {name} is here 💃 Let the fun begin! 🎉",
                f"Welcome, {name}! 🌟 We were waiting for you! 😊",
                f"Hey {name}! 🚀 The party has started! 🎊",
                f"Yayyy! {name} arrived 🎈 How are you, bro? 😄",
                f"Hello {name}! ✨ The group was incomplete without you! 🥰",
                f"Welcome aboard, {name}! 🏆 Ready for some fun? 😎",
                f"Guys, {name} has joined! 🥳 Fun times ahead! 🚀",
                f"Namaste {name}! 🙏 Warm welcome! 🎁",
                f"Yay! {name} joined the squad! 🎯 It's going to be awesome! 😆",
                f"Hey {name}! 🎊 Welcome to the madness! 🤪",
                f"The party just got better! {name} is here! 🍾🔥",
                f"Welcome {name}! 🌈 Hope you're ready for fun! 😜",
                f"Yay! {name} joined the gang! 🤩 How’s everything going?",
                f"Hello {name}! 🎤 Mic check, let’s see your swag! 😎",
                f"Let’s go! {name} is here! 🎶 Time to groove! 💃",
                f"Welcome {name}! 🏵️ There’s a special seat just for you! 😉",
                f"Hey {name}! 🫶 Welcome to the group 🌟",
                f"Yay! {name} is in the house! 🏠 Let’s chat! 💬",
                f"Welcome {name}! 🎲 Luck is now on your side! 😃",
                f"Welcome {name}! Forgot about us? 😒",
            ]
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(random.randint(2, 4))  # simulate realistic delay
            await update.message.reply_text(random.choice(welcome_messages))

# handler export
def welcome_handler():
    return MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members)
