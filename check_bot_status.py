#!/usr/bin/env python3
"""
Check where the Telegram bot is currently running
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ No TELEGRAM_BOT_TOKEN found in .env")
    exit(1)

print("🔍 Checking Telegram bot status...")
print()

# Get bot info
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    if data['ok']:
        bot_info = data['result']
        print(f"✅ Bot: @{bot_info['username']}")
        print(f"   Name: {bot_info['first_name']}")
        print(f"   ID: {bot_info['id']}")
        print()
else:
    print(f"❌ Failed to get bot info: {response.status_code}")
    exit(1)

# Try to get updates (this will fail if another instance is running)
print("🔍 Checking for active connections...")
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
response = requests.get(url, params={'timeout': 1})

if response.status_code == 200:
    print("✅ No other bot instance detected!")
    print("   You can run the bot now: python sniper_bot.py")
    print()
elif response.status_code == 409:
    print("⚠️  CONFLICT DETECTED!")
    print()
    print("Another bot instance is running somewhere:")
    print()
    print("Possible locations:")
    print("  1. Render.com deployment")
    print("  2. Railway.app deployment")
    print("  3. Another computer/server")
    print("  4. GitHub Actions (should be disabled now)")
    print()
    print("To fix:")
    print("  1. Go to https://dashboard.render.com/")
    print("  2. Find 'base-fair-launch-sniper' service")
    print("  3. Click 'Suspend' or 'Delete'")
    print("  4. Wait 30 seconds")
    print("  5. Run: python sniper_bot.py")
    print()
else:
    print(f"❌ Unexpected response: {response.status_code}")
    print(f"   {response.text}")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("📚 Documentation:")
print("   - TELEGRAM_CONFLICT_FIXED.md - How to fix the conflict")
print("   - FIXED_AND_READY.md - What was fixed")
print("   - START_HERE.md - Quick start guide")
print()

