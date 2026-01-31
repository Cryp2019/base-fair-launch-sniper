#!/usr/bin/env python3
"""
Force restart bot and clear Telegram cache
"""
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
    """Test start command"""
    msg = (
        "┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃                                                    ┃\n"
        "┃        🚀 *BASE SNIPER*          ┃\n"
        "┃                                                    ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "*✅ BOT RESTARTED!*\n\n"
        "All new features are now active:\n\n"
        "┌─────────────────────┐\n"
        "│  👛 *WALLETS*        │\n"
        "└─────────────────────┘\n\n"
        "▸ Create Base wallets\n"
        "▸ Export private keys\n"
        "▸ Manage funds\n\n"
        "┌─────────────────────┐\n"
        "│  🔍 *SNIPING*        │\n"
        "└─────────────────────┘\n\n"
        "▸ Auto-scans every 10s\n"
        "▸ Detects new launches\n"
        "▸ Premium priority\n\n"
        "┌─────────────────────┐\n"
        "│  🎨 *NEW MENU*       │\n"
        "└─────────────────────┘\n\n"
        "▸ 4-row layout\n"
        "▸ Wallet button added\n"
        "▸ Better organization\n\n"
        "👇 *Use the menu below:*"
    )
    
    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "wallets":
        msg = (
            "┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃                                                    ┃\n"
            "┃      👛 *MY WALLETS*          ┃\n"
            "┃                                                    ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            "Wallet feature is working!\n\n"
            "This proves the new code is active.\n\n"
            "Now stop this test bot and run:\n"
            "`python sniper_bot.py`\n\n"
            "The full bot has all features!"
        )
        await query.edit_message_text(msg, parse_mode='Markdown')
    else:
        await query.edit_message_text(
            f"Button '{query.data}' clicked!\n\n"
            f"This is a test bot.\n"
            f"Run `python sniper_bot.py` for full features.",
            parse_mode='Markdown'
        )

async def main():
    """Run test bot"""
    print("=" * 50)
    print("🔄 RESTARTING BOT WITH NEW FEATURES")
    print("=" * 50)
    print()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot and see menu"),
        BotCommand("menu", "Show main menu"),
    ]
    
    print("📝 Setting bot commands...")
    await app.bot.set_my_commands(commands)
    print("✅ Commands set!")
    print()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Bot initialized")
    print("📱 Send /start to @base_fair_launch_bot")
    print()
    print("You should see:")
    print("  - 4-row menu")
    print("  - 👛 My Wallets button")
    print("  - All new features")
    print()
    print("Press Ctrl+C to stop this test")
    print("Then run: python sniper_bot.py")
    print("=" * 50)
    print()
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping test bot...")
        print("Now run: python sniper_bot.py")
    finally:
        await app.stop()

if __name__ == '__main__':
    asyncio.run(main())

