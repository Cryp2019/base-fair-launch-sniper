#!/usr/bin/env python3
"""
Test script to verify bot menu and features
"""
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def create_main_menu():
    """Create main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Check Token", callback_data="checktoken"),
            InlineKeyboardButton("📊 My Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("👛 My Wallets", callback_data="wallets"),
            InlineKeyboardButton("🎁 Referrals", callback_data="refer")
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
            InlineKeyboardButton("🔔 Alerts", callback_data="alerts")
        ],
        [
            InlineKeyboardButton("💎 Upgrade", callback_data="upgrade"),
            InlineKeyboardButton("ℹ️ How It Works", callback_data="howitworks")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test start command with new menu"""
    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃                                                    ┃\n"
        "┃        🚀 BASE SNIPER          ┃\n"
        "┃                                                    ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "✅ *NEW FEATURES ADDED!*\n\n"
        "┌─────────────────────┐\n"
        "│  👛 *WALLETS*        │\n"
        "└─────────────────────┘\n\n"
        "▸ Create Base wallets\n"
        "▸ Export private keys\n"
        "▸ Manage funds easily\n\n"
        "┌─────────────────────┐\n"
        "│  🔍 *SNIPING*        │\n"
        "└─────────────────────┘\n\n"
        "▸ Auto-scans every 10s\n"
        "▸ Detects new launches\n"
        "▸ Premium priority alerts\n\n"
        "┌─────────────────────┐\n"
        "│  🎨 *NEW MENU*       │\n"
        "└─────────────────────┘\n\n"
        "▸ Reorganized layout\n"
        "▸ Wallet button added\n"
        "▸ Better balance\n\n"
        "👇 *Check out the new menu below!*"
    )
    
    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

async def main():
    """Run test bot"""
    print("🧪 Testing bot menu...")
    print(f"Token: {TELEGRAM_TOKEN[:20]}...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("✅ Starting bot...")
    print("📱 Send /start to the bot in Telegram")
    print("Press Ctrl+C to stop")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        await app.stop()

if __name__ == '__main__':
    asyncio.run(main())

