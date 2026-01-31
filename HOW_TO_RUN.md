# 🤖 How to Run the Enhanced Fair Launch Bot

## Current Situation

You're running: `public_bot.py` (different bot)  
You need: `bot.py` (the enhanced sniper bot with Telegram)

## Start the Enhanced Bot

### Option 1: Stop current bot and start the main one

```powershell
# Stop the current bot (Ctrl+C in the terminal)
# Then run:
python bot.py
```

### Option 2: Run in a new terminal

```powershell
# Open a new PowerShell terminal
cd e:\base-fair-launch-sniper
python bot.py
```

## What the Bot Does

Once running, `bot.py` will:

1. ✅ Connect to Base chain via Alchemy
2. ✅ Connect to Telegram bot
3. ✅ Scan for new USDC and WETH pairs every cycle
4. ✅ Analyze each pair with enhanced functions:
   - Check ownership renouncement
   - Verify LP lock (actual token balances!)
   - Detect honeypots via API
   - Measure real buy/sell taxes
   - Calculate pre-mine ratio
5. ✅ Send Telegram alerts for fair launches

## Expected Output

When running, you'll see:
```
2026-01-30 02:30:00 - INFO - Bot started
2026-01-30 02:30:01 - INFO - Connected to Base chain - Block: 41,483,xxx
2026-01-30 02:30:02 - INFO - Telegram bot ready
2026-01-30 02:30:03 - INFO - Scanning for new pairs...
```

## Telegram Commands

Once the bot is running, you can use these commands in Telegram:

- `/start` - Get welcome message
- `/howitworks` - See how the bot works
- `/scan` - Manually trigger a scan

## Alerts

When a fair launch is detected, you'll get a Telegram message like:

```
✅ NEW TOKEN DETECTED ✅

🔤 SafeMoon 2.0 ($SAFE2)
🔗 Pair: 0x1234...5678
🏷️ Token: 0xabcd...ef01

🛡️ Fair Launch Checks:
✅ Ownership renounced
✅ Creator holding: 2.5%
✅ Liquidity locked (90 days, 75% locked via Unicrypt)
✅ Tax check passed
💸 Buy Tax: 1% | Sell Tax: 1%
```

## Configuration

The bot uses your `.env` file:
- ✅ `ALCHEMY_BASE_KEY` - Connected
- ✅ `TELEGRAM_BOT_TOKEN` - Configured
- ✅ `TELEGRAM_CHAT_ID` - Set to `@base_fair_launch_alerts`

## Troubleshooting

**If bot doesn't start:**
1. Check `.env` has all required keys
2. Verify Telegram bot token is correct
3. Ensure Alchemy API key is valid

**If no alerts:**
- This is normal! Fair launches are rare
- Most tokens fail the checks (scams filtered out)
- Expect 0-5 alerts per day

## Ready?

Just run:
```bash
python bot.py
```

And watch for fair launch alerts in Telegram! 🚀
