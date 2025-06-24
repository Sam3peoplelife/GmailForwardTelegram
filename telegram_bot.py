from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from gmail_checker import get_auth_url, exchange_code_for_token, check_new_emails
import dotenv
import pickle
import os

TELEGRAM_TOKEN = dotenv.get_key('.env', 'TELEGRAM_API_TOKEN')
interval = 60

user_data = {}

def save_user_data():
    with open("user_data.pkl", "wb") as f:
        pickle.dump(user_data, f)

def load_user_data():
    global user_data
    if os.path.exists("user_data.pkl"):
        with open("user_data.pkl", "rb") as f:
            user_data = pickle.load(f)
    else:
        user_data = {}

def get_user_lists(user_id):
    # Ensure user data exists
    if user_id not in user_data:
        user_data[user_id] = {
            "whiteListSender": [],
            "blackListSender": [],
            "whiteListSubject": [],
            "blackListSubject": [],
            "token": None,
            "last_checked_id": None,
            "first_run": True
        }
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_lists(user_id)  # Ensure user data exists
    auth_url = get_auth_url(user_id)
    await update.message.reply_text(
        "Welcome! Please authenticate with Google:\n" + auth_url +
        "\nAfter authorizing, paste the code you receive here."
    )
    await update.message.reply_text("/authCode <code> to authenticate with Google.\n")

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.split(' ', 1)[1] if ' ' in update.message.text else None
    try:
        token = exchange_code_for_token(code, user_id)
        user_data[user_id]["token"] = token
        save_user_data()
        await update.message.reply_text("Google authentication successful! You will now receive notifications.\n"
                                        "You can manage your filters after authentication:\n"
                                        "/blacklistsender <email>\n/whitelistsender <email>\n"
                                        "/blacklistsubject <subject>\n/whitelistsubject <subject>\n"
                                        "/setinterval <seconds>")
    except Exception as e:
        await update.message.reply_text(f"Authentication failed: {e}")

async def handle_list_command(
    update: Update,
    user_input: str,
    list_ref: list,
    list_name: str,
    item_type: str
):
    if len(user_input.split()) < 2:
        if not list_ref:
            await update.message.reply_text(f"No {item_type}s in the {list_name}. You can add one now.")
        else:
            await update.message.reply_text(f"Current {list_name}: {', '.join(list_ref)}")
        await update.message.reply_text(f"Please send the {item_type} to add to the {list_name}.")
    else:
        item = user_input.split(' ', 1)[1]
        if item not in list_ref:
            list_ref.append(item)
            await update.message.reply_text(f"Added '{item}' to {list_name}.")
            save_user_data()
        else:
            await update.message.reply_text(f"'{item}' is already in {list_name}.")

async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    user_lists = get_user_lists(user_id)
    user_input = update.message.text.strip()
    is_authenticated = user_lists.get("token") is not None

    # If not authenticated, only allow /authCode
    if not is_authenticated:
        if user_input.startswith("/authCode"):
            await handle_auth_code(update, context)
        else:
            await update.message.reply_text(
                "You must authenticate first. Use /authCode <code> to authenticate with Google."
            )
        return

    # If authenticated, block /start and /authCode
    if user_input.startswith("/start"):
        await update.message.reply_text("You are already authenticated. Use filter commands or /setinterval.")
    elif user_input.startswith("/authCode"):
        await update.message.reply_text("You are already authenticated. No need to use /authCode again.")
    elif user_input.startswith("/blacklistsender"):
        await handle_list_command(update, user_input, user_lists["blackListSender"], "blacklist", "sender's email")
    elif user_input.startswith("/whitelistsender"):
        await handle_list_command(update, user_input, user_lists["whiteListSender"], "whitelist", "sender's email")
    elif user_input.startswith("/blacklistsubject"):
        await handle_list_command(update, user_input, user_lists["blackListSubject"], "blacklist", "subject")
    elif user_input.startswith("/whitelistsubject"):
        await handle_list_command(update, user_input, user_lists["whiteListSubject"], "whitelist", "subject")
    else:
        await update.message.reply_text(
            "Invalid command. Use /blacklistsender, /whitelistsender, /blacklistsubject, /whitelistsubject, or /setinterval."
        )

async def interval_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global interval
    try:
        new_interval = int(update.message.text.split()[1])
        if new_interval <= 0:
            raise ValueError("Interval must be a positive integer.")
        interval = new_interval
        await update.message.reply_text(f"Interval changed to {interval} seconds.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /setinterval <seconds> (must be a positive integer)")

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    for user_id, data in user_data.items():
        token = data.get("token")
        if not token:
            continue
        try:
            new_emails, last_id = check_new_emails(token, data.get("last_checked_id"))
            data["last_checked_id"] = last_id

            # Skip notifications if this is the first run for the user
            if data.get("first_run", False):
                data["first_run"] = False
                continue
            
            if not new_emails:
                continue
            for email in new_emails:
                if (data["whiteListSender"] and email['sender'] not in data["whiteListSender"]) or (email['sender'] in data["blackListSender"]):
                    continue
                if (data["whiteListSubject"] and email['subject'] not in data["whiteListSubject"]) or (email['subject'] in data["blackListSubject"]):
                    continue
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"New email!\nFrom: {email['sender']}\nSubject: {email['subject']}"
                )
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text=f"Error checking your Gmail: {e}")
    save_user_data()

def main():
    load_user_data()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setinterval", interval_change))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_input_handler))
    application.add_handler(MessageHandler(filters.COMMAND, user_input_handler))
    job_queue = application.job_queue
    job_queue.run_repeating(check_and_notify, interval=interval, first=5)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()