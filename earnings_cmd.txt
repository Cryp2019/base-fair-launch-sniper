async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral earnings and commission stats"""
    user = update.effective_user
    
    # Check if user has commission active
    if not db.is_commission_active(user.id):
        await update.message.reply_text(
            "💰 *REFERRAL EARNINGS*\n\n"
            "You don't have active commissions yet.\n\n"
            "To unlock commissions:\n"
            "1. Refer 10 users who make trades\n"
            "2. Get upgraded to Premium\n"
            "3. Earn 5% of trading fees for 30 days!\n\n"
            "Share your referral link to start earning! 🚀",
            parse_mode='Markdown'
        )
        return
    
    # Get commission stats
    stats = db.get_commission_stats(user.id)
    commissions = db.get_referrer_commissions(user.id)
    
    # Build message
    msg = (
        f"💰 *REFERRAL EARNINGS*\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📊 *STATISTICS*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Total Earned: `{stats['total_earned']:.6f} ETH`\n"
        f"Total Trades: `{stats['total_trades']}`\n"
        f"Days Remaining: `{stats['days_remaining']}`\n\n"
    )
    
    # Show recent commissions
    if commissions:
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += "📝 *RECENT COMMISSIONS*\n"
        msg += "━━━━━━━━━━━━━━━━\n\n"
        
        for i, comm in enumerate(commissions[:5]):  # Show last 5
            msg += f"• `{comm['commission_amount_eth']:.6f} ETH`\n"
            if i >= 4:
                break
    
    msg += "\n━━━━━━━━━━━━━━━━\n"
    msg += "Keep referring to earn more! 🚀"
    
    await update.message.reply_text(msg, parse_mode='Markdown')
