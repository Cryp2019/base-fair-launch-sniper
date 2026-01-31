#!/usr/bin/env python3
"""
💰 Payment Monitor for Base Fair Launch Sniper Bot
Automatically detects USDC payments and upgrades users to premium
"""
import logging
import asyncio
from web3 import Web3
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# USDC on Base
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

# ERC20 ABI for Transfer events
ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class PaymentMonitor:
    def __init__(self, w3: Web3, db, payment_wallet: str, bot_app):
        self.w3 = w3
        self.db = db
        self.payment_wallet = Web3.to_checksum_address(payment_wallet)
        self.bot_app = bot_app
        self.usdc_contract = w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS),
            abi=ERC20_ABI
        )
        self.processed_txs = set()  # Track processed transactions
        
    async def start_monitoring(self):
        """Start monitoring for USDC payments"""
        logger.info(f"💰 Starting payment monitor for wallet: {self.payment_wallet}")
        
        # Get current block
        last_block = self.w3.eth.block_number
        
        while True:
            try:
                current_block = self.w3.eth.block_number
                
                if current_block > last_block:
                    # Check for new USDC transfers to payment wallet
                    await self.check_payments(last_block + 1, current_block)
                    last_block = current_block
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Payment monitor error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def check_payments(self, from_block: int, to_block: int):
        """Check for USDC payments in block range"""
        try:
            # Get Transfer events to our payment wallet
            transfer_filter = self.usdc_contract.events.Transfer.create_filter(
                fromBlock=from_block,
                toBlock=to_block,
                argument_filters={'to': self.payment_wallet}
            )
            
            events = transfer_filter.get_all_entries()
            
            for event in events:
                await self.process_payment(event)
                
        except Exception as e:
            logger.error(f"Error checking payments: {e}")
    
    async def process_payment(self, event):
        """Process a USDC payment and upgrade user if valid"""
        try:
            tx_hash = event['transactionHash'].hex()
            
            # Skip if already processed
            if tx_hash in self.processed_txs:
                return
            
            # Get payment details
            from_address = event['args']['from']
            amount_raw = event['args']['value']
            amount_usdc = amount_raw / 1e6  # USDC has 6 decimals
            
            logger.info(f"💰 Payment detected: {amount_usdc} USDC from {from_address}")
            
            # Check if payment is >= 4 USDC
            if amount_usdc >= 4.0:
                # Try to find user by wallet address
                user_id = self.db.get_user_by_wallet(from_address)
                
                if user_id:
                    # Upgrade user to premium
                    self.db.update_tier(user_id, 'premium')
                    logger.info(f"✅ Auto-upgraded user {user_id} to premium!")
                    
                    # Notify user
                    try:
                        await self.bot_app.bot.send_message(
                            chat_id=user_id,
                            text=(
                                "🎉 *PAYMENT CONFIRMED!*\n\n"
                                "✅ You've been upgraded to *PREMIUM*! 💎\n\n"
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                "⭐ *PREMIUM FEATURES UNLOCKED*\n"
                                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                                "✓ Advanced analytics\n"
                                "✓ Initial liquidity data\n"
                                "✓ Priority alerts (5-10s faster)\n"
                                "✓ Premium badge 💎\n\n"
                                f"Payment: {amount_usdc:.2f} USDC\n"
                                f"TX: `{tx_hash}`\n\n"
                                "Thank you for your support! 🚀"
                            ),
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify user {user_id}: {e}")
                else:
                    logger.warning(f"⚠️ Payment from unknown wallet: {from_address}")
                    # Could store this for manual processing
            
            # Mark as processed
            self.processed_txs.add(tx_hash)
            
        except Exception as e:
            logger.error(f"Error processing payment: {e}")

