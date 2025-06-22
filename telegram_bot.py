from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from gmail_checker import authenticate_gmail, check_new_emails
import dotenv

# Telegram bot settings
TELEGRAM_TOKEN = dotenv.get_key('.env', 'TELEGRAM_API_TOKEN')
CHAT_ID = dotenv.get_key('.env', 'TELEGRAM_CHAT_ID')

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """Check for new emails and send notifications to Telegram."""
    new_emails = check_new_emails()
    if not new_emails:
        return
    
    for email in new_emails:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"New email!\nFrom: {email['sender']}\nSubject: {email['subject']}"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    await update.message.reply_text("Bot started! Checking Gmail every 5 minutes.")
    # Set up periodic checking
    if context.job_queue is None:
        raise ValueError("JobQueue is not initialized.")
    context.job_queue.run_repeating(check_and_notify, interval=60, first=0)

def main():
    """Main function to run the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
        
    # Add handler for /start command
    application.add_handler(CommandHandler("start", start))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()