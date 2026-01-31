# 💰 How to Verify Payments and Upgrade Users

## 🎯 Your Payment Wallet

**Base Chain Wallet:** `0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6`

This wallet is now integrated into your bot! Users will see it when they click "💎 Upgrade" in the menu.

---

## 📋 Payment Process (User Side)

1. User clicks "💎 Upgrade" in bot menu
2. Bot shows payment instructions with your wallet address
3. User sends **4 USDC on Base** to your wallet
4. User DMs you the transaction hash
5. You verify and upgrade them

---

## ✅ How to Verify Payments (Your Side)

### Step 1: User Sends You Transaction Hash

User will send something like:
```
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### Step 2: Verify on Basescan

1. Go to: https://basescan.org/tx/[TRANSACTION_HASH]
2. Check:
   - ✅ **To Address:** `0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6` (your wallet)
   - ✅ **Token:** USDC
   - ✅ **Amount:** 4 USDC (or more)
   - ✅ **Status:** Success ✅

### Step 3: Upgrade User to Premium

Open your database and run:

```bash
# Option 1: Using Python
python -c "from database import Database; db = Database(); db.update_tier(USER_ID, 'premium'); print('✅ User upgraded!')"

# Option 2: Using SQLite directly
sqlite3 sniper_bot.db "UPDATE users SET tier='premium' WHERE user_id=USER_ID;"
```

Replace `USER_ID` with the user's Telegram ID (they can find it by clicking "📊 My Stats" in the bot).

### Step 4: Notify User

Send them a message in Telegram:
```
🎉 Payment verified! You've been upgraded to PREMIUM! 💎

Your premium features are now active:
✅ Advanced analytics
✅ Priority alerts (5-10s faster)
✅ Initial liquidity data

Thank you for your support! 🚀
```

---

## 🤖 Quick Upgrade Script

Create a file called `upgrade_user.py`:

```python
#!/usr/bin/env python3
import sys
from database import Database

if len(sys.argv) != 2:
    print("Usage: python upgrade_user.py <user_id>")
    sys.exit(1)

user_id = int(sys.argv[1])
db = Database()

# Upgrade user
db.update_tier(user_id, 'premium')

# Get user info
user = db.get_user(user_id)
print(f"✅ User upgraded to premium!")
print(f"   User ID: {user_id}")
print(f"   Username: @{user['username']}")
print(f"   Tier: {user['tier']}")
```

**Usage:**
```bash
python upgrade_user.py 123456789
```

---

## 📊 Track Your Payments

### View All Premium Users

```bash
sqlite3 sniper_bot.db "SELECT user_id, username, tier FROM users WHERE tier='premium';"
```

### Count Premium Users

```bash
sqlite3 sniper_bot.db "SELECT COUNT(*) FROM users WHERE tier='premium';"
```

### Monthly Revenue Estimate

```bash
# Count premium users and multiply by $4
sqlite3 sniper_bot.db "SELECT COUNT(*) * 4 as monthly_revenue FROM users WHERE tier='premium';"
```

---

## 🔄 Payment Verification Checklist

When a user sends you a transaction hash:

- [ ] Copy transaction hash
- [ ] Open Basescan: https://basescan.org/tx/[HASH]
- [ ] Verify recipient is your wallet
- [ ] Verify token is USDC
- [ ] Verify amount is 4+ USDC
- [ ] Verify status is "Success"
- [ ] Get user's Telegram ID (ask them or check bot stats)
- [ ] Run: `python upgrade_user.py [USER_ID]`
- [ ] Notify user they're upgraded
- [ ] Mark payment as processed (keep a spreadsheet)

---

## 💡 Pro Tips

### 1. Keep a Payment Log

Create a simple spreadsheet:
| Date | User ID | Username | Txn Hash | Amount | Status |
|------|---------|----------|----------|--------|--------|
| 2026-01-31 | 123456 | @john | 0x123... | 4 USDC | ✅ Verified |

### 2. Set Expiration Dates (Future Enhancement)

Currently, premium is permanent. To add expiration:

```sql
-- Add expiration column
ALTER TABLE users ADD COLUMN premium_expires TEXT;

-- Set expiration (30 days from now)
UPDATE users SET premium_expires = datetime('now', '+30 days') WHERE user_id=123456;
```

### 3. Automate Verification (Future)

You can use Alchemy webhooks to monitor your wallet:
- Set up webhook for incoming USDC transfers
- Parse transaction data
- Auto-upgrade users
- Send confirmation message

---

## 🎁 Free Premium (Referrals)

Users who refer 10 people get **1 month FREE premium** automatically!

**How it works:**
1. User shares referral link
2. 10 people sign up using their link
3. Bot automatically upgrades them to premium
4. They get instant notification

**No manual work needed for referral upgrades!** ✅

---

## 📞 Support

If a user has payment issues:

1. **Check Basescan** - Verify transaction exists
2. **Check Network** - Must be Base (not Ethereum mainnet)
3. **Check Token** - Must be USDC (not ETH or other tokens)
4. **Check Amount** - Must be 4+ USDC

Common issues:
- ❌ Sent on wrong network (Ethereum instead of Base)
- ❌ Sent wrong token (ETH instead of USDC)
- ❌ Sent to wrong address (typo)

---

## 🚀 Ready to Accept Payments!

Your bot now shows:
- ✅ Your payment wallet address
- ✅ Clear payment instructions
- ✅ Referral progress (X/10)
- ✅ Premium feature list

**Users can now pay and you can verify + upgrade them manually!**

When you're ready to automate, see **PAYMENT_INTEGRATION.md** for Coinbase Commerce integration.

