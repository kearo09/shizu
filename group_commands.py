import re
import logging
import time
import random
import os
from telegram import Update, ChatPermissions
from telegram.ext import MessageHandler, CallbackContext, filters
from typing import Dict, Set, Optional

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_OWNER_ID = 7638769372  # Change to your Telegram user ID

# Simulated database
user_warns: Dict[int, Dict[int, int]] = {}  # {chat_id: {user_id: warn_count}}
muted_users: Dict[int, Set[int]] = {}

async def is_admin(chat_id: int, user_id: int, context: CallbackContext) -> bool:
    if user_id == BOT_OWNER_ID:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ('administrator', 'creator')
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        return False

async def has_permission(chat_id: int, context: CallbackContext, action: str) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        return getattr(bot_member, action, False)
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        return False

async def send_admin_only_message(message) -> None:
    replies = [
        "🚫 This command is for admins only.",
        "❌ You need admin rights to use this command.",
        "🔐 Only admins are allowed to do that!!"
    ]
    await message.reply_text(random.choice(replies))

async def extract_user_and_args(update: Update, context: CallbackContext) -> Optional[tuple]:
    message = update.effective_message
    chat = update.effective_chat
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        args = context.args
    else:
        await message.reply_text("⚠️ Please reply to the user's message to use this command.")
        return None
    return target_user, args

async def warn_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if chat.type not in ('group', 'supergroup'):
        return
    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return
    result = await extract_user_and_args(update, context)
    if not result:
        return
    target_user, _ = result
    if target_user.id in [user.id, context.bot.id]:
        await message.reply_text("🤦‍♂️ You can't warn yourself or the bot.")
        return
    if await is_admin(chat.id, target_user.id, context):
        await message.reply_text("🛡️ You can't warn other admins.")
        return
    if chat.id not in user_warns:
        user_warns[chat.id] = {}
    warn_count = user_warns[chat.id].get(target_user.id, 0) + 1
    user_warns[chat.id][target_user.id] = warn_count
    if warn_count >= 3:
        if not await has_permission(chat.id, context, "can_restrict_members"):
            await message.reply_text("❌ I need ban permissions to ban users after 3 warnings.")
            return
        try:
            await context.bot.ban_chat_member(chat.id, target_user.id)
            await message.reply_text(
                f"🚨 {target_user.mention_html()} has been banned after 3 warnings.",
                parse_mode='HTML'
            )
            user_warns[chat.id].pop(target_user.id, None)
        except Exception as e:
            logger.error(f"Ban error: {e}")
            await message.reply_text("⚠️ Failed to ban the user.")
    else:
        await message.reply_text(
            f"⚠️ {target_user.mention_html()} has been warned. ({warn_count}/3)",
            parse_mode='HTML'
        )

async def unwarn_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return
    result = await extract_user_and_args(update, context)
    if not result:
        return
    target_user, _ = result
    if chat.id not in user_warns or target_user.id not in user_warns[chat.id]:
        await message.reply_text("ℹ️ This user has no warnings.")
        return
    warn_count = user_warns[chat.id][target_user.id] - 1
    if warn_count <= 0:
        user_warns[chat.id].pop(target_user.id)
        await message.reply_text(f"✅ All warnings cleared for {target_user.mention_html()}.", parse_mode='HTML')
    else:
        user_warns[chat.id][target_user.id] = warn_count
        await message.reply_text(
            f"⚠️ 1 warning removed for {target_user.mention_html()}. ({warn_count}/3)",
            parse_mode='HTML'
        )

