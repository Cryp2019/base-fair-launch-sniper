"""
Top Performers Command Handler
Shows the best performing tokens that just launched
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application
from datetime import datetime

logger = logging.getLogger(__name__)

async def top_performers_command(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 sponsored_projects=None):
    """Show top performing tokens from the last 24 hours"""
    
    if not sponsored_projects:
        await update.message.reply_text(
            "⚠️ Top performers feature temporarily unavailable.\n"
            "Check back soon for the best performing launches!"
        )
        return
    
    user = update.effective_user
    logger.info(f"📊 {user.first_name} requested top performers")
    
    # Get top performers from last 24 hours
    performers = sponsored_projects.get_top_performers(limit=15, hours=24)
    
    if not performers:
        await update.message.reply_text(
            "📊 <b>TOP PERFORMERS</b>\n\n"
            "No high-performing tokens found in the last 24 hours.\n"
            "Check back soon!",
            parse_mode='HTML'
        )
        return
    
    # Build message
    msg = "📊 <b>TOP PERFORMERS (Last 24 Hours)</b>\n\n"
    msg += "🚀 Best performing launches from Base network:\n\n"
    
    for i, token in enumerate(performers, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
        
        symbol = token['token_symbol']
        price_change = token['price_increase_percent']
        
        # Color emoji based on performance
        if price_change > 500:
            perf_emoji = "🚀🚀🚀"
        elif price_change > 200:
            perf_emoji = "🚀🚀"
        elif price_change > 100:
            perf_emoji = "🚀"
        elif price_change > 0:
            perf_emoji = "📈"
        else:
            perf_emoji = "📉"
        
        # Format market cap
        mc = token['market_cap']
        if mc >= 1_000_000:
            mc_str = f"${mc/1_000_000:.1f}M"
        elif mc >= 1_000:
            mc_str = f"${mc/1_000:.1f}K"
        else:
            mc_str = f"${mc:.2f}"
        
        # Format volume
        vol = token['volume_24h']
        if vol >= 1_000_000:
            vol_str = f"${vol/1_000_000:.1f}M"
        elif vol >= 1_000:
            vol_str = f"${vol/1_000:.1f}K"
        else:
            vol_str = f"${vol:.2f}"
        
        msg += f"{emoji} <b>{token['token_name']}</b> ({symbol})\n"
        msg += f"   {perf_emoji} <code>+{price_change:.1f}%</code>\n"
        msg += f"   💰 MC: {mc_str} | Vol: {vol_str}\n"
        msg += f"   👥 {token['holder_count']:,} holders | 🛡️ {token['security_score']}/100\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "💡 Tip: Use /featured to promote your project and get featured!"
    
    # Create button to request features
    keyboard = [
        [InlineKeyboardButton("⭐ Get Featured", callback_data="featured_info"),
         InlineKeyboardButton("🔄 Refresh", callback_data="top_performers")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=reply_markup)


async def featured_projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show sponsorship packages and how to get featured"""
    
    user = update.effective_user
    logger.info(f"⭐ {user.first_name} requested sponsorship info")
    
    from sponsored_projects import format_ad_rates_message
    
    msg = format_ad_rates_message()
    
    # Add contact button
    keyboard = [
        [InlineKeyboardButton("💬 Contact Support", url="https://t.me/support")],
        [InlineKeyboardButton("📊 View Top Performers", callback_data="top_performers"),
         InlineKeyboardButton("🏠 Back to Menu", callback_data="start_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=reply_markup)


def register_top_performers_handlers(app: Application, sponsored_projects=None):
    """Register handlers for top performers and sponsorship commands"""
    from telegram.ext import CommandHandler, CallbackQueryHandler
    
    # Command handlers
    async def top_performers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await top_performers_command(update, context, sponsored_projects)
    
    async def featured_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await featured_projects_command(update, context)
    
    # Callback query handlers
    async def top_performers_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Create temporary message to show loading
        await top_performers_command(query, context, sponsored_projects)
    
    async def featured_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        from sponsored_projects import format_ad_rates_message
        msg = format_ad_rates_message()
        
        keyboard = [
            [InlineKeyboardButton("💬 Contact Support", url="https://t.me/support")],
            [InlineKeyboardButton("📊 Top Performers", callback_data="top_performers")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=reply_markup)
    
    # Register handlers
    app.add_handler(CommandHandler('top', top_performers_handler))
    app.add_handler(CommandHandler('featured', featured_handler))
    app.add_handler(CallbackQueryHandler(top_performers_callback, pattern='top_performers'))
    app.add_handler(CallbackQueryHandler(featured_info_callback, pattern='featured_info'))
    
    logger.info("✅ Top performers handlers registered")
