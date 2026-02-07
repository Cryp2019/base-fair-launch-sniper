"""
Group Poster Module
Posts good-rated projects with Buy Now button to Telegram groups
"""
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from security_scanner import SecurityScanner
from trading import TradingBot

logger = logging.getLogger(__name__)

class GroupPoster:
    def __init__(self, w3=None):
        # Initialize with optional web3 instance
        if w3:
            self.scanner = SecurityScanner(w3)
            self.trading = TradingBot(w3)
        else:
            # For standalone use, try to initialize with default web3
            try:
                from web3 import Web3
                default_w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
                self.scanner = SecurityScanner(default_w3)
                self.trading = TradingBot(default_w3)
            except:
                # Fallback: create minimal instance
                self.scanner = None
                self.trading = None
        
        self.min_rating_score = 75  # Only post projects with 75+ score
    
    def format_project_message(self, project: dict, rating: dict) -> str:
        """Format project data into a nice Telegram message"""
        token_name = project.get('name', 'Unknown')
        contract = project.get('contract', 'N/A')
        launch_time = project.get('launch_time', 'N/A')
        dex = project.get('dex', 'Uniswap')
        liquidity = project.get('liquidity_usd', 0)
        market_cap = project.get('market_cap', 0)
        score = rating.get('score', 0)
        risk_level = rating.get('risk_level', 'Unknown')
        
        return f"""
🚀 <b>NEW FAIR LAUNCH DETECTED</b>

<b>Token:</b> {token_name}
<b>Contract:</b> <code>{contract[:20]}...</code>
<b>DEX:</b> {dex}

💰 <b>MARKET DATA:</b>
• Liquidity: ${liquidity:,.0f}
• Market Cap: ${market_cap:,.0f}
• Launch: {launch_time}

🛡️ <b>SECURITY RATING:</b> {score}/100
<b>Risk Level:</b> {risk_level.upper()}

✅ <b>Status:</b> VERIFIED & SAFE TO BUY

<b>Chain:</b> Base Network
<b>Type:</b> Fair Launch
"""
    
    def get_buy_button(self, contract_address: str, project_id: str) -> InlineKeyboardMarkup:
        """Create Buy Now button with callback"""
        keyboard = [
            [InlineKeyboardButton("💳 BUY NOW", callback_data=f"buy_{contract_address}_{project_id}")],
            [InlineKeyboardButton("📊 Chart", url=f"https://dexscreener.com/base/{contract_address}"),
             InlineKeyboardButton("ℹ️ Info", url=f"https://basescan.org/token/{contract_address}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def should_post_project(self, project: dict) -> tuple:
        """
        Check if project meets posting criteria
        Returns: (should_post: bool, rating: dict)
        """
        try:
            if not self.scanner:
                logger.warning("Scanner not initialized")
                return False, {}
            
            contract_address = project.get('contract')
            if not contract_address:
                return False, {}
            
            rating = self.scanner.get_project_rating(contract_address)
            
            # Only post if rating score is 75 or higher
            if rating.get('score', 0) >= self.min_rating_score:
                return True, rating
            else:
                logger.info(f"Project {contract_address} rated {rating.get('score')} - below threshold")
                return False, rating
        except Exception as e:
            logger.error(f"Error checking project: {e}")
            return False, {}
    
    async def post_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE, project: dict) -> bool:
        """Post good-rated project to group with Buy button"""
        should_post, rating = self.should_post_project(project)
        
        if not should_post:
            logger.info(f"Project {project.get('contract')} filtered out - low rating")
            return False
        
        try:
            # Format message
            message_text = self.format_project_message(project, rating)
            
            # Create Buy button
            reply_markup = self.get_buy_button(
                project.get('contract'),
                project.get('id', 'unknown')
            )
            
            # Send to group
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            logger.info(f"Posted project {project.get('contract')} to group {update.effective_chat.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting to group: {e}")
            return False
    
    async def handle_buy_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle Buy Now button click"""
        query = update.callback_query
        await query.answer("Processing buy order...")
        
        try:
            # Extract contract and project ID from callback data
            callback_data = query.data
            parts = callback_data.split('_')
            
            if len(parts) < 3:
                await query.edit_message_text(
                    text="❌ Invalid button data",
                    parse_mode='HTML'
                )
                return
            
            contract_address = parts[1]
            project_id = '_'.join(parts[2:])
            user_id = update.effective_user.id
            
            # Execute buy
            result = self.trading.execute_buy(
                contract_address=contract_address,
                amount_eth=0.1,  # Default amount
                user_id=user_id
            )
            
            if result.get('success'):
                tx_hash = result.get('tx_hash', 'N/A')
                tx_short = tx_hash[:20] + '...' if len(str(tx_hash)) > 20 else tx_hash
                
                await query.edit_message_text(
                    text=f"✅ <b>BUY EXECUTED!</b>\n\n"
                         f"<b>TX Hash:</b> <code>{tx_short}</code>\n"
                         f"<b>Status:</b> {result.get('status', 'pending').upper()}\n"
                         f"<b>Amount:</b> 0.1 ETH\n\n"
                         f"🔗 <a href='https://basescan.org/tx/{tx_hash}'>View on Basescan</a>",
                    parse_mode='HTML'
                )
                logger.info(f"User {user_id} successfully bought {contract_address}")
            else:
                error_msg = result.get('error', 'Unknown error')
                await query.edit_message_text(
                    text=f"❌ <b>BUY FAILED</b>\n\n"
                         f"<b>Error:</b> {error_msg}",
                    parse_mode='HTML'
                )
                logger.error(f"Buy failed for user {user_id}: {error_msg}")
        except Exception as e:
            logger.error(f"Error processing buy: {e}")
            await query.edit_message_text(
                text=f"❌ Error processing buy: {str(e)}",
                parse_mode='HTML'
            )
