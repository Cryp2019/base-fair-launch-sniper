#!/usr/bin/env python3
"""
Complete troubleshooting guide for group posting
"""

guide = """
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║  🔧 COMPLETE TROUBLESHOOTING GUIDE - GROUP POSTING NOT WORKING   ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 QUICK DIAGNOSIS

Run this to find the problem:
  python diagnose_group_posting.py

It will tell you exactly what's missing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CHECKLIST 1: CONFIGURATION

□ GROUP_CHAT_ID is set in .env
  How to check: Open .env, look for GROUP_CHAT_ID=-1234567890
  
  If missing:
  1. Run: python setup_group_id.py
  2. Enter your group ID (from @userinfobot)
  3. Save and restart bot

□ GROUP_CHAT_ID format is correct
  ✅ Correct:   GROUP_CHAT_ID=-1001234567890
  ❌ Wrong:     GROUP_CHAT_ID=1001234567890 (missing -)
  ❌ Wrong:     GROUP_CHAT_ID = -1001234567890 (spaces)
  ❌ Wrong:     GROUP_CHAT_ID=@groupname (use number instead)

□ No extra spaces in .env
  ✅ Correct:   GROUP_CHAT_ID=-1001234567890
  ❌ Wrong:     GROUP_CHAT_ID = -1001234567890
  ❌ Wrong:     GROUP_CHAT_ID=-1001234567890 (extra space)

□ TELEGRAM_BOT_TOKEN is set in .env
  How to check: Open .env, look for TELEGRAM_BOT_TOKEN=...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CHECKLIST 2: BOT SETUP

□ Bot is in the group
  How to check: Open Telegram group, check members list
  
  If bot is not there:
  1. Get bot username: @base_fair_launch_bot (or your bot name)
  2. Open group
  3. Click "+" button
  4. Add members
  5. Search for bot by username
  6. Add it

□ Bot is ADMIN with permissions
  How to check: Right-click bot in group → See "Administrator" label
  
  If not admin:
  1. Right-click the bot
  2. Click "Promote as Administrator"
  3. Check these permissions:
     ✅ Send Messages (REQUIRED)
     ✅ Send Media (REQUIRED)
     ✅ Manage Chat (optional)
  4. Click "Save"

□ Group is not super-restricted
  If group has restricted settings:
  1. Group Settings → Permissions
  2. Make sure bots can post
  3. Make sure external accounts can post
  4. Save

□ Group is not archived
  Archived groups cannot receive messages
  1. Open group
  2. If settings show "Archived", unarchive it

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CHECKLIST 3: BOT OPERATION

□ Bot is running
  How to check: Open terminal, see messages like:
    "🔍 Starting real-time scanning..."
    "📢 Alerts will be sent to all users"
  
  If bot not running:
  1. Open terminal/PowerShell
  2. Run: cd e:\base-fair-launch-sniper
  3. Run: python sniper_bot.py
  4. Wait 10 seconds for startup message

□ Bot is scanning for tokens
  How to check: Look for messages like:
    "✨ Found X new pair(s)"
    "🚀 New launch detected"
  
  If not scanning:
  1. Check Web3 connection: python verify_integration.py
  2. Check RPC is accessible: https://mainnet.base.org
  3. Check Alchemy key if using custom RPC

□ New tokens are being detected
  The bot only posts when:
  1. A NEW token launches on Base chain
  2. Its security rating is 75+ out of 100
  3. Your group ID is set
  4. Bot is in the group
  
  If no projects post:
  - Wait 5-30 minutes (depends on launch activity)
  - Check minimum rating threshold (should be 75)
  - Verify at least one token with 75+ rating has launched

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CHECKLIST 4: GROUP ID VERIFICATION

If unsure about your group ID:

□ Get it from @userinfobot
  1. Open Telegram app
  2. Search for: @userinfobot
  3. Start the bot
  4. Open your group
  5. Add @userinfobot to the group
  6. It will send group info with ID
  7. Example: "ID: -1001234567890"
  8. Copy the ID number
  9. Set in .env: GROUP_CHAT_ID=-1001234567890

□ Get it from @RawDataBot
  1. Search for: @RawDataBot
  2. Add to your group
  3. It sends raw JSON with group info
  4. Look for: "chat": {"id": -1001234567890}
  5. Use that ID

□ Important: Group vs Channel ID
  GROUP ID: Usually starts with -1001... (negative, 13 digits)
  CHANNEL ID: Also starts with -1001... but different permissions
  PRIVATE CHAT: Might be different format
  
  You need a GROUP ID, not a channel or private chat

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔨 STEP-BY-STEP FIX

If nothing is posting, follow this:

STEP 1: Stop the bot
  Press Ctrl+C in the terminal running sniper_bot.py

STEP 2: Get your group ID
  Run: python setup_group_id.py
  
  Or manually:
  1. Add @userinfobot to your group
  2. It sends your group ID
  3. Copy the negative number (e.g., -1001234567890)

STEP 3: Update .env
  Open .env file
  Find: GROUP_CHAT_ID=
  Change to: GROUP_CHAT_ID=-1001234567890
  (Replace with YOUR actual group ID)
  
  Save file (Ctrl+S)

STEP 4: Make bot admin
  In Telegram:
  1. Open your group
  2. Right-click your bot
  3. "Promote as Administrator"
  4. Check "Send Messages" ✅
  5. Check "Send Media" ✅
  6. Click "Save"

STEP 5: Restart bot
  In terminal:
  python sniper_bot.py

STEP 6: Verify setup
  Run in another terminal:
  python diagnose_group_posting.py

STEP 7: Wait for posts
  The bot will post when:
  • A new token launches
  • Security rating is 75+
  • You wait 2-3 minutes for analysis
  
  Posts will appear automatically! 🚀

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ COMMON MISTAKES

Mistake 1: GROUP_CHAT_ID is empty
  ❌ GROUP_CHAT_ID=
  ✅ GROUP_CHAT_ID=-1001234567890

Mistake 2: Spaces around equals
  ❌ GROUP_CHAT_ID = -1001234567890
  ✅ GROUP_CHAT_ID=-1001234567890

Mistake 3: Missing minus sign
  ❌ GROUP_CHAT_ID=1001234567890
  ✅ GROUP_CHAT_ID=-1001234567890

Mistake 4: Using channel instead of group
  Groups: Private or public GROUPS
  Channels: Broadcast-only, not groups
  
  Bot can't post to channels by default
  Make sure you're using a GROUP

Mistake 5: Bot not admin
  Bot won't post if it doesn't have:
  ✅ Send Messages permission
  ✅ Admin status (recommended)

Mistake 6: Wrong ID format
  ❌ GROUP_CHAT_ID=@groupname (username)
  ❌ GROUP_CHAT_ID=123456789 (positive number)
  ✅ GROUP_CHAT_ID=-1001234567890 (negative number)

Mistake 7: Bot account isn't admin in group
  Go to group settings
  Make bot an administrator
  Give it "Send Messages" permission

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 TESTING

To test without waiting for real tokens:

Option 1: Send test message
  python diagnose_group_posting.py
  (It attempts to send a test message)

Option 2: Manual test
  Edit sniper_bot.py, find post_to_group_with_buy_button()
  Add test data and call it manually

Option 3: Check logs
  Run bot with: python sniper_bot.py
  Watch for these messages:
  
  ✅ "Group posting enabled"
  ✅ "Found X new pair(s)"
  ✅ "Posted to group"
  
  If you see these, everything works!
  Just wait for good projects (75+ rating)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 FINAL HELP

Still not working? Try this:

1. Run diagnostic: python diagnose_group_posting.py
2. Check output for specific error
3. Fix the specific issue it shows
4. Restart bot
5. Wait for new token launches

Most common issue:
  ❌ GROUP_CHAT_ID is empty or wrong
  
  Fix:
  1. Run: python setup_group_id.py
  2. Enter your group ID
  3. Restart bot

You're set! The bot will auto-post good projects to your group 🚀

"""

print(guide)

# Save to file
with open('TROUBLESHOOTING_GROUP_POSTING.txt', 'w') as f:
    f.write(guide)

print("\n✅ Full guide saved to: TROUBLESHOOTING_GROUP_POSTING.txt")
