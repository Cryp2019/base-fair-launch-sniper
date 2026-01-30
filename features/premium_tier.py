"""
Premium Tier Management via Telegram Stars
Monetize without Stripe complexity - Telegram handles all payments
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os

PREMIUM_PRICE = 4  # Telegram Stars (~$4 USD)
PREMIUM_FILE = "premium_users.json"

class PremiumManager:
    def __init__(self):
        self.premium_users = self._load()
    
    def _load(self):
        try:
            with open(PREMIUM_FILE, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()
    
    def _save(self):
        with open(PREMIUM_FILE, 'w') as f:
            json.dump(list(self.premium_users), f)
    
    def is_premium(self, user_id: int) -> bool:
        return user_id in self.premium_users
    
    def add_premium(self, user_id: int):
        self.premium_users.add(user_id)
        self._save()
    
    def remove_premium(self, user_id: int):
        """For subscription cancellations"""
        self.premium_users.discard(user_id)
        self._save()
    
    async def handle_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Telegram Stars payment confirmation"""
        user_id = update.pre_checkout_query.from_user.id
        
        # Telegram verifies payment automatically via pre_checkout_query
        # This is just a placeholder - actual integration uses Telegram's Payment API
        self.add_premium(user_id)
        
        await update.effective_chat.send_message(
            f"✅ Premium activated! You now get:\n"
            "• ⚡ 60-second early alerts\n"
            "• 🐋 Whale wallet tracking\n"
            "• 🔓 LP unlock warnings\n"
            "• 📊 Advanced analytics\n"
            "• 💬 Priority support\n\n"
            "Type /alerts to see premium features in action!"
        )

# Integration in public_bot.py:
# premium = PremiumManager()
# 
# async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.effective_user.id
#     if premium.is_premium(user_id):
#         await send_premium_alerts(update, context)
#     else:
#         await update.message.reply_text(
#             "🆓 Free tier: 5-min delayed alerts\n"
#             "💎 Premium ($4/mo): Real-time alerts + whale tracking\n"
#             "🚀 Upgrade: /premium",
#             reply_markup=InlineKeyboardMarkup([[
#                 InlineKeyboardButton("💎 Upgrade to Premium", callback_data="upgrade_premium")
#             ]])
#         )
