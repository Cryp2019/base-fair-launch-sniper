# 📱 Setting Up Personal Telegram Alerts

## Quick Setup (3 steps)

### Step 1: Get Your Chat ID

Run this script:
```bash
cd e:\base-fair-launch-sniper
python get_chat_id.py
```

### Step 2: Message Your Bot

1. Open Telegram
2. Find your bot (search for the bot ID: `8145491592`)
3. Send ANY message to it (e.g., "hello")
4. The script will display your Chat ID

### Step 3: Update GitHub Secret

1. Go to: https://github.com/Cryp2019/base-fair-launch-sniper/settings/secrets/actions
2. Find `TELEGRAM_CHAT_ID` and click edit (or create new if it doesn't exist)
3. Replace the value with YOUR Chat ID (it will be a number like `123456789`)
4. Click "Update secret"

---

## ✅ Done!

Now all fair launch alerts will come directly to your personal Telegram chat instead of a public channel!

---

## Alternative: Keep Public Channel

If you want BOTH personal alerts AND a public channel:

1. Create a Telegram channel
2. Add your bot as an admin
3. Use the channel ID as `TELEGRAM_CHAT_ID`
4. Invite others to join the channel

---

## Troubleshooting

**Bot not responding?**
- Make sure `bot.py` is running locally, OR
- The GitHub Actions workflow is active

**Can't find the bot?**
- Search for bot ID: `8145491592`
- Or run `python open_bot.py` to get the bot username

**Chat ID not showing?**
- Make sure the script is running (`python get_chat_id.py`)
- Try sending the message again
- Check that you're messaging the correct bot
