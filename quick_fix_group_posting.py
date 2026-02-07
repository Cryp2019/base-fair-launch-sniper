#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Troubleshooting guide for group posting issues
"""
import sys

# Show the guide without special characters that cause issues
print("""
TROUBLESHOOTING GUIDE - GROUP POSTING NOT WORKING
==================================================

QUICK DIAGNOSIS
===============
Run: python diagnose_group_posting.py
This will tell you exactly what's missing.


THE PROBLEM (Most Common)
=========================
GROUP_CHAT_ID is empty in your .env file!

Your .env has:
  GROUP_CHAT_ID=

It should have:
  GROUP_CHAT_ID=-1001234567890
  (with YOUR actual group ID)


HOW TO FIX
==========

STEP 1: Get your group ID
  a) Add @userinfobot to your Telegram group
  b) It sends: "ID: -1001234567890"
  c) Copy that number (it will be negative like -1001...)

STEP 2: Set it in .env
  a) Open .env file
  b) Find: GROUP_CHAT_ID=
  c) Add your ID: GROUP_CHAT_ID=-1001234567890
  d) Save file

STEP 3: Make bot admin
  a) Open Telegram group
  b) Right-click the bot
  c) Click "Promote as Administrator"
  d) Check "Send Messages" permission
  e) Click "Save"

STEP 4: Restart bot
  a) Stop bot (Ctrl+C)
  b) Run: python sniper_bot.py
  c) Wait for "Group posting enabled" message

STEP 5: Done!
  The bot will now post good projects to your group automatically


AUTOMATED SETUP
===============
Run this to automatically set your group ID:
  python setup_group_id.py

Then follow the prompts to add your group ID.


CHECKLIST
=========
Before group posting works, check:
  
  1. GROUP_CHAT_ID is set in .env (not empty)
     Check: Open .env, look for GROUP_CHAT_ID=-1234567890
  
  2. Format is correct
     RIGHT:   GROUP_CHAT_ID=-1001234567890
     WRONG:   GROUP_CHAT_ID=1001234567890 (missing -)
     WRONG:   GROUP_CHAT_ID=@groupname (use numbers)
  
  3. No extra spaces
     RIGHT:   GROUP_CHAT_ID=-1001234567890
     WRONG:   GROUP_CHAT_ID = -1001234567890
  
  4. Bot is in the group
     Check: Open group, look for bot in members
  
  5. Bot is admin with Send Messages permission
     Check: Right-click bot, should show "Administrator"
  
  6. Bot is actually running
     Check: Terminal shows "Scanning for new launches..."


IF STILL NOT POSTING
====================
1. Run: python diagnose_group_posting.py
2. Follow any error messages it shows
3. Most likely: GROUP_CHAT_ID is still empty or wrong
4. Second likely: Bot doesn't have permissions
5. Third: Bot is not in the group


WHAT SHOULD HAPPEN
===================
Once everything is set up:

1. Bot starts running and shows:
   "Group posting enabled"
   "Starting real-time scanning..."

2. When a new token launches:
   Bot analyzes it
   
3. If rating is 75+:
   Bot posts to your group with:
   - Token name and symbol
   - Market cap and liquidity
   - Security rating (75-100)
   - "Buy Now" button
   - Links to chart and info

4. You click "Buy Now"
   Bot executes the trade instantly


COMMON MISTAKES
===============
1. GROUP_CHAT_ID is empty
   Fix: Add your group ID

2. Spaces around equals sign
   WRONG: GROUP_CHAT_ID = -1001234567890
   RIGHT: GROUP_CHAT_ID=-1001234567890

3. Missing minus sign
   WRONG: GROUP_CHAT_ID=1001234567890
   RIGHT: GROUP_CHAT_ID=-1001234567890

4. Bot is not admin
   Fix: Make bot admin in group settings

5. Bot doesn't have Send Messages permission
   Fix: Go to bot admin settings, check "Send Messages"

6. Using channel instead of group
   Channels won't work - use a GROUP

7. Wrong group ID (from different group)
   Make sure the ID is from YOUR group


VERIFICATION
============
To verify setup is correct:
  1. Open terminal
  2. Run: python diagnose_group_posting.py
  3. It will test posting a message
  4. Check your group for test message
  5. If you see it, everything works!


NEXT STEPS
==========
1. Add GROUP_CHAT_ID to .env
2. Make bot admin in group
3. Restart bot: python sniper_bot.py
4. Wait for new projects to launch
5. Bot will auto-post when rating is 75+


NEED HELP?
==========
For detailed guide:
  python troubleshoot_group_posting.py

For automated setup:
  python setup_group_id.py

For diagnostics:
  python diagnose_group_posting.py


YOU'RE ALMOST THERE!
===================
Just need to add GROUP_CHAT_ID and you're done!
The bot will handle the rest automatically.

""")

# Save to file too
with open('QUICK_FIX_GROUP_POSTING.txt', 'w', encoding='utf-8') as f:
    f.write("""
QUICK FIX - GROUP POSTING NOT WORKING
======================================

PROBLEM: GROUP_CHAT_ID is empty in .env

SOLUTION:
1. Get your group ID (add @userinfobot to group, it sends ID)
2. Add to .env: GROUP_CHAT_ID=-1001234567890 (your ID)
3. Save .env
4. Restart bot: python sniper_bot.py

VERIFICATION:
1. Run: python diagnose_group_posting.py
2. It will send test message to your group
3. If you see it, everything works!

DONE! Bot will now post good projects to your group.
    """)

print("\nQuick fix guide saved to: QUICK_FIX_GROUP_POSTING.txt")
