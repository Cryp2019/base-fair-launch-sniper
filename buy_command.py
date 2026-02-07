async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command for buying tokens
    Usage: /buy <token_address> <amount_eth>
    Example: /buy 0x1234567890abcdef1234567890abcdef12345678 0.1
    """
    user = update.effective_user
    
    # Check if command is from a group
    if is_group_chat(update):
        # Delete the user's command message for privacy
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete message in group: {e}")
            # If we can't delete, warn user to use DM
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=(
                        "⚠️ *Privacy Warning*\\n\\n"
                        "I couldn't delete your /buy command in the group.\\n"
                        "For privacy, please use /buy in a private message with me.\\n\\n"
                        "This keeps your wallet address hidden from others."
                    ),
                    parse_mode='Markdown'
                )
            except:
                pass
            return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Invalid Format*\\n\\n"
            "Usage: `/buy <token_address> <amount_eth>`\\n\\n"
            "Example:\\n"
            "`/buy 0x1234...5678 0.1`\\n\\n"
            "• Token address (required)\\n"
            "• ETH amount (required)",
            parse_mode='Markdown'
        )
        return
    
    token_address = context.args[0]
    
    try:
        eth_amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Amount*\\n\\n"
            f"'{context.args[1]}' is not a valid number.\\n\\n"
            "Example: `/buy 0x1234...5678 0.1`",
            parse_mode='Markdown'
        )
        return
    
    # Validate token address format
    if not token_address.startswith('0x') or len(token_address) != 42:
        await update.message.reply_text(
            "❌ *Invalid Token Address*\\n\\n"
            "Token address must be a valid Ethereum address.\\n\\n"
            "Example: `0x1234567890abcdef1234567890abcdef12345678`",
            parse_mode='Markdown'
        )
        return
    
    # Validate amount
    if eth_amount <= 0:
        await update.message.reply_text(
            "❌ *Invalid Amount*\\n\\n"
            "Amount must be greater than 0.",
            parse_mode='Markdown'
        )
        return
    
    # Check if user has a wallet
    wallets = db.get_user_wallets(user.id)
    if not wallets:
        await update.message.reply_text(
            "❌ *No Wallet Found*\\n\\n"
            "You need to create a wallet first.\\n"
            "Use /start to create one.",
            parse_mode='Markdown'
        )
        return
    
    wallet_address = wallets[0]['wallet_address']
    private_key = db.get_wallet_private_key(user.id, wallet_address)
    
    if not private_key:
        await update.message.reply_text(
            "❌ *Wallet Error*\\n\\n"
            "Could not retrieve your wallet. Please contact support.",
            parse_mode='Markdown'
        )
        return
    
    # Check wallet balance
    try:
        balance = w3.eth.get_balance(wallet_address)
        balance_eth = balance / 10**18
        
        if balance_eth < eth_amount:
            await update.message.reply_text(
                f"❌ *Insufficient Balance*\\n\\n"
                f"You have: `{balance_eth:.4f} ETH`\\n"
                f"You need: `{eth_amount} ETH`\\n\\n"
                f"Please deposit more ETH to your wallet:\\n"
                f"`{wallet_address}`",
                parse_mode='Markdown'
            )
            return
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        await update.message.reply_text(
            "❌ *Error*\\n\\n"
            "Could not check your wallet balance. Please try again.",
            parse_mode='Markdown'
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"⏳ *EXECUTING BUY ORDER...*\\n\\n"
        f"Token: `{token_address}`\\n"
        f"Amount: *{eth_amount} ETH*\\n\\n"
        f"Please wait...",
        parse_mode='Markdown'
    )
    
    # Execute buy with fee
    try:
        result = trading_bot.buy_token(
            token_address,
            private_key,
            eth_amount,
            fee_wallet=admin_manager.fee_wallet,
            fee_percentage=admin_manager.fee_percentage
        )
        
        if result['success']:
            # Mark user as having traded (for referral tracking)
            referrer_id = db.mark_user_traded(user.id)
            
            # Check if referrer should be upgraded to premium
            if referrer_id:
                if db.check_and_upgrade_premium(referrer_id):
                    # Notify referrer they got premium
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=(
                                "🎉 *CONGRATULATIONS!*\\n\\n"
                                "One of your referrals just made their first trade!\\n"
                                "You've reached *10 active referrals*!\\n\\n"
                                "✅ You've been upgraded to *PREMIUM* for 1 month! 💎"
                            ),
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            # Send success message
            await processing_msg.edit_text(
                f"✅ *BUY ORDER SUCCESSFUL!*\\n\\n"
                f"Token: `{token_address}`\\n"
                f"Amount: *{eth_amount} ETH*\\n"
                f"Tokens Received: *{result.get('tokens_received', 'N/A')}*\\n\\n"
                f"Transaction Hash:\\n"
                f"`{result['tx_hash']}`\\n\\n"
                f"[View on Basescan](https://basescan.org/tx/{result['tx_hash']})",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            await processing_msg.edit_text(
                f"❌ *BUY ORDER FAILED*\\n\\n"
                f"Error: {result.get('error', 'Unknown error')}\\n\\n"
                f"Please try again or contact support.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Buy command error: {e}")
        await processing_msg.edit_text(
            f"❌ *BUY ORDER FAILED*\\n\\n"
            f"Error: {str(e)}\\n\\n"
            f"Please try again or contact support.",
            parse_mode='Markdown'
        )
