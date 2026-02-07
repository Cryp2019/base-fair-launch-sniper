"""
Test if bot can connect to Telegram and respond to commands
Run this locally to verify bot functionality
"""
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Get token from environment or paste here
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or 'YOUR_BOT_TOKEN_HERE'

if 'YOUR_BOT_TOKEN' in BOT_TOKEN:
    print("❌ Please set TELEGRAM_BOT_TOKEN environment variable")
    print("   Or edit this file and paste your token")
    exit(1)

# Simple start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"✅ Bot is working!\n\n"
        f"Hello {user.first_name}!\n"
        f"User ID: {user.id}\n"
        f"Username: @{user.username or 'none'}"
    )
    print(f"✅ Received /start from {user.first_name} (ID: {user.id})")

async def main():
    """Start the bot"""
    print("🚀 Starting test bot...")
    print(f"📱 Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handler
    app.add_handler(CommandHandler("start", start))
    
    # Initialize and start
    print("🔄 Initializing...")
    await app.initialize()
    await app.start()
    
    # Check bot info
    bot_info = await app.bot.get_me()
    print(f"✅ Bot username: @{bot_info.username}")
    print(f"✅ Bot ID: {bot_info.id}")
    print(f"✅ Bot name: {bot_info.first_name}")
    
    # Check webhook
    webhook_info = await app.bot.get_webhook_info()
    if webhook_info.url:
        print(f"⚠️  WEBHOOK IS SET: {webhook_info.url}")
        print("   This will prevent polling from working!")
        print("   Deleting webhook...")
        await app.bot.delete_webhook()
        print("   ✅ Webhook deleted")
    else:
        print("✅ No webhook set - polling will work")
    
    # Start polling
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎯 Bot is now polling for updates")
    print("📱 Send /start to your bot in Telegram")
    print("Press Ctrl+C to stop")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n👋 Stopping bot...")
    finally:
        await app.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Bot stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
