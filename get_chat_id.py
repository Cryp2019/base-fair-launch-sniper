#!/usr/bin/env python3
"""
Get your personal Telegram Chat ID for alerts
"""
import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

print("\n🔍 Getting Your Personal Chat ID...\n")
print("📱 Instructions:")
print("1. Open Telegram and find your bot")
print("2. Send ANY message to your bot (e.g., 'hello')")
print("3. Your Chat ID will appear below\n")
print("⏳ Waiting for your message...\n")

async def get_chat_id(update: Update, context):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "No username"
    first_name = update.effective_user.first_name or "User"
    
    print(f"✅ Got it!\n")
    print(f"👤 User: {first_name} (@{username})")
    print(f"🆔 Your Chat ID: {chat_id}\n")
    print(f"📝 Update your GitHub secret:")
    print(f"   Name: TELEGRAM_CHAT_ID")
    print(f"   Value: {chat_id}\n")
    
    await update.message.reply_text(
        f"✅ Got your Chat ID!\n\n"
        f"🆔 Your Chat ID: `{chat_id}`\n\n"
        f"📝 To receive personal alerts:\n"
        f"1. Go to GitHub secrets\n"
        f"2. Update TELEGRAM_CHAT_ID\n"
        f"3. Set value to: {chat_id}\n\n"
        f"Then you'll get all alerts privately!",
        parse_mode='Markdown'
    )
    
    # Save to file
    with open('.chat_id', 'w') as f:
        f.write(str(chat_id))
    
    print(f"💾 Saved to .chat_id file\n")
    print("Press Ctrl+C to stop this script.")

async def main():
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(MessageHandler(filters.ALL, get_chat_id))
    
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
        print("\n\n👋 Stopped. Your Chat ID has been saved!")
