# 🚀 Railway Setup Guide - COMPLETE

## ⚠️ IMPORTANT: Your Payment Wallet is NOT Showing

The issue is that Railway doesn't have access to your `.env` file. You need to add environment variables directly in Railway's dashboard.

---

## 📋 Required Environment Variables for Railway

Go to Railway → Your Project → **Variables** tab and add these:

### 1. Core Bot Configuration (Already Set)
```
TELEGRAM_BOT_TOKEN=8145491592:AAHVZ8xcr3q8i3ahsDuxJyt_F-aLXgRf4TE
ALCHEMY_BASE_KEY=RiA4S5DS3ZpgokvFCOenZ
BOT_USERNAME=base_fair_launch_bot
```

### 2. Payment Configuration (MISSING - ADD THESE!)
```
PAYMENT_WALLET_ADDRESS=0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6
FEE_COLLECTION_WALLET=0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6
TRADING_FEE_PERCENTAGE=0.5
```

---

## 🎯 How to Add Variables in Railway

### Step-by-Step:

1. **Login to Railway**
   - Go to: https://railway.app
   - Login with your account

2. **Select Your Project**
   - Click on: `base-fair-launch-sniper`

3. **Open Variables Tab**
   - Click "Variables" in the left sidebar or top menu

4. **Add Each Variable**
   - Click "New Variable" button
   - Enter variable name (e.g., `PAYMENT_WALLET_ADDRESS`)
   - Enter value (e.g., `0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6`)
   - Click "Add"

5. **Repeat for All Variables**
   - Add all 3 payment-related variables

6. **Railway Auto-Redeploys**
   - Once you save, Railway automatically redeploys (2-3 minutes)

---

## ✅ What Happens After Adding Variables

### 1. Payment Wallet Shows in Bot
Instead of "Not configured", users will see:
```
Send 4 USDC on Base to:
0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6
```

### 2. Automatic Premium Upgrades! 🎉
When a user sends 4+ USDC to your wallet:
- ✅ Bot automatically detects the payment
- ✅ Finds the user by their wallet address
- ✅ Upgrades them to premium instantly
- ✅ Sends them a confirmation message

**No manual work needed!**

### 3. Trading Fees Collected
When users trade:
- ✅ Bot takes 0.5% fee automatically
- ✅ Sends to your wallet before executing trade
- ✅ Tracks fees in admin panel

---

## 💰 How Automatic Payment Detection Works

### User Flow:
1. User creates wallet in bot (👛 My Wallets → Create Wallet)
2. User clicks "💎 Upgrade to Premium"
3. User sends 4 USDC from their bot wallet to your address
4. **Bot detects payment within 30 seconds**
5. **Bot auto-upgrades user to premium**
6. **Bot sends confirmation message**

### Technical Details:
- Monitors USDC contract on Base every 30 seconds
- Checks for Transfer events to your payment wallet
- Verifies amount >= 4 USDC
- Matches sender address to user's wallet in database
- Auto-upgrades and notifies user

---

## 🔍 How to Verify It's Working

### After Railway Redeploys:

**1. Check Deployment Logs**
```
Go to Railway → Deployments → View Logs
Look for:
✅ Connected to Base (Block: XXX)
💰 Payment wallet: 0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6
💰 Payment monitor started - auto-upgrades enabled!
```

**2. Test in Telegram**
```
Open @base_fair_launch_bot
Click "💎 Upgrade to Premium"
Should show your wallet address (not "Not configured")
```

**3. Check Admin Panel**
```
Send: /admin
Look for "Payment Wallet" section
Should show: 0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6
```

---

## 🎯 Testing Automatic Upgrades

### Test with Small Amount:

1. **Create a test wallet in bot**
   - Click "👛 My Wallets"
   - Click "➕ Create New Wallet"
   - Save the address

2. **Fund it with USDC**
   - Send 5 USDC to your bot wallet
   - (Use your main wallet or exchange)

3. **Send payment**
   - Use bot's wallet to send 4 USDC to payment address
   - Wait 30-60 seconds

4. **Check for auto-upgrade**
   - Bot should send you a message:
   ```
   🎉 PAYMENT CONFIRMED!
   ✅ You've been upgraded to PREMIUM! 💎
   ```

5. **Verify premium status**
   - Click "📊 My Stats"
   - Should show "💎 PREMIUM" tier

---

## 📊 Revenue Tracking

### View Payments on Basescan:
```
https://basescan.org/address/0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6
```

Filter by:
- **Token:** USDC
- **Method:** Transfer

You'll see all incoming premium payments!

### View Trading Fees:
Same Basescan link, but filter by:
- **Token:** ETH
- **Method:** Transfer

You'll see all 0.5% trading fees!

---

## 💡 Pro Tips

### Separate Wallets for Better Tracking:
```
PAYMENT_WALLET_ADDRESS=0x1Cc45DCAF7ACddAEE53518956d29684F43fCA8F6  (Premium payments)
FEE_COLLECTION_WALLET=0xYOUR_OTHER_WALLET  (Trading fees)
```

This makes it easier to track:
- Premium revenue vs trading revenue
- Tax reporting
- Business analytics

---

## 🚨 Common Issues

### Issue: "Not configured" still showing
**Solution:** Make sure you added `PAYMENT_WALLET_ADDRESS` to Railway (not just .env)

### Issue: Auto-upgrade not working
**Check:**
- User sent from wallet created in bot
- Amount is >= 4 USDC (not ETH!)
- Payment is on Base chain (not Ethereum mainnet)
- Check Railway logs for errors

### Issue: Trading fees not collected
**Check:**
- `TRADING_FEE_PERCENTAGE` is set in Railway
- `FEE_COLLECTION_WALLET` is set in Railway
- User has enough ETH for fee + trade + gas

---

## ✅ Final Checklist

Before going live:

- [ ] Added `PAYMENT_WALLET_ADDRESS` to Railway
- [ ] Added `FEE_COLLECTION_WALLET` to Railway  
- [ ] Added `TRADING_FEE_PERCENTAGE` to Railway
- [ ] Railway deployment successful (check logs)
- [ ] Payment wallet shows in bot (not "Not configured")
- [ ] Tested auto-upgrade with small payment
- [ ] Admin panel accessible via `/admin`
- [ ] Basescan bookmark saved for tracking payments

---

**Add those 3 environment variables to Railway NOW and your bot will be fully functional! 🚀**

