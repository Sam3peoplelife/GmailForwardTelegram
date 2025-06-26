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
            "tokens": [],  # list of tokens for multiple accounts
            "last_checked_ids": [],  # list of last_checked_id per account
            "first_run": []  # list of bools per account
        }
    # Migrate old structure if needed
    if "tokens" not in user_data[user_id]:
        user_data[user_id]["tokens"] = user_data[user_id].get("token", [])
    if "last_checked_ids" not in user_data[user_id]:
        user_data[user_id]["last_checked_ids"] = [user_data[user_id].get("last_checked_id", None)] * len(user_data[user_id]["tokens"])
    if "first_run" not in user_data[user_id]:
        user_data[user_id]["first_run"] = [True] * len(user_data[user_id]["tokens"])
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lists = get_user_lists(user_id)
    if user_lists["tokens"]:
        await update.message.reply_text("You are already authenticated. Use /addaccount to add more Gmail accounts.")
        return
    auth_url = get_auth_url(user_id)
    await update.message.reply_text(
        "Welcome! Please authenticate with Google:\n" + auth_url +
        "\nAfter authorizing, paste the code you receive here with /authCode <code>."
    )

async def add_more_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_lists(user_id)  # Ensure user data exists
    auth_url = get_auth_url(user_id)
    await update.message.reply_text(
        "You can add another Google account for notifications:\n" + auth_url +
        "\nAfter authorizing, paste the code you receive here with /authCode <code>."
    )

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.split(' ', 1)[1] if ' ' in update.message.text else None
    try:
        token = exchange_code_for_token(code, user_id)
        user_lists = get_user_lists(user_id)
        user_lists["tokens"].append(token)
        user_lists["last_checked_ids"].append(None)
        user_lists["first_run"].append(True)
        save_user_data()
        await update.message.reply_text(
            "Google authentication successful! You will now receive notifications for all your accounts.\n"
            "You can manage your filters after authentication:\n"
            "/blacklistsender <email>\n/whitelistsender <email>\n"
            "/blacklistsubject <subject>\n/whitelistsubject <subject>\n"
            "/setinterval <seconds>\n"
            "To add another account, use /addaccount"
        )
    except Exception as e:
        await update.message.reply_text(f"Authentication failed: {e}")

async def handle_list_command(
    update: Update,
    user_input: str,
    list_ref: list,
    list_name: str,
    item_type: str,
    list_command_operation: str
):
    if len(user_input.split()) < 2:
        if not list_ref:
            await update.message.reply_text(f"No {item_type}s in the {list_name}. You can add one now.")
        else:
            await update.message.reply_text(f"Current {list_name}: {', '.join(list_ref)}")
        await update.message.reply_text(f"Please send the {item_type} to add to the {list_name}.")
    else:
        item = user_input.split(' ', 1)[1]
        if list_command_operation == "remove":
            if item in list_ref:
                list_ref.remove(item)
                await update.message.reply_text(f"Removed '{item}' from {list_name}.")
                save_user_data()
            else:
                await update.message.reply_text(f"'{item}' is not in {list_name}.")
        elif list_command_operation == "add":
            if item not in list_ref:
                list_ref.append(item)
                await update.message.reply_text(f"Added '{item}' to {list_name}.")
                save_user_data()
            else:
                await update.message.reply_text(f"'{item}' is already in {list_name}.")
        else:
            raise ValueError("Invalid list command operation. Use 'add' or 'remove'.")

async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    user_lists = get_user_lists(user_id)
    user_input = update.message.text.strip()
    is_authenticated = bool(user_lists.get("tokens"))

    # If not authenticated, only allow /authCode
    if not is_authenticated:
        if user_input.startswith("/authCode"):
            await handle_auth_code(update, context)
        else:
            await update.message.reply_text(
                "You must authenticate first. Use /authCode <code> to authenticate with Google."
            )
        return

    # If authenticated, block /start and /authCode, but allow /addaccount
    if user_input.startswith("/start"):
        await update.message.reply_text("You are already authenticated. Use filter commands, /addaccount, or /setinterval.")
    elif user_input.startswith("/authCode"):
        await update.message.reply_text("You are already authenticated. Use /addaccount to add more Gmail accounts.")
    elif user_input.startswith("/addaccount"):
        await add_more_account(update, context)
    elif user_input.startswith("/blacklistsender"):
        await handle_list_command(update, user_input, user_lists["blackListSender"], "blacklist", "sender's email", "add")
    elif user_input.startswith("/whitelistsender"):
        await handle_list_command(update, user_input, user_lists["whiteListSender"], "whitelist", "sender's email", "add")
    elif user_input.startswith("/blacklistsubject"):
        await handle_list_command(update, user_input, user_lists["blackListSubject"], "blacklist", "subject", "add")
    elif user_input.startswith("/whitelistsubject"):
        await handle_list_command(update, user_input, user_lists["whiteListSubject"], "whitelist", "subject", "add")
    elif user_input.startswith("/blacklistsenderremove"):
        await handle_list_command(update, user_input, user_lists["blackListSender"], "blacklist", "sender's email", "remove")
    elif user_input.startswith("/whitelistsenderremove"):
        await handle_list_command(update, user_input, user_lists["whiteListSender"], "whitelist", "sender's email", "remove")
    elif user_input.startswith("/blacklistsubjectremove"):
        await handle_list_command(update, user_input, user_lists["blackListSubject"], "blacklist", "subject", "remove")
    elif user_input.startswith("/whitelistsubjectremove"):
        await handle_list_command(update, user_input, user_lists["whiteListSubject"], "whitelist", "subject", "remove")
    else:
        await update.message.reply_text(
            "Invalid command. Use /blacklistsender, /whitelistsender, /blacklistsubject, /whitelistsubject, /addaccount, or /setinterval."
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
        tokens = data.get("tokens", [])
        last_checked_ids = data.get("last_checked_ids", [])
        first_run_flags = data.get("first_run", [])
        if not tokens:
            continue
        for idx, token in enumerate(tokens):
            try:
                last_id = last_checked_ids[idx] if idx < len(last_checked_ids) else None
                new_emails, new_last_id = check_new_emails(token, last_id)
                # Update last_checked_ids
                if idx < len(last_checked_ids):
                    last_checked_ids[idx] = new_last_id
                else:
                    last_checked_ids.append(new_last_id)
                # Skip notifications if this is the first run for this account
                if idx < len(first_run_flags) and first_run_flags[idx]:
                    first_run_flags[idx] = False
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
                        text=f"New email (Account {idx+1}):\nFrom: {email['sender']}\nSubject: {email['subject']}"
                    )
            except Exception as e:
                await context.bot.send_message(chat_id=user_id, text=f"Error checking your Gmail account {idx+1}: {e}")
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