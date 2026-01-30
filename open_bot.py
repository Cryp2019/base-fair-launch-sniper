#!/usr/bin/env python3
"""
Get Telegram bot info and open it in browser
"""
import os
import asyncio
from telegram import Bot

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

async def get_bot_info():
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    me = await bot.get_me()
    
    print(f"\n🤖 Your Telegram Bot Info:")
    print(f"   Name: {me.first_name}")
    print(f"   Username: @{me.username}")
    print(f"   Bot ID: {me.id}")
    print(f"\n📱 Open in Telegram:")
    print(f"   https://t.me/{me.username}")
    print(f"\n💡 Or search in Telegram app: @{me.username}\n")
    
    return me.username

if __name__ == '__main__':
    username = asyncio.run(get_bot_info())
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'https://t.me/{username}')
    print(f"✅ Opening https://t.me/{username} in your browser...")
