from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from gmail_checker import authenticate_gmail, check_new_emails
import dotenv

# Telegram bot settings
TELEGRAM_TOKEN = dotenv.get_key('.env', 'TELEGRAM_API_TOKEN')
CHAT_ID = dotenv.get_key('.env', 'TELEGRAM_CHAT_ID')
whiteListSender = []
blackListSender = []
whiteListSubject = []
blackListSubject = []
interval = 60  # Default interval in seconds
FIRST_RUN = True

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """Check for new emails and send notifications to Telegram."""
    global FIRST_RUN
    new_emails = check_new_emails()
    if not new_emails:
        return
    if FIRST_RUN:
        FIRST_RUN = False
        return
    
    for email in new_emails:
        if (whiteListSender and email['sender'] not in whiteListSender) or (email['sender'] in blackListSender):
            continue
        if (whiteListSubject and email['subject'] not in whiteListSubject) or (email['subject'] in blackListSubject):
            continue
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"New email!\nFrom: {email['sender']}\nSubject: {email['subject']}"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    await update.message.reply_text("Bot started! Checking your Gmail.")
    await update.message.reply_text("Use /blacklistsender or /whitelistsender to manage your email filters.\n"
                                    "Use /blacklistsubject or /whitelistsubject to manage subject filters.\n"
                                    "Use /setinterval <seconds> to change the checking interval.\n"
                                    "Example: /blacklistsender blacklist@gmail.com")
    # Set up periodic checking
    if context.job_queue is None:
        raise ValueError("JobQueue is not initialized.")
    context.job_queue.run_repeating(check_and_notify, interval=interval, first=0)

async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for user input to add senders to blacklist or whitelist."""
    if not update.message or not update.message.text:
        return
    user_input = update.message.text
    if not user_input:
        return
    if user_input.startswith("/blacklistsender"):
        if len(user_input.split()) < 2:
            if not blackListSender:
                await update.message.reply_text("No senders in the blacklist. You can add one now.")
            else:
                await update.message.reply_text(f"Current blacklist: {', '.join(blackListSender)}")
            await update.message.reply_text("Please send the sender's email to add to the blacklist.")
        else:
            email = user_input.split()[1]
            blackListSender.append(email)
            await update.message.reply_text(f"Added {email} to blacklist.")
    elif user_input.startswith("/whitelistsender"):
        if len(user_input.split()) < 2:
            if not whiteListSender:
                await update.message.reply_text("No senders in the whitelist. You can add one now.")
            else:
                await update.message.reply_text(f"Current whitelist: {', '.join(whiteListSender)}")
            await update.message.reply_text("Please send the sender's email to add to the whitelist.")
        else:
            email = user_input.split()[1]
            whiteListSender.append(email)
            await update.message.reply_text(f"Added {email} to whitelist.")
    elif user_input.startswith("/blacklistsubject"):
        if len(user_input.split()) < 2:
            if not blackListSubject:
                await update.message.reply_text("No subjects in the blacklist. You can add one now.")
            else:
                await update.message.reply_text(f"Current blacklist: {', '.join(blackListSubject)}")
            await update.message.reply_text("Please send the subject to add to the blacklist.")
        else:
            subject = user_input.split()[1]
            blackListSubject.append(subject)
            await update.message.reply_text(f"Added '{subject}' to subject blacklist.")
    elif user_input.startswith("/whitelistsubject"):
        if len(user_input.split()) < 2:
            if not whiteListSubject:
                await update.message.reply_text("No subjects in the whitelist. You can add one now.")
            else:
                await update.message.reply_text(f"Current whitelist: {', '.join(whiteListSubject)}")
            await update.message.reply_text("Please send the subject to add to the whitelist.")
        else:
            subject = user_input.split()[1]
            whiteListSubject.append(subject)
            await update.message.reply_text(f"Added '{subject}' to subject whitelist.")
    else:
        await update.message.reply_text("Invalid command. Use /blacklistsender or /whitelistsender for senders, "
                                        "/blacklistsubject or /whitelistsubject for subjects.")

async def blacklistsender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for adding a sender to the blacklist."""
    await update.message.reply_text("Please send the sender's email to add to the blacklist.")
    await user_input_handler(update, context)

async def whitelistsender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for adding a sender to the whitelist."""
    await update.message.reply_text("Please send the sender's email to add to the whitelist.")
    await user_input_handler(update, context)

async def whitelistsubject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for adding a subject to the whitelist."""
    await update.message.reply_text("Please send the subject to add to the whitelist.")
    await user_input_handler(update, context)

async def blacklistsubject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for adding a subject to the blacklist."""
    await update.message.reply_text("Please send the subject to add to the blacklist.")
    await user_input_handler(update, context)

async def interval_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for changing the interval of email checks."""
    global interval
    try:
        new_interval = int(update.message.text.split()[1])
        if new_interval <= 0:
            raise ValueError("Interval must be a positive integer.")
        interval = new_interval
        await update.message.reply_text(f"Interval changed to {interval} seconds.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /setinterval <seconds> (must be a positive integer)")

def main():
    """Main function to run the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
        
    # Add handler for /start command
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("blacklistsender", blacklistsender))
    application.add_handler(CommandHandler("whitelistsender", whitelistsender))
    application.add_handler(CommandHandler("whitelistsubject", whitelistsubject))
    application.add_handler(CommandHandler("blacklistsubject", blacklistsubject))
    application.add_handler(CommandHandler("setinterval", interval_change))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()