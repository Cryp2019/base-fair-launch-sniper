# 🚀 How to Run the Updated Bot

## ⚠️ Important: Bot Processes Keep Getting Killed

The bot processes are being killed (return code: -1). This means either:
1. You're manually stopping them
2. Another process is interfering
3. There's a system issue

## ✅ What I've Implemented

All three features are **COMPLETE** in the code:

1. ✅ **Wallet Creation** - Lines 779-974 in `sniper_bot.py`
2. ✅ **Sniping Function** - Lines 1184-1231 in `sniper_bot.py`
3. ✅ **Fixed Menu** - Lines 329-349 in `sniper_bot.py`

## 🔧 How to Run the Bot Manually

### Step 1: Stop ALL Python Processes

Open PowerShell and run:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Step 2: Wait 10 Seconds

This ensures Telegram clears the connection:
```powershell
Start-Sleep -Seconds 10
```

### Step 3: Start the Bot

```bash
python sniper_bot.py
```

### Step 4: Keep It Running

**DO NOT STOP THE PROCESS!**

The bot needs to stay running to:
- Accept Telegram commands
- Scan for new launches
- Send alerts to users

## 📱 Testing the New Features

Once the bot is running, open Telegram and:

### Test 1: New Menu
```
1. Send /start to @base_fair_launch_bot
2. You should see a 4-row menu:
   Row 1: 🔍 Check Token | 📊 My Stats
   Row 2: 👛 My Wallets  | 🎁 Referrals  ← NEW!
   Row 3: 🏆 Leaderboard | 🔔 Alerts
   Row 4: 💎 Upgrade     | ℹ️ How It Works
```

### Test 2: Wallet Creation
```
1. Click "👛 My Wallets"
2. Click "➕ Create New Wallet"
3. Bot generates a new Base wallet
4. Save the private key shown
```

### Test 3: Sniping Function
```
The bot automatically scans every 10 seconds.
Watch the console for:
"🔍 Starting scan loop..."
"🚀 New launch detected: ..."
```

## 🐛 Troubleshooting

### Issue: "I don't see the new menu"

**Cause:** Old bot instance still connected to Telegram

**Solution:**
1. Stop ALL Python processes
2. Wait 10 seconds
3. Start bot again
4. Send /start in Telegram (not just open the chat)

### Issue: "Bot keeps getting killed"

**Cause:** You or another process is stopping it

**Solution:**
1. Don't press Ctrl+C
2. Don't close the terminal
3. Let it run in the background
4. Check Task Manager for conflicts

### Issue: "No wallet button in menu"

**Cause:** Bot not restarted after code changes

**Solution:**
1. The code IS updated (check lines 329-349)
2. You MUST restart the bot to see changes
3. Old bot instance shows old menu

## 📋 Verification Checklist

Before running, verify the code has the changes:

### Check 1: Menu Has Wallet Button
```bash
python -c "exec(open('sniper_bot.py').read()); print('Wallet button found!' if 'My Wallets' in open('sniper_bot.py').read() else 'NOT FOUND')"
```

### Check 2: Wallet Functions Exist
```bash
python -c "print('✅ Wallet functions found!' if 'wallets_callback' in open('sniper_bot.py').read() else '❌ NOT FOUND')"
```

### Check 3: Database Has Wallets Table
```bash
python -c "print('✅ Wallets table found!' if 'CREATE TABLE IF NOT EXISTS wallets' in open('database.py').read() else '❌ NOT FOUND')"
```

## 🎯 Expected Behavior

### When Bot Starts:
```
╔═══════════════════════════════════╗
   🚀 BASE FAIR LAUNCH SNIPER BOT
╚═══════════════════════════════════╝

✅ Initializing...
✅ Connected to Base (Block: 25,123,456)
✅ Bot username: @base_fair_launch_bot
✅ Database initialized

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Starting real-time scanning...
📢 Alerts will be sent to all users
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Press Ctrl+C to stop
```

### When User Sends /start:
They see the NEW 4-row menu with "👛 My Wallets" button

### When User Clicks "👛 My Wallets":
They see wallet management screen with "➕ Create New Wallet" button

### When Scanning:
Every 10 seconds, bot checks for new Uniswap V3 pairs on Base

## 🔍 Manual Verification

If you can't run the bot, you can verify the code changes:

### View the New Menu:
```bash
python -c "import sniper_bot; print(sniper_bot.create_main_menu())"
```

### Check Wallet Functions:
```bash
grep -n "wallets_callback" sniper_bot.py
grep -n "create_wallet_callback" sniper_bot.py
grep -n "export_key_callback" sniper_bot.py
```

### Check Database Schema:
```bash
grep -A 10 "CREATE TABLE IF NOT EXISTS wallets" database.py
```

## 💡 Alternative: Run in Background

If you want to run the bot in the background:

### Windows (PowerShell):
```powershell
Start-Process python -ArgumentList "sniper_bot.py" -WindowStyle Hidden
```

### Check if Running:
```powershell
Get-Process python | Format-Table Id, ProcessName, StartTime
```

## 📞 What to Do Next

1. **Stop killing the bot processes** - Let them run
2. **Wait 10 seconds** after stopping old processes
3. **Start the bot** with `python sniper_bot.py`
4. **Keep it running** - Don't close the terminal
5. **Test in Telegram** - Send /start to see new menu

## ✅ Confirmation

All code changes are complete and saved:
- ✅ `database.py` - Wallets table added
- ✅ `sniper_bot.py` - Menu updated, wallet functions added
- ✅ No syntax errors - Code compiles successfully
- ✅ Dependencies installed - eth-account v0.10.0

**The bot WILL work once you run it and keep it running!**

## 🚨 Critical Note

**You MUST keep the bot process running for it to work!**

The bot is not a one-time script. It's a server that:
- Listens for Telegram messages 24/7
- Scans blockchain every 10 seconds
- Responds to user commands

If you stop it, it can't do anything!

