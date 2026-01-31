# 💰 How to Collect Premium Fees ($4/month)

## 🎯 Best Payment Options for Telegram Bots

### Option 1: Telegram Stars (RECOMMENDED) ⭐
**Easiest and most integrated with Telegram**

#### Pros:
- ✅ Built directly into Telegram
- ✅ No external payment processor needed
- ✅ Users pay with Telegram Stars (in-app currency)
- ✅ Telegram handles all payment processing
- ✅ You get paid in Stars, withdraw to bank

#### How to Set Up:
1. Contact @BotFather
2. Enable payments: `/mybots` → Select your bot → `Payments`
3. Connect your payment provider (Stripe, etc.)
4. Add payment buttons to your bot

#### Implementation:
```python
from telegram import LabeledPrice

# In upgrade_callback function:
await context.bot.send_invoice(
    chat_id=user.id,
    title="Premium Subscription",
    description="1 month of premium features",
    payload="premium_1month",
    provider_token="YOUR_PROVIDER_TOKEN",  # From BotFather
    currency="USD",
    prices=[LabeledPrice("Premium", 400)]  # $4.00 in cents
)
```

---

### Option 2: Crypto Payments (POPULAR FOR WEB3) 🪙
**Best for crypto-native users**

#### Recommended Services:
- **Coinbase Commerce** - Easy integration, supports ETH/USDC/BTC
- **NOWPayments** - Supports 200+ cryptocurrencies
- **CoinPayments** - Oldest and most trusted

#### Pros:
- ✅ No chargebacks
- ✅ Lower fees (1-2% vs 3-5% for cards)
- ✅ Instant settlement
- ✅ Your users are crypto users anyway!

#### How to Set Up (Coinbase Commerce):
1. Sign up at https://commerce.coinbase.com/
2. Get API key
3. Create payment button
4. User pays in ETH/USDC
5. You receive notification webhook
6. Upgrade user to premium

#### Implementation:
```python
import requests

def create_payment_link(user_id):
    response = requests.post(
        'https://api.commerce.coinbase.com/charges',
        headers={'X-CC-Api-Key': 'YOUR_API_KEY'},
        json={
            'name': 'Premium Subscription',
            'description': '1 month premium',
            'pricing_type': 'fixed_price',
            'local_price': {'amount': '4.00', 'currency': 'USD'},
            'metadata': {'user_id': user_id}
        }
    )
    return response.json()['data']['hosted_url']
```

---

### Option 3: Stripe (TRADITIONAL) 💳
**Best for credit card payments**

#### Pros:
- ✅ Most trusted payment processor
- ✅ Supports all major cards
- ✅ Recurring subscriptions built-in
- ✅ Great documentation

#### Cons:
- ❌ Higher fees (2.9% + $0.30)
- ❌ Requires business verification
- ❌ More complex integration

#### How to Set Up:
1. Sign up at https://stripe.com/
2. Get API keys
3. Create subscription product
4. Generate payment link
5. Send link to user
6. Webhook confirms payment
7. Upgrade user

---

## 🚀 Quick Implementation (Crypto - Easiest)

### Step 1: Add Payment Wallet to .env
```env
PAYMENT_WALLET_ADDRESS=0xYourWalletAddress
USDC_BASE_ADDRESS=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913
```

### Step 2: Update Upgrade Button

Add this to `sniper_bot.py`:

```python
async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upgrade info with payment options"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = db.get_user(user.id)
    
    current_tier = user_data['tier'] if user_data else 'free'
    
    if current_tier == 'premium':
        msg = "✅ You already have PREMIUM! 💎"
        await query.edit_message_text(msg, reply_markup=create_back_button())
        return
    
    # Payment wallet address
    payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS')
    
    msg = (
        f"╔═══════════════════════╗\n"
        f"   💎 *UPGRADE TO PREMIUM*\n"
        f"╚═══════════════════════╝\n\n"
        f"⭐ *PREMIUM* - $4/month\n\n"
        f"*Features:*\n"
        f"• Advanced analytics\n"
        f"• Priority alerts (5-10s faster)\n"
        f"• Custom filters\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *PAYMENT OPTIONS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Send *4 USDC* on Base to:\n"
        f"`{payment_wallet}`\n\n"
        f"After payment, send transaction hash to verify!\n\n"
        f"🎁 *OR GET IT FREE:*\n"
        f"Refer 10 users = 1 month FREE!"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ I Paid - Verify", callback_data="verify_payment")],
        [InlineKeyboardButton("« Back", callback_data="menu")]
    ]
    
    await query.edit_message_text(msg, parse_mode='Markdown', 
                                  reply_markup=InlineKeyboardMarkup(keyboard))
```

### Step 3: Add Payment Verification

```python
async def verify_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user for transaction hash"""
    query = update.callback_query
    await query.answer()
    
    msg = (
        "📝 *Payment Verification*\n\n"
        "Please send your transaction hash (txn hash) from Basescan.\n\n"
        "Example:\n"
        "`0x1234567890abcdef...`\n\n"
        "I'll verify your payment and activate premium!"
    )
    
    await query.edit_message_text(msg, parse_mode='Markdown', 
                                  reply_markup=create_back_button())
    
    # Set state to wait for txn hash
    context.user_data['waiting_for_payment'] = True
```

---

## 🔄 Automated Payment Verification

For fully automated payments, you can:

1. **Monitor your wallet** for incoming USDC transactions
2. **Check transaction metadata** for user ID
3. **Auto-upgrade** when payment confirmed

This requires running a separate script that monitors the blockchain.

---

## 💡 Recommended Approach

**For Your Bot (Crypto-Native Users):**

1. **Manual Crypto Payments** (Easiest to start)
   - User sends 4 USDC to your wallet
   - User sends you the txn hash
   - You verify manually and upgrade them
   - Takes 2 minutes per payment

2. **Later: Automated Crypto** (Scale up)
   - Use Coinbase Commerce or NOWPayments
   - Fully automated
   - Webhook upgrades users instantly

3. **Alternative: Telegram Stars** (If you want traditional payments)
   - Built into Telegram
   - Users can pay with cards
   - Telegram handles everything

---

## 📊 Fee Comparison

| Method | Fee | Setup Time | Automation |
|--------|-----|------------|------------|
| Manual Crypto | 0% | 5 min | Manual |
| Coinbase Commerce | 1% | 30 min | Automated |
| Stripe | 2.9% + $0.30 | 1 hour | Automated |
| Telegram Stars | ~5% | 30 min | Automated |

---

## 🎯 Next Steps

1. Choose payment method (I recommend starting with manual crypto)
2. Add your wallet address to `.env`
3. Update the upgrade button with payment instructions
4. Test with a small payment
5. Scale to automated when you have more users

**Want me to implement the payment system for you? Let me know which method you prefer!**

