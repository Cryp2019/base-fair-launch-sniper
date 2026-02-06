"""
Enhanced handle_token_input function with comprehensive security scan
Copy this code to replace the existing handle_token_input function in sniper_bot.py (around line 1588)
"""

async def handle_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's token contract address input with comprehensive security scan"""
    user = update.effective_user
    text = update.message.text.strip()

    # Check if user is waiting for snipe input
    if context.user_data.get('waiting_for_snipe'):
        await handle_snipe_input(update, context, text)
        return

    # Check if user is waiting for token input
    if not context.user_data.get('waiting_for_token'):
        return

    # Clear the waiting state
    context.user_data['waiting_for_token'] = False

    # Validate address format
    if not text.startswith('0x') or len(text) != 42:
        await update.message.reply_text(
            "❌ Invalid address format!\n\n"
            "Please send a valid Ethereum address:\n"
            "`0x1234567890abcdef1234567890abcdef12345678`\n\n"
            "Use /start to try again.",
            parse_mode='Markdown'
        )
        return

    # Send "analyzing" message
    analyzing_msg = await update.message.reply_text("🔍 Analyzing token... Please wait...")

    try:
        # Check if user is premium
        user_data = db.get_user(user.id)
        is_premium = user_data and user_data['tier'] == 'premium'

        # Get token contract
        token_address = w3.to_checksum_address(text)
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

        # Get basic token info
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            total_supply = token_contract.functions.totalSupply().call()
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            await analyzing_msg.edit_text(
                "❌ *Error: Not a valid ERC20 token*\n\n"
                "This contract doesn't appear to be a standard token.\n\n"
                f"Error: `{str(e)[:100]}`",
                parse_mode='Markdown'
            )
            return

        # Check ownership
        owner = "Unknown"
        renounced = False
        try:
            owner = token_contract.functions.owner().call()
            burn_addresses = [
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000001",
                "0x000000000000000000000000000000000000dEaD"
            ]
            renounced = owner.lower() in [a.lower() for a in burn_addresses]
        except:
            renounced = True  # No owner function = likely renounced
            owner = "No owner function (likely renounced)"

        # Format supply
        supply_formatted = total_supply / (10 ** decimals)

        # ===== COMPREHENSIVE METRICS =====
        metrics = {
            'price_usd': 0,
            'market_cap': 0,
            'liquidity_usd': 0,
            'volume_24h': 0,
            'ath': None,
            'has_limits': False,
            'limit_details': 'No limits',
            'clog_percentage': 0.03,
            'airdrops': []
        }
        
        # Try to fetch comprehensive metrics
        try:
            # Get DexScreener data
            dex_data = await get_dexscreener_data(token_address)
            metrics.update(dex_data)
            
            # Get transfer limits
            limits = await check_transfer_limits(token_address)
            metrics['has_limits'] = limits['has_limits']
            metrics['limit_details'] = limits['details']
            
            # Get clog percentage
            metrics['clog_percentage'] = await calculate_clog_percentage(token_address, token_address)
            
            # Detect airdrops (premium only)
            if is_premium:
                metrics['airdrops'] = await detect_airdrops(token_address)
        except Exception as e:
            logger.debug(f"Could not fetch all metrics: {e}")

        # ===== SECURITY SCAN =====
        is_honeypot = False
        buy_tax = 0
        sell_tax = 0
        transfer_tax = 0
        liquidity_locked = False
        lock_days = 0
        locker_name = "Unknown"
        
        try:
            from security_scanner import SecurityScanner
            scanner = SecurityScanner(w3)
            
            # Check honeypot
            honeypot_result = scanner.check_honeypot(token_address)
            is_honeypot = honeypot_result.get('is_honeypot', False)
            buy_tax = honeypot_result.get('buy_tax', 0)
            sell_tax = honeypot_result.get('sell_tax', 0)
            
            # Check liquidity lock
            lock_result = scanner.check_liquidity_lock(token_address)
            liquidity_locked = lock_result.get('is_locked', False)
            lock_days = lock_result.get('lock_days', 0)
            locker_name = lock_result.get('locker_name', 'Unknown')
        except Exception as e:
            logger.debug(f"Security scan failed: {e}")

        total_tax = buy_tax + sell_tax + transfer_tax

        # Format numbers
        def format_number(num):
            if num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"${num/1_000:.2f}K"
            else:
                return f"${num:.2f}"

        mc_str = format_number(metrics['market_cap']) if metrics['market_cap'] > 0 else "N/A"
        ath_str = format_number(metrics['ath']) if metrics.get('ath') and is_premium else ("Premium Only" if not is_premium else "N/A")
        liq_str = format_number(metrics['liquidity_usd']) if metrics['liquidity_usd'] > 0 else "N/A"
        price_str = f"${metrics['price_usd']:.8f}" if metrics['price_usd'] > 0 else "N/A"
        vol_str = format_number(metrics['volume_24h']) if metrics['volume_24h'] > 0 else "N/A"

        # Build response message
        status_emoji = "✅" if renounced else "⚠️"
        airdrop_str = ", ".join(metrics['airdrops']) if is_premium and metrics['airdrops'] else ("None detected" if is_premium else "Premium Only")

        msg = (
            f"╔═══════════════════════╗\n"
            f"   🔍 *TOKEN ANALYSIS*\n"
            f"╚═══════════════════════╝\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *TOKEN INFO*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Name: *{name}*\n"
            f"Symbol: *${symbol.upper()}*\n"
            f"Decimals: *{decimals}*\n"
            f"Total Supply: *{supply_formatted:,.0f}*\n\n"
            f"🧢 MC: {mc_str}     | ATH: {ath_str}\n"
            f"💧 Liq: {liq_str}\n"
            f"🏷 Price: {price_str}\n"
            f"🎚 Vol: {vol_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ *SAFETY CHECKS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{status_emoji} Ownership: *{'Renounced ✅' if renounced else 'NOT Renounced ⚠️'}*\n"
            f"{'✅' if not is_honeypot else '🚨'} Honeypot: *{'SAFE' if not is_honeypot else 'DETECTED ⚠️'}*\n"
            f"{'✅' if liquidity_locked else '❌'} LP Locked: *{'YES' if liquidity_locked else 'NO'}*"
        )

        if liquidity_locked:
            msg += f"\n   └ {lock_days} days via {locker_name}"

        msg += (
            f"\n\n🏧 B: {buy_tax:.2f}% | S: {sell_tax:.2f}% | T: {total_tax:.2f}%\n"
            f"⚖️ {metrics['limit_details']}\n"
            f"🪠 Clog: {metrics['clog_percentage']:.2f}%\n\n"
        )

        if is_premium:
            msg += f"🪂 Airdrops: {airdrop_str}\n\n"
        else:
            msg += f"💡 *Upgrade to Premium* for ATH tracking & airdrop detection!\n\n"

        msg += (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 *CONTRACT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`{token_address}`\n\n"
            f"⚠️ *DYOR! Not financial advice.*\n"
            f"Always verify before investing!"
        )

        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔍 View on Basescan", url=f"https://basescan.org/token/{token_address}"),
            ],
            [
                InlineKeyboardButton("📊 DexScreener", url=f"https://dexscreener.com/base/{token_address}"),
                InlineKeyboardButton("🦄 Uniswap", url=f"https://app.uniswap.org/#/tokens/base/{token_address}")
            ],
            [
                InlineKeyboardButton("« Back to Menu", callback_data="menu")
            ]
        ]

        await analyzing_msg.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Token analysis error: {e}")
        await analyzing_msg.edit_text(
            f"❌ *Error analyzing token*\n\n"
            f"Could not analyze this contract. Make sure:\n"
            f"• Address is correct\n"
            f"• Token is on Base chain\n"
            f"• Contract is verified\n\n"
            f"Error: `{str(e)[:100]}`",
            parse_mode='Markdown'
        )
