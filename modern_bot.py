#!/usr/bin/env python3
"""
🚀 Base Fair Launch Sniper - Modern Telegram Bot
Sleek, modern design with comprehensive features
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import UserDatabase

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'base_fair_launch_bot')

# Initialize database
db = UserDatabase()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== MODERN UI COMPONENTS =====

def create_main_menu():
    """Create main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 How It Works", callback_data="howitworks"),
            InlineKeyboardButton("📊 My Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("🎁 Referral Link", callback_data="refer"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("🔔 Toggle Alerts", callback_data="alerts"),
            InlineKeyboardButton("💎 Upgrade", callback_data="upgrade")
        ],
        [
            InlineKeyboardButton("🔗 Join Channel", url="https://t.me/base_fair_launch_alerts"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button():
    """Create back to menu button"""
    keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu")]]
    return InlineKeyboardMarkup(keyboard)

# ===== COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with modern design"""
    user = update.effective_user
    args = context.args
    
    # Check for referral code
    referrer_code = args[0] if args else None
    
    # Add user to database
    result = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referrer_code=referrer_code
    )
    
    total_users = db.get_total_users()
    
    # Build welcome message with modern formatting
    welcome_msg = (
        f"╔═══════════════════════╗\n"
        f"   🚀 *BASE FAIR LAUNCH*\n"
        f"        *SNIPER BOT*\n"
        f"╚═══════════════════════╝\n\n"
        f"👋 Welcome, *{user.first_name}*!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *PROTECTION FEATURES*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Ownership Renounced\n"
        f"✅ <5% Creator Pre-mine\n"
        f"✅ Liquidity Locked 30+ Days\n"
        f"✅ No Honeypot/Tax Scams\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 *COMMUNITY STATS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: *{total_users:,}*\n"
        f"🎁 Your Tier: *Free*\n"
        f"🔔 Alerts: *Enabled*\n\n"
    )
    
    if result.get('referred_by'):
        welcome_msg += f"✨ *Referred by User {result['referred_by']}*\n\n"
    
    welcome_msg += (
        f"⚠️ *DISCLAIMER*\n"
        f"Not financial advice. 99% of tokens fail.\n"
        f"Always DYOR and invest responsibly.\n\n"
        f"👇 *Choose an option below:*"
    )
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    query = update.callback_query
    await query.answer()

    msg = (
        f"╔═══════════════════════╗\n"
        f"      📱 *MAIN MENU*\n"
        f"╚═══════════════════════╝\n\n"
        f"Choose an option below:"
    )

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

async def howitworks_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain how the bot works"""
    query = update.callback_query
    await query.answer()

    msg = (
        f"╔═══════════════════════╗\n"
        f"   🔍 *HOW IT WORKS*\n"
        f"╚═══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *VERIFICATION PROCESS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*1️⃣ Ownership Check*\n"
        f"   └ Confirms contract ownership\n"
        f"      sent to burn address\n\n"
        f"*2️⃣ Pre-mine Analysis*\n"
        f"   └ Verifies creator holds\n"
        f"      less than 5% of supply\n\n"
        f"*3️⃣ Liquidity Lock*\n"
        f"   └ Checks LP tokens locked\n"
        f"      via Unicrypt/Team Finance\n\n"
        f"*4️⃣ Honeypot Detection*\n"
        f"   └ Scans for hidden taxes\n"
        f"      and malicious functions\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *AUTOMATED SCANNING*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏱️ Scans every 5 minutes\n"
        f"🔍 Monitors Uniswap V3 on Base\n"
        f"📢 Instant alerts for fair launches\n"
        f"🎯 Filters out 95%+ of scams\n\n"
        f"⚠️ *Note:* Cannot detect ALL\n"
        f"honeypots. Always test with\n"
        f"small amounts first!"
    )

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_back_button()
    )

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_stats = db.get_user_stats(user.id)

    if not user_stats:
        await query.edit_message_text(
            "❌ User not found. Please use /start first!",
            reply_markup=create_back_button()
        )
        return

    user_data = user_stats['user']
    referrals = user_stats['referrals']

    # Build referrals list
    referral_list = ""
    if referrals:
        referral_list = "\n\n*Recent Referrals:*\n"
        for i, ref in enumerate(referrals[:5], 1):
            username = f"@{ref['username']}" if ref['username'] else "No username"
            referral_list += f"{i}. {ref['first_name']} ({username})\n"

    msg = (
        f"╔═══════════════════════╗\n"
        f"    📊 *YOUR STATS*\n"
        f"╚═══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *PROFILE*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Name: *{user_data['first_name']}*\n"
        f"User ID: `{user_data['user_id']}`\n"
        f"Joined: *{user_data['joined_date'][:10]}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 *ACCOUNT STATUS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Tier: *{user_data['tier'].upper()}*\n"
        f"Alerts: *{'✅ Enabled' if user_data['alerts_enabled'] else '❌ Disabled'}*\n"
        f"Referrals: *{user_data['total_referrals']}*\n"
        f"{referral_list}"
    )

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_back_button()
    )

async def refer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral link"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_data = db.get_user(user.id)

    if not user_data:
        await query.edit_message_text(
            "❌ User not found. Please use /start first!",
            reply_markup=create_back_button()
        )
        return

    referral_code = user_data['referral_code']
    referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
    total_users = db.get_total_users()

    # Determine rewards based on user count
    if total_users < 500:
        rewards = (
            f"*🎁 PRE-LAUNCH REWARDS*\n\n"
            f"• 5 referrals → Early premium access\n"
            f"• 10 referrals → Lifetime free premium\n"
            f"• 25 referrals → Custom alert settings\n"
            f"• Top 10 → Exclusive perks"
        )
    else:
        rewards = (
            f"*🎁 REFERRAL REWARDS*\n\n"
            f"• 3 referrals → 1 month free premium\n"
            f"• 10 referrals → 6 months free premium\n"
            f"• 25 referrals → Lifetime premium"
        )

    msg = (
        f"╔═══════════════════════╗\n"
        f"   🎁 *REFERRAL LINK*\n"
        f"╚═══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *YOUR LINK*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"`{referral_link}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *YOUR STATS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Total Referrals: *{user_data['total_referrals']}*\n"
        f"Your Code: `{referral_code}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{rewards}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 Share your link to earn rewards!"
    )

    keyboard = [
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}&text=🚀 Check out Base Fair Launch Sniper! Find legit tokens before they moon 🌙")],
        [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
    ]

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral leaderboard"""
    query = update.callback_query
    await query.answer()

    leaders = db.get_leaderboard(limit=10)
    total_users = db.get_total_users()

    leaderboard_text = ""
    medals = ['🥇', '🥈', '🥉']

    for i, leader in enumerate(leaders, 1):
        medal = medals[i-1] if i <= 3 else f"  {i}."
        name = leader['first_name'] or leader['username'] or f"User {leader['user_id']}"
        referrals = leader['total_referrals']
        leaderboard_text += f"{medal} *{name}* - {referrals} referrals\n"

    if not leaders:
        leaderboard_text = "No referrals yet. Be the first!\nUse the referral button to get started."

    msg = (
        f"╔═══════════════════════╗\n"
        f"   🏆 *LEADERBOARD*\n"
        f"╚═══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *COMMUNITY STATS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: *{total_users:,}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 *TOP REFERRERS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{leaderboard_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 Invite friends to climb the ranks!"
    )

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_back_button()
    )

