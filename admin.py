#!/usr/bin/env python3
"""
👑 Admin Module for Base Fair Launch Sniper Bot
Provides admin controls, fee management, and user management
"""
import logging
import os
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Admin configuration
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')  # Set this in Railway
TRADING_FEE_PERCENTAGE = float(os.getenv('TRADING_FEE_PERCENTAGE', '0.5'))  # Default 0.5%


class AdminManager:
    def __init__(self, db, w3):
        self.db = db
        self.w3 = w3
        self.admin_id = ADMIN_CHAT_ID
        self.fee_percentage = TRADING_FEE_PERCENTAGE
        self.payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS', '')
        self.fee_wallet = os.getenv('FEE_COLLECTION_WALLET', self.payment_wallet)  # Can be different
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return str(user_id) == str(self.admin_id)
    
    def calculate_trading_fee(self, eth_amount: float) -> Dict:
        """Calculate trading fee from ETH amount"""
        fee_amount = eth_amount * (self.fee_percentage / 100)
        net_amount = eth_amount - fee_amount
        
        return {
            'gross_amount': eth_amount,
            'fee_amount': fee_amount,
            'net_amount': net_amount,
            'fee_percentage': self.fee_percentage
        }
    
    def update_payment_address(self, new_address: str) -> Dict:
        """Update payment wallet address"""
        try:
            # Validate address
            checksum_address = self.w3.to_checksum_address(new_address)
            
            # Update in environment (note: this only updates runtime, not Railway config)
            os.environ['PAYMENT_WALLET_ADDRESS'] = checksum_address
            self.payment_wallet = checksum_address
            
            return {
                'success': True,
                'address': checksum_address,
                'message': 'Payment address updated! Remember to update Railway env var.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Invalid address: {str(e)}'
            }
    
    def update_fee_percentage(self, new_percentage: float) -> Dict:
        """Update trading fee percentage"""
        try:
            if new_percentage < 0 or new_percentage > 10:
                return {
                    'success': False,
                    'message': 'Fee must be between 0% and 10%'
                }
            
            self.fee_percentage = new_percentage
            os.environ['TRADING_FEE_PERCENTAGE'] = str(new_percentage)
            
            return {
                'success': True,
                'percentage': new_percentage,
                'message': f'Trading fee updated to {new_percentage}%'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_admin_stats(self) -> Dict:
        """Get comprehensive admin statistics"""
        try:
            # Get all users
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Premium users
            cursor.execute("SELECT COUNT(*) FROM users WHERE tier = 'premium'")
            premium_users = cursor.fetchone()[0]
            
            # Total referrals
            cursor.execute("SELECT SUM(referral_count) FROM users")
            total_referrals = cursor.fetchone()[0] or 0
            
            # Total wallets created
            cursor.execute("SELECT COUNT(*) FROM wallets")
            total_wallets = cursor.fetchone()[0]
            
            # Get fee collection stats (would need to track in database)
            # For now, return placeholder
            total_fees_collected = 0.0  # Would track this in trades table
            
            conn.close()
            
            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'free_users': total_users - premium_users,
                'total_referrals': total_referrals,
                'total_wallets': total_wallets,
                'total_fees_collected': total_fees_collected,
                'current_fee_percentage': self.fee_percentage,
                'payment_wallet': self.payment_wallet,
                'fee_wallet': self.fee_wallet
            }
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {}
    
    def grant_premium(self, user_id: int, duration_days: int = 365) -> Dict:
        """Manually grant premium to a user"""
        try:
            # Update user tier
            self.db.upgrade_to_premium(user_id)
            
            return {
                'success': True,
                'message': f'Premium granted to user {user_id} for {duration_days} days'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def broadcast_message(self, message: str) -> Dict:
        """Broadcast message to all users (returns user IDs to send to)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT user_id FROM users")
            user_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'user_ids': user_ids,
                'total_users': len(user_ids)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