async def mute_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return
    if not await has_permission(chat.id, context, "can_restrict_members"):
        await message.reply_text("❌ I need permission to mute users.")
        return
    result = await extract_user_and_args(update, context)
    if not result:
        return
    target_user, args = result
    if target_user.id in [user.id, context.bot.id]:
        await message.reply_text("🤦‍♂️ You can't mute yourself or the bot.")
        return
    if await is_admin(chat.id, target_user.id, context):
        await message.reply_text("🛡️ You can't mute other admins.")
        return
    duration = parse_mute_duration(args[0]) if args else None
    until_date = int(time.time()) + duration if duration else None
    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        muted_users.setdefault(chat.id, set()).add(target_user.id)
        msg = "permanently" if not duration else f"{format_duration(duration)}"
        await message.reply_text(f"🔇 {target_user.mention_html()} has been muted {msg}.", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Mute error: {e}")
        await message.reply_text("⚠️ Could not mute the user.")

async def unmute_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return
    if not await has_permission(chat.id, context, "can_restrict_members"):
        await message.reply_text("❌ I need permission to unmute users.")
        return
    result = await extract_user_and_args(update, context)
    if not result:
        return
    target_user, _ = result
    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        muted_users.get(chat.id, set()).discard(target_user.id)
        await message.reply_text(f"🔊 {target_user.mention_html()} has been unmuted.", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Unmute error: {e}")
        await message.reply_text("⚠️ Failed to unmute the user.")

async def ban_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return
    if not await has_permission(chat.id, context, "can_restrict_members"):
        await message.reply_text("❌ I need ban permissions to perform this action.")
        return
    result = await extract_user_and_args(update, context)
    if not result:
        return
    target_user, _ = result
    if await is_admin(chat.id, target_user.id, context):
        await message.reply_text("🛡️ You can't ban another admin.")
        return
    try:
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"🚫 {target_user.mention_html()} has been banned.", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ban error: {e}")
        await message.reply_text("⚠️ Failed to ban the user.")

async def unban_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type not in ('group', 'supergroup'):
        return

    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return

    result = await extract_user_and_args(update, context)
    if not result:
        return

    target_user, _ = result

    if target_user.id == context.bot.id:
        await message.reply_text("🤖 I cannot unban myself. Please manually add me back to the group.")
        return

    try:
        await context.bot.unban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"✅ {target_user.mention_html()} has been unbanned!", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Unban error: {e}")
        await message.reply_text("⚠️ Failed to unban the user!")

async def kick_user(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not await is_admin(chat.id, user.id, context):
        await send_admin_only_message(message)
        return
    if not await has_permission(chat.id, context, "can_restrict_members"):
        await message.reply_text("❌ I need permission to kick users.")
        return
    result = await extract_user_and_args(update, context)
    if not result:
        return
    target_user, _ = result
    try:
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await context.bot.unban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"👢 {target_user.mention_html()} has been kicked.", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Kick error: {e}")
        await message.reply_text("⚠️ Failed to kick the user.")

async def pin_message(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if not await is_admin(chat.id, message.from_user.id, context):
        await send_admin_only_message(message)
        return
    if not await has_permission(chat.id, context, "can_pin_messages"):
        await message.reply_text("❌ I need pin message permission.")
        return
    if not message.reply_to_message:
        await message.reply_text("⚠️ Please reply to the message you want to pin.")
        return
    try:
        await context.bot.pin_chat_message(chat.id, message.reply_to_message.message_id)
        await message.reply_text("📌 Message pinned successfully.")
    except Exception as e:
        logger.error(f"Pin error: {e}")
        await message.reply_text("⚠️ Failed to pin the message.")

async def unpin_message(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if not await is_admin(chat.id, message.from_user.id, context):
        await send_admin_only_message(message)
        return
    if not await has_permission(chat.id, context, "can_pin_messages"):
        await message.reply_text("❌ I need unpin permission.")
        return
    try:
        await context.bot.unpin_chat_message(chat.id)
        await message.reply_text("📍 Message unpinned.")
    except Exception as e:
        logger.error(f"Unpin error: {e}")
        await message.reply_text("⚠️ Failed to unpin message.")

def parse_mute_duration(duration_str: str) -> int:
    try:
        if duration_str.endswith("m"):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith("h"):
            return int(duration_str[:-1]) * 3600
        elif duration_str.endswith("d"):
            return int(duration_str[:-1]) * 86400
        else:
            return int(duration_str)
    except:
        return 600

def format_duration(seconds: int) -> str:
    if seconds >= 86400:
        return f"for {seconds//86400} day(s)"
    elif seconds >= 3600:
        return f"for {seconds//3600} hour(s)"
    elif seconds >= 60:
        return f"for {seconds//60} minute(s)"
    return f"for {seconds} seconds"

async def handle_group_help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("""
🛡️ <b>Admin Commands (.prefix only)</b>:
.warn [reply] - Warn a user (3 = ban)
.unwarn [reply] - Remove 1 warning
.mute [reply] [1m/1h] - Mute temporarily/permanently
.unmute [reply] - Unmute the user
.ban [reply] - Ban user
.unban [reply] - Unban user
.kick [reply] - Kick from group
.pin [reply] - Pin a message
.unpin - Unpin the current message
.help - Show this help
""", parse_mode='HTML')

def add_handlers(app):
    dot_commands = [
        (r'^\.(warn)\b', warn_user),
        (r'^\.(unwarn)\b', unwarn_user),
        (r'^\.(mute)\b', mute_user),
        (r'^\.(unmute)\b', unmute_user),
        (r'^\.(ban)\b', ban_user),
        (r'^\.(unban)\b', unban_user),
        (r'^\.(kick)\b', kick_user),
        (r'^\.(pin)\b', pin_message),
        (r'^\.(unpin)\b', unpin_message),
        (r'^\.(help|gh)\b', handle_group_help),
    ]

    for pattern, handler in dot_commands:
        app.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS & filters.Regex(pattern),
                handler
            )
        )

