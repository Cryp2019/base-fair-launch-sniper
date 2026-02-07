#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive setup wizard for group posting
"""
import os
import re

def main():
    print("\n" + "="*70)
    print("INTERACTIVE GROUP POSTING SETUP")
    print("="*70 + "\n")
    
    print("""
Step 1: Get your Telegram group ID
===================================
How to get your group ID:

Option A (Easiest):
  1. Open Telegram app
  2. Go to your group
  3. Search for bot: @userinfobot
  4. Add @userinfobot to the group
  5. It will send you a message with ID
  6. Example: "ID: -1001234567890"
  7. Copy that ID (with the minus sign)

Option B:
  1. Search for: @RawDataBot
  2. Add to your group
  3. It sends JSON with "chat": {"id": -1001234567890}
  4. Use that ID
    """)
    
    while True:
        group_id = input("Enter your group ID (example: -1001234567890): ").strip()
        
        # Validate format
        if not group_id:
            print("ERROR: Group ID cannot be empty")
            continue
        
        # Add minus if missing
        if group_id.startswith('@'):
            print("ERROR: You entered a username. Use the numeric ID instead.")
            print("       The ID should be a negative number like: -1001234567890")
            continue
        
        if not group_id.startswith('-'):
            # Try to parse as positive number
            try:
                num = int(group_id)
                if num > 0:
                    group_id = '-' + group_id
                    print(f"NOTE: Added minus sign. Using: {group_id}")
            except ValueError:
                print("ERROR: Group ID must be a number")
                continue
        
        # Validate it's a number
        try:
            id_int = int(group_id)
            if id_int >= 0:
                print("ERROR: Group ID should be negative (start with -)")
                continue
            break
        except ValueError:
            print("ERROR: Invalid format. Should be like: -1001234567890")
            continue
    
    print(f"\nGRoup ID: {group_id}")
    
    # Step 2: Update .env
    print("\n" + "-"*70)
    print("Step 2: Updating .env file")
    print("-"*70 + "\n")
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Replace GROUP_CHAT_ID
        new_content = re.sub(
            r'GROUP_CHAT_ID=.*',
            f'GROUP_CHAT_ID={group_id}',
            env_content
        )
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"SUCCESS: Updated .env")
        print(f"  GROUP_CHAT_ID={group_id}\n")
    except Exception as e:
        print(f"ERROR: Failed to update .env: {e}\n")
        return False
    
    # Step 3: Bot permissions
    print("-"*70)
    print("Step 3: Make bot admin in Telegram")
    print("-"*70)
    print("""
IMPORTANT: Your bot needs to be an ADMINISTRATOR in the group

Follow these steps in Telegram:
  1. Open your group
  2. Find your bot in the members list
  3. Right-click the bot
  4. Select "Promote as Administrator"
  5. Make sure these are CHECKED:
     - Send Messages
     - Send Media
     - Manage Chat (optional)
  6. Click "Save"

Without these permissions, the bot cannot post!
    """)
    
    ready = input("Have you made the bot admin? (yes/no): ").strip().lower()
    if ready not in ['yes', 'y']:
        print("\nPlease make the bot admin first, then run this script again.\n")
        return False
    
    # Step 4: Restart bot
    print("\n" + "-"*70)
    print("Step 4: Restart the bot")
    print("-"*70 + "\n")
    
    print("""
The bot is now configured! Here's what to do:

1. In the terminal running the bot:
   Press Ctrl+C to stop it

2. Start the bot again:
   python sniper_bot.py

3. Wait for this message:
   "Group posting enabled - Buy buttons active"

4. The bot is now ready to post!
   It will automatically post good projects (75+ rating) to your group.

5. To verify it works:
   Run: python diagnose_group_posting.py
   (It will try to send a test message to your group)
    """)
    
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print("""
Next steps:
  1. Stop the bot (Ctrl+C)
  2. Run: python sniper_bot.py
  3. Check group for test message (optional: run diagnose)
  4. Wait for new projects to launch
  5. Bot will post automatically!

Your group posting is now ENABLED and ready to go! (emoji)
    """)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            print("\nSetup incomplete. Try again.\n")
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.\n")
    except Exception as e:
        print(f"\nError: {e}\n")
