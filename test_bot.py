#!/usr/bin/env python3
"""
Simple test bot to verify Telegram connection works
"""
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple start command"""
    await update.message.reply_text(
        "🔍 *Base Fair Launch Sniper Bot*\n\n"
        "✅ Bot is working!\n\n"
        "Commands:\n"
        "/start - This message\n"
        "/test - Test command\n\n"
        "⚠️ Full referral system coming soon!",
        parse_mode='Markdown'
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command"""
    await update.message.reply_text("✅ Test successful! Bot is responding.")

async def main():
    if not TELEGRAM_TOKEN:
        logging.error("Missing TELEGRAM_BOT_TOKEN in .env")
        return
    
    logging.info("Starting bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    
    logging.info("✅ Bot started! Send /start in Telegram")
    
    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\n👋 Bot stopped")
