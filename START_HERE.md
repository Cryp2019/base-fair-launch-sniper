# 🚀 Base Fair Launch Sniper Bot - Quick Start Guide

## ✅ Your Bot is Ready!

I've created a **modern, sleek Telegram bot** that scans ALL new token launches on Base chain and sends beautiful alerts to users!

## 📁 Main File

**`sniper_bot.py`** - This is your complete bot with:
- ✨ Beautiful modern UI with emojis and formatting
- 🔍 Real-time scanning of Base chain (every 30 seconds)
- 📢 Instant alerts to all users with alerts enabled
- 🎁 Referral system with rewards
- 📊 User stats and leaderboard
- 🔘 Interactive inline keyboard buttons
- 🛡️ Safety checks (ownership, honeypot detection)

## 🔧 Setup Instructions

### 1. Fix Your Alchemy API Key

Your `.env` file has an incomplete Alchemy key. You need to:

1. Go to [Alchemy.com](https://www.alchemy.com/)
2. Create a free account
3. Create a new app for **Base Mainnet**
4. Copy the FULL API key
5. Update `.env` file:

```env
ALCHEMY_BASE_KEY=your_full_alchemy_key_here
```

### 2. Stop Other Bot Instances

You have another bot instance running. Stop it first:

```bash
# Press Ctrl+C in any terminal running a bot
# Or close all Python processes
```

### 3. Run the Bot

```bash
python sniper_bot.py
```

## 🎨 Features

### For Users:
- `/start` - Register and see welcome message
- Beautiful inline keyboard menu
- Real-time alerts for ALL new token launches
- Direct links to Basescan, DexScreener, Uniswap
- Referral system to earn rewards
- Toggle alerts on/off
- View stats and leaderboard

### For You (Admin):
- Automatic 24/7 scanning
- Scans every 30 seconds for new pairs
- Sends alerts to all users with alerts enabled
- Tracks all users in SQLite database
- Beautiful formatted messages

## 📊 What Gets Scanned

The bot monitors:
- ✅ Uniswap V3 on Base chain
- ✅ New USDC pairs
- ✅ New WETH pairs
- ✅ Checks ownership status
- ✅ Provides direct links to charts

## 🎯 How It Works

1. **Scanning Loop**: Checks Base chain every 30 seconds
2. **Detection**: Finds new Uniswap V3 pairs
3. **Analysis**: Analyzes token contract (name, symbol, ownership)
4. **Alert**: Sends beautiful formatted alert to all users
5. **Links**: Provides Basescan, DexScreener, Uniswap links

## 💬 Test the Bot

1. Open Telegram
2. Search for your bot: `@base_fair_launch_bot` (or your bot username)
3. Send `/start`
4. You'll see a beautiful welcome message with buttons!

## 🎨 UI Features

- ╔═══╗ Box borders for headers
- 🚀 Emojis for visual appeal
- ━━━ Section dividers
- Inline keyboard buttons for navigation
- Markdown formatting for emphasis
- Clean, modern layout

## 📝 Next Steps

1. **Fix Alchemy Key** - Get a complete API key
2. **Test Bot** - Send /start in Telegram
3. **Monitor Logs** - Watch for new token detections
4. **Share Bot** - Give users your bot link

## 🔗 Bot Link Format

Users can start your bot with:
```
https://t.me/base_fair_launch_bot
```

Or with referral:
```
https://t.me/base_fair_launch_bot?start=BASE123456
```

## ⚠️ Important Notes

- The bot runs continuously and scans every 30 seconds
- Alerts are sent to ALL users with alerts enabled
- Database (`users.db`) tracks all users and referrals
- Press `Ctrl+C` to stop the bot gracefully

## 🎁 Referral System

- Users get unique referral codes
- Track referrals in database
- Leaderboard shows top referrers
- Rewards for referring friends

## 🛡️ Safety Features

- Checks if ownership is renounced
- Provides direct verification links
- Warns users to DYOR
- Not financial advice disclaimer

---

## 🚨 Current Issues to Fix

1. **Alchemy API Key** - Your key in `.env` is incomplete
2. **Stop other bots** - Only run one instance at a time

Once you fix the Alchemy key, the bot will start scanning and sending alerts!

Enjoy your sleek, modern Base Fair Launch Sniper Bot! 🚀

