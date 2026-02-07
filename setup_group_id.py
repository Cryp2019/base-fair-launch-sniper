#!/usr/bin/env python3
"""
Helper to get and set up your Telegram group ID
"""

print("""
╔════════════════════════════════════════════════════════════════╗
║          GET YOUR TELEGRAM GROUP ID - SETUP GUIDE             ║
╚════════════════════════════════════════════════════════════════╝

📱 STEP 1: Get Your Group ID
═════════════════════════════════════════════════════════════════

Option A: Using @userinfobot (Recommended)
───────────────────────────────────────────
1. Open your Telegram group
2. Click the group name at top
3. Click "Members" 
4. Search and add: @userinfobot
5. @userinfobot will send you a message with your group info
6. Copy the ID (negative number like -1001234567890)

Option B: Using @RawDataBot
─────────────────────────────
1. Add @RawDataBot to your group
2. It sends raw group data
3. Look for "chat": {"id": -1001234567890}
4. Copy the ID

Option C: From Group URL (if public)
─────────────────────────────────────
URL: https://t.me/groupname/123456789
ID: -1001234567890 (usually -100 + group ID)


🔧 STEP 2: Add Group ID to .env
═════════════════════════════════════════════════════════════════

Open your .env file and find this line:

GROUP_CHAT_ID=

Replace it with:

GROUP_CHAT_ID=-1001234567890

Example (replace the number with YOUR group ID):
GROUP_CHAT_ID=-1234567890


✅ STEP 3: Bot Permissions
═════════════════════════════════════════════════════════════════

Make sure your bot is an ADMIN with these permissions:
  ✅ Send Messages (REQUIRED)
  ✅ Send Media (REQUIRED)
  ✅ Send Stickers (optional)
  ✅ Manage Messages (optional, for editing)

To set permissions:
1. Right-click your bot in the group
2. Select "Promote as Administrator"
3. Check "Send Messages" 
4. Check "Send Media"
5. Click "Save"


🚀 STEP 4: Restart Bot
═════════════════════════════════════════════════════════════════

1. Save .env file (Ctrl+S)
2. Stop the bot (Ctrl+C) if running
3. Start bot: python sniper_bot.py
4. Wait for "Group posting enabled" message


💡 TROUBLESHOOTING
═════════════════════════════════════════════════════════════════

If still not posting:

1. Check GROUP_CHAT_ID is set: python diagnose_group_posting.py
2. Verify bot is in the group (check members list)
3. Verify bot is admin with Send Messages permission
4. Check bot is actually running (should see scanning messages)
5. Wait for a new token launch (may take 5-30 minutes)
6. Check .env has no extra spaces: GROUP_CHAT_ID=-1234567890

Common mistakes:
  ❌ GROUP_CHAT_ID= (missing the actual ID)
  ❌ GROUP_CHAT_ID = -1234567890 (spaces around =)
  ❌ GROUP_CHAT_ID=1234567890 (missing minus sign)
  ❌ GROUP_CHAT_ID=@groupname (should be -number)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to set it up? Follow the steps above and the bot will start
posting good-rated projects to your group automatically! 🚀

""")

# Try to help get the ID
print("\n" + "="*70)
print("🤖 AUTOMATED SETUP HELPER")
print("="*70 + "\n")

import os

group_id = input("Enter your Telegram group ID (from @userinfobot): ").strip()

if not group_id:
    print("❌ No group ID provided")
    exit(1)

if not group_id.startswith('-'):
    group_id = '-' + group_id

try:
    int(group_id)  # Verify it's a valid number
except ValueError:
    print(f"❌ Invalid group ID: {group_id}")
    print("   Should be a negative number like: -1001234567890")
    exit(1)

print(f"\n✅ Group ID: {group_id}")
print("   Updating .env...")

# Read .env
with open('.env', 'r') as f:
    env_content = f.read()

# Replace GROUP_CHAT_ID
import re
env_content = re.sub(
    r'GROUP_CHAT_ID=.*',
    f'GROUP_CHAT_ID={group_id}',
    env_content
)

# Write back
with open('.env', 'w') as f:
    f.write(env_content)

print(f"✅ Updated .env with GROUP_CHAT_ID={group_id}")
print("\n" + "="*70)
print("✨ SETUP COMPLETE!")
print("="*70)
print("""
Next steps:
1. Close any running bot (Ctrl+C)
2. Run: python sniper_bot.py
3. Wait for projects with 75+ security rating
4. They will auto-post to your group! 🚀
""")
