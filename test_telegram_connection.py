#!/usr/bin/env python3
"""
Simple test to verify Telegram bot connection
"""
import os
import asyncio

# Load .env
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    os.environ[parts[0].strip()] = parts[1].strip()
except:
    pass

from telegram import Bot

async def test():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '@base_fair_launch_alerts')
    
    print(f"Token: {token[:20]}..." if token else "No token")
    print(f"Chat ID: {chat_id}")
    
    if not token:
        print("\n[X] No TELEGRAM_BOT_TOKEN found!")
        return
    
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"\n[OK] Connected to bot: @{me.username}")
        print(f"Bot ID: {me.id}")
        
        # Send test message
        print(f"\nSending test message to {chat_id}...")
        await bot.send_message(
            chat_id=chat_id,
            text="🤖 Bot connection test successful! The enhanced fair launch sniper is ready."
        )
        print("[OK] Test message sent!")
        
    except Exception as e:
        print(f"\n[X] Error: {e}")

if __name__ == '__main__':
    asyncio.run(test())
