#!/usr/bin/env python3
"""
Simplified Telegram bot - guaranteed to work on Render.com
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN and os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if 'TELEGRAM_BOT_TOKEN' in line:
                TELEGRAM_TOKEN = line.split('=')[1].strip()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        "🔍 *Base Fair Launch Sniper Bot*\n\n"
        "✅ Bot is working on Render.com!\n\n"
        "This is a simplified version to test deployment.\n"
        "Full features coming soon!\n\n"
        "Commands:\n"
        "/start - This message\n"
        "/test - Test the bot",
        parse_mode='Markdown'
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command"""
    await update.message.reply_text("✅ Bot is responding! Deployment successful! 🎉")

def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logging.error("No TELEGRAM_BOT_TOKEN found!")
        return
    
    logging.info("Starting bot...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test))
    
    logging.info("Bot started successfully!")
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
