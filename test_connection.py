#!/usr/bin/env python3
"""
Quick test script to verify API connections
"""
import os
import asyncio
from web3 import Web3
from telegram import Bot

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

async def test_connections():
    print("🔍 Testing Base Fair Launch Sniper Connections...\n")
    
    # Test Alchemy/Base connection
    print("1️⃣ Testing Base chain connection...")
    try:
        BASE_RPC = f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_BASE_KEY')}"
        w3 = Web3(Web3.HTTPProvider(BASE_RPC))
        if w3.is_connected():
            block = w3.eth.block_number
            print(f"   ✅ Connected to Base! Latest block: {block}\n")
        else:
            print(f"   ❌ Failed to connect to Base\n")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    # Test Telegram bot
    print("2️⃣ Testing Telegram bot connection...")
    try:
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        me = await bot.get_me()
        print(f"   ✅ Bot connected: @{me.username} ({me.first_name})\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    print("✅ All connections successful! Bot is ready to run.\n")
    print("To start the bot, run: python bot.py")
    return True

if __name__ == '__main__':
    asyncio.run(test_connections())
