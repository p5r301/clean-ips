import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests

from config import (
    TELEGRAM_BOT_TOKEN, GITHUB_TOKEN, GITHUB_REPO,
    GITHUB_BRANCH, CHANNEL_ID, ADMIN_IDS, IPS_FILE_PATH
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_STATES = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access denied.")
        return

    keyboard = [
        [InlineKeyboardButton("Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("Send Clean IP File", callback_data="send_ip_file")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "IP Bot Menu:", reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if not is_admin(user_id):
        await query.answer("Access denied.", show_alert=True)
        return

    await query.answer()

    if query.data == "add_admin":
        ADMIN_STATES[user_id] = "waiting_for_admin_id"
        await query.edit_message_text("Send the new admin's Telegram user ID:")

    elif query.data == "send_ip_file":
        ADMIN_STATES[user_id] = "waiting_for_ip_file"
        await query.edit_message_text("Send the clean IP file (txt format):")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    state = ADMIN_STATES.get(user_id)

    if state == "waiting_for_admin_id":
        try:
            new_admin_id = int(update.message.text.strip())
            if new_admin_id not in ADMIN_IDS:
                ADMIN_IDS.append(new_admin_id)
                await update.message.reply_text(f"Admin {new_admin_id} added successfully!")
            else:
                await update.message.reply_text("User is already an admin.")
        except ValueError:
            await update.message.reply_text("Invalid ID. Send a numeric Telegram user ID.")
        finally:
            ADMIN_STATES.pop(user_id, None)

    elif state == "waiting_for_ip_file":
        if update.message.document and update.message.document.file_name.endswith(".txt"):
            await process_ip_file(update, context)
        else:
            await update.message.reply_text("Please send a valid .txt file.")
        ADMIN_STATES.pop(user_id, None)


async def process_ip_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_content = await file.download_as_bytearray()
    ip_data = file_content.decode("utf-8").strip()

    ips = [line.strip() for line in ip_data.splitlines() if line.strip()]
    cleaned_ips = "\n".join(ips)

    success = update_github_file(cleaned_ips)

    if success:
        await update.message.reply_text(f"Saved! {len(ips)} IPs processed.")
        send_channel_notification(len(ips))
    else:
        await update.message.reply_text("Error saving to GitHub. Check token and repo.")


def update_github_file(content: str) -> bool:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{IPS_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    existing = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH})

    if existing.status_code == 200:
        sha = existing.json()["sha"]
        data = {
            "message": "Update IPs",
            "content": __import__("base64").b64encode(content.encode()).decode(),
            "sha": sha,
            "branch": GITHUB_BRANCH
        }
    else:
        data = {
            "message": "Create IPs file",
            "content": __import__("base64").b64encode(content.encode()).decode(),
            "branch": GITHUB_BRANCH
        }

    resp = requests.put(url, json=data, headers=headers)
    return resp.status_code in (200, 201)


def send_channel_notification(ip_count: int):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"✅ <b>مخزن ایپی تمیز اپدیت شد!</b>\n\n"
        f"📁 تعداد ایپی‌ها: <b>{ip_count}</b>\n\n"
        f"🔄 ایپی‌هاتونو اپدیت کنید!\n\n"
        f"@LILSIB\n@Red_Sonic_pAnEL"
    )
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
