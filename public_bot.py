#!/usr/bin/env python3
"""
Working Telegram bot with referral system
Compatible with python-telegram-bot 20.x
"""
import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from database import UserDatabase

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = "base_fair_launch_bot"

# Initialize database
db = UserDatabase()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===== BOT COMMANDS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and user registration"""
    user = update.effective_user
    args = context.args
    
    # Check if user came from referral link
    referrer_code = args[0] if args else None
    
    # Add user to database
    result = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referrer_code=referrer_code
    )
    
    # Get total users
    total_users = db.get_total_users()
    
    welcome_msg = (
        f"🔍 *Welcome to Base Fair Launch Sniper!*\n\n"
        f"Hi {user.first_name}! I help you find *truly* fair-launched tokens on Base chain.\n\n"
        f"✅ Renounced ownership\n"
        f"✅ <5% pre-mine\n"
        f"✅ Locked liquidity (30+ days)\n"
        f"✅ No suspicious tax functions\n\n"
        f"👥 *Community:* {total_users} users\n"
        f"🎁 *Your Status:* Free Tier\n\n"
        f"⚠️ *DISCLAIMER:* Not financial advice. Most new tokens fail. Always DYOR.\n\n"
        f"*Commands:*\n"
        f"/refer - Get your referral link & earn rewards\n"
        f"/stats - View your stats & referrals\n"
        f"/leaderboard - Top referrers\n"
        f"/howitworks - Learn about verification\n"
        f"/alerts - Toggle alert notifications\n\n"
    )
    
    if result['success'] and result.get('referred_by'):
        welcome_msg += f"✨ You were referred by user {result['referred_by']}!\n"
    
    if total_users >= 500:
        welcome_msg += f"\n🎉 *We've reached 500+ users!* Premium tiers now available. /upgrade for details."
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and share referral link"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("Please use /start first to register!")
        return
    
    referral_code = user_data['referral_code']
    referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"
    
    total_users = db.get_total_users()
    
    if total_users < 500:
        rewards_msg = (
            f"\n🎁 *Referral Rewards (Pre-Launch):*\n"
            f"• Refer 5 users → Early access to premium features\n"
            f"• Refer 10 users → Lifetime free premium\n"
            f"• Refer 25 users → Custom alert settings\n"
            f"• Top 10 referrers → Exclusive perks\n"
        )
    else:
        rewards_msg = (
            f"\n🎁 *Referral Rewards:*\n"
            f"• Refer 3 users → 1 month free premium\n"
            f"• Refer 10 users → 6 months free premium\n"
            f"• Refer 25 users → Lifetime premium\n"
        )
    
    msg = (
        f"🔗 *Your Referral Link*\n\n"
        f"`{referral_link}`\n\n"
        f"📊 *Your Stats:*\n"
        f"• Total Referrals: {user_data['total_referrals']}\n"
        f"• Your Code: `{referral_code}`\n"
        f"{rewards_msg}\n"
        f"💡 Share this link with friends to earn rewards!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Check out this Base Fair Launch Sniper bot! 🔍")]
    ]
    
    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user = update.effective_user
    user_stats = db.get_user_stats(user.id)
    
    if not user_stats:
        await update.message.reply_text("Please use /start first to register!")
        return
    
    user_data = user_stats['user']
    referrals = user_stats['referrals']
    
    msg = (
        f"📊 *Your Statistics*\n\n"
        f"👤 *User:* {user_data['first_name']}\n"
        f"🆔 *User ID:* `{user_data['user_id']}`\n"
        f"📅 *Joined:* {user_data['joined_date'][:10]}\n"
        f"🎁 *Tier:* {user_data['tier'].capitalize()}\n"
        f"🔔 *Alerts:* {'Enabled' if user_data['alerts_enabled'] else 'Disabled'}\n\n"
        f"👥 *Referrals:* {user_data['total_referrals']}\n"
    )
    
    if referrals:
        msg += f"\n*Recent Referrals:*\n"
        for i, ref in enumerate(referrals[:5], 1):
            msg += f"{i}. {ref['first_name']} (@{ref['username'] or 'no username'})\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top referrers"""
    leaders = db.get_leaderboard(limit=10)
    total_users = db.get_total_users()
    
    msg = (
        f"🏆 *Referral Leaderboard*\n\n"
        f"👥 Total Users: {total_users}\n\n"
    )
    
    medals = ['🥇', '🥈', '🥉']
    for i, leader in enumerate(leaders, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = leader['first_name'] or leader['username'] or f"User {leader['user_id']}"
        msg += f"{medal} {name} - {leader['total_referrals']} referrals\n"
    
    if not leaders:
        msg += "No referrals yet. Be the first! Use /refer to get your link.\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def alerts_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle alert notifications"""
    user = update.effective_user
    new_state = db.toggle_alerts(user.id)
    
    status = "enabled ✅" if new_state else "disabled ❌"
    msg = f"🔔 Alerts have been {status}\n\n"
    
    if new_state:
        msg += "You'll now receive notifications when fair launches are detected!"
    else:
        msg += "You won't receive alert notifications. Use /alerts again to re-enable."
    
    await update.message.reply_text(msg)

async def howitworks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain verification process"""
    msg = (
        "🛡️ *How Fair Launch Verification Works:*\n\n"
        "1️⃣ *Ownership Check*\n"
        "   → Confirms contract ownership sent to burn address\n\n"
        "2️⃣ *Pre-mine Analysis*\n"
        "   → Checks creator wallet holds <5% of supply\n\n"
        "3️⃣ *Liquidity Lock*\n"
        "   → Verifies LP tokens locked via Unicrypt/Team Finance\n\n"
        "4️⃣ *Tax Screening*\n"
        "   → Flags contracts with hidden tax functions\n\n"
        "⚠️ *Limitations:* Cannot detect all honeypots. Always test with small amounts first.\n\n"
        "🤖 *Automated Scanning:*\n"
        "• Scans Base chain every 5 minutes\n"
        "• Monitors Uniswap V3 for new USDC pairs\n"
        "• Sends instant alerts for fair launches"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upgrade options"""
    total_users = db.get_total_users()
    
    if total_users < 500:
        msg = (
            f"🚀 *Premium Tiers Coming Soon!*\n\n"
            f"We're currently at {total_users}/500 users.\n\n"
            f"When we reach 500 users, premium tiers will unlock:\n"
            f"• Priority alerts (get notified first)\n"
            f"• Custom filter settings\n"
            f"• Historical data access\n"
            f"• Advanced analytics\n\n"
            f"💡 Use /refer to invite friends and earn lifetime premium!"
        )
    else:
        msg = (
            f"💎 *Premium Tiers*\n\n"
            f"🆓 *Free Tier* (Current)\n"
            f"• Basic fair launch alerts\n"
            f"• Standard verification\n"
            f"• 5-minute scan interval\n\n"
            f"⭐ *Premium Tier* ($9.99/month)\n"
            f"• Priority alerts (instant)\n"
            f"• Custom filter settings\n"
            f"• 1-minute scan interval\n"
            f"• Historical data access\n"
            f"• Advanced analytics dashboard\n\n"
            f"🔗 Upgrade: [Payment Link]\n"
            f"💡 Or refer 10 users for 6 months free!"
        )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# ===== MAIN =====
def main():
    if not TELEGRAM_TOKEN:
        logging.error("Missing TELEGRAM_BOT_TOKEN in .env")
        return
    
    logging.info("🚀 Starting Base Fair Launch Sniper Bot...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("alerts", alerts_toggle))
    app.add_handler(CommandHandler("howitworks", howitworks))
    app.add_handler(CommandHandler("upgrade", upgrade))
    
    logging.info("✅ Bot started successfully!")
    logging.info(f"📱 Bot username: @{BOT_USERNAME}")
    logging.info("💬 Send /start in Telegram to test")
    logging.info("Press Ctrl+C to stop")
    
    # Start polling (blocking call)
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
