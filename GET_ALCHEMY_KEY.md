# 🔑 How to Get Your Alchemy API Key

## The Problem

Your current Alchemy key is incomplete:
```
RiA4S5DS3ZpgokvFCOenZ  ❌ Only 21 characters
```

Alchemy API keys should be **~32 characters** long and look like:
```
AbCdEfGh1234567890IjKlMnOpQrSt  ✅ Full key
```

## 📝 Step-by-Step Guide

### 1. Go to Alchemy Dashboard
Visit: **https://dashboard.alchemy.com/**

### 2. Sign Up / Log In
- Create a free account if you don't have one
- Or log in with your existing account

### 3. Create a New App
1. Click **"+ Create new app"** button
2. Fill in the details:
   - **Name**: `Base Fair Launch Sniper`
   - **Description**: `Sniper bot for Base chain`
   - **Chain**: Select **"Base"**
   - **Network**: Select **"Base Mainnet"**
3. Click **"Create app"**

### 4. Get Your API Key
1. Find your new app in the dashboard
2. Click **"API Key"** button
3. You'll see your **HTTPS** endpoint like:
   ```
   https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY_HERE
   ```
4. Copy **ONLY** the part after `/v2/`
   - This is your API key!

### 5. Update Your .env File

Open `.env` and replace the old key:

**Before:**
```env
ALCHEMY_BASE_KEY=RiA4S5DS3ZpgokvFCOenZ
```

**After:**
```env
ALCHEMY_BASE_KEY=your_full_32_character_key_here
```

### 6. Save and Restart

1. Save the `.env` file
2. Stop the bot if it's running (Ctrl+C)
3. Restart: `python sniper_bot.py`

## ✅ How to Verify It's Working

When you run the bot with the correct key, you should see:

```
╔═══════════════════════════════════╗
   🚀 BASE FAIR LAUNCH SNIPER BOT
╚═══════════════════════════════════╝

✅ Initializing...
✅ Connected to Base (Block: 41,518,662)  ← This means it's working!
✅ Bot username: @base_fair_launch_bot
✅ Database initialized

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Starting real-time scanning...
📢 Alerts will be sent to all users
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If you see **"400 Client Error: Bad Request"**, your key is still wrong.

## 🆓 Alchemy Free Tier

The free tier includes:
- ✅ 300M compute units/month
- ✅ Enough for your sniper bot
- ✅ No credit card required
- ✅ Base Mainnet access

Perfect for this project!

## 🚨 Common Mistakes

### ❌ Wrong: Using the full URL
```env
ALCHEMY_BASE_KEY=https://base-mainnet.g.alchemy.com/v2/AbCdEf123
```

### ✅ Correct: Just the key
```env
ALCHEMY_BASE_KEY=AbCdEf123456789012345678901234
```

### ❌ Wrong: Incomplete key
```env
ALCHEMY_BASE_KEY=RiA4S5DS3ZpgokvFCOenZ
```

### ✅ Correct: Full 32-character key
```env
ALCHEMY_BASE_KEY=AbCdEfGh1234567890IjKlMnOpQrSt
```

## 🔗 Quick Links

- **Alchemy Dashboard**: https://dashboard.alchemy.com/
- **Alchemy Docs**: https://docs.alchemy.com/
- **Base Chain Info**: https://docs.base.org/

## 💡 Alternative: Use a Different RPC

If you can't get Alchemy working, you can use Base's public RPC:

```env
# In sniper_bot.py, change line 28 to:
BASE_RPC = "https://mainnet.base.org"
```

But Alchemy is recommended because it's:
- ✅ Faster
- ✅ More reliable
- ✅ Better rate limits
- ✅ Free tier is generous

## 📞 Need Help?

If you're still stuck:
1. Check your Alchemy dashboard for the app
2. Make sure you selected "Base Mainnet" (not testnet)
3. Copy the FULL key (should be ~32 chars)
4. Paste it in `.env` without quotes or spaces

---

Once you have the correct key, your bot will start scanning Base chain and sending alerts! 🚀