async def alerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle alert notifications"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    new_state = db.toggle_alerts(user.id)

    status_emoji = "✅" if new_state else "❌"
    status_text = "ENABLED" if new_state else "DISABLED"

    msg = (
        f"╔═══════════════════════╗\n"
        f"   🔔 *ALERTS {status_text}*\n"
        f"╚═══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 *NOTIFICATION STATUS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Alerts are now: {status_emoji} *{status_text}*\n\n"
    )

    if new_state:
        msg += (
            f"✅ You'll receive notifications when\n"
            f"   fair launches are detected!\n\n"
            f"📊 *What you'll get:*\n"
            f"• Token name & symbol\n"
            f"• Contract addresses\n"
            f"• Verification results\n"
            f"• Direct Basescan links\n"
        )
    else:
        msg += (
            f"❌ You won't receive alert notifications.\n\n"
            f"💡 Click the button again to re-enable."
        )

    keyboard = [
        [InlineKeyboardButton(f"{'🔕 Disable' if new_state else '🔔 Enable'} Alerts", callback_data="alerts")],
        [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
    ]

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upgrade options"""
    query = update.callback_query
    await query.answer()

    total_users = db.get_total_users()

    if total_users < 500:
        msg = (
            f"╔═══════════════════════╗\n"
            f"  💎 *PREMIUM COMING*\n"
            f"╚═══════════════════════╝\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *PROGRESS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Current Users: *{total_users}* / 500\n"
            f"Progress: {'█' * (total_users // 50)}{'░' * (10 - total_users // 50)} {total_users * 100 // 500}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 *PREMIUM FEATURES*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ Priority alerts (instant)\n"
            f"🎯 Custom filter settings\n"
            f"📈 Historical data access\n"
            f"📊 Advanced analytics\n"
            f"🐋 Whale tracking\n"
            f"⏰ LP unlock warnings\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 *EARLY ACCESS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 Refer friends to unlock premium:\n"
            f"• 10 referrals = Lifetime premium!\n\n"
            f"Use /refer to get your link!"
        )
    else:
        msg = (
            f"╔═══════════════════════╗\n"
            f"   💎 *PREMIUM TIERS*\n"
            f"╚═══════════════════════╝\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆓 *FREE TIER* (Current)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Basic fair launch alerts\n"
            f"✅ Standard verification\n"
            f"✅ 5-minute scan interval\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⭐ *PREMIUM* - $4/month\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ 60-second alerts\n"
            f"🎯 Custom filters\n"
            f"📊 Advanced analytics\n"
            f"🐋 Whale tracking\n"
            f"⏰ LP unlock warnings\n"
            f"📈 Historical data\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 *Get premium FREE:*\n"
            f"Refer 10 users = 6 months free!"
        )

    keyboard = [
        [InlineKeyboardButton("🎁 Get Referral Link", callback_data="refer")],
        [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
    ]

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    query = update.callback_query
    await query.answer()

    msg = (
        f"╔═══════════════════════╗\n"
        f"     ℹ️ *HELP GUIDE*\n"
        f"╚═══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 *COMMANDS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"/start - Start the bot & register\n"
        f"/menu - Show main menu\n"
        f"/stats - View your statistics\n"
        f"/refer - Get referral link\n"
        f"/help - Show this help message\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 *WHAT WE DO*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"We scan Base chain 24/7 for new\n"
        f"token launches and verify:\n\n"
        f"✅ Ownership renounced\n"
        f"✅ Low pre-mine (<5%)\n"
        f"✅ Liquidity locked\n"
        f"✅ No honeypots/scams\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 *SUPPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Join: @base_fair_launch_alerts\n"
        f"Report issues: Contact @admin\n\n"
        f"⚠️ *Always DYOR before investing!*"
    )

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        reply_markup=create_back_button()
    )

# ===== CALLBACK QUERY ROUTER =====

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route callback queries to appropriate handlers"""
    query = update.callback_query

    handlers = {
        'menu': menu,
        'howitworks': howitworks_callback,
        'stats': stats_callback,
        'refer': refer_callback,
        'leaderboard': leaderboard_callback,
        'alerts': alerts_callback,
        'upgrade': upgrade_callback,
        'help': help_callback
    }

    handler = handlers.get(query.data)
    if handler:
        await handler(update, context)
    else:
        await query.answer("Unknown command!")

# ===== MAIN =====

async def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN in .env file!")
        logger.error("Please add: TELEGRAM_BOT_TOKEN=your_token_here")
        return

    logger.info("🚀 Starting Base Fair Launch Sniper Bot...")

    # Create application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_callback))

    # Add callback query handler
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("✅ Bot initialized successfully!")
    logger.info(f"📱 Bot username: @{BOT_USERNAME}")
    logger.info("💬 Send /start in Telegram to test")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Press Ctrl+C to stop")

    # Start polling
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped gracefully")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


