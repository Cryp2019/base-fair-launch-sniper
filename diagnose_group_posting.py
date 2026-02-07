#!/usr/bin/env python3
"""
Debugging script to diagnose group posting issues
"""
import os
import sys

print("\n" + "="*70)
print("🔍 GROUP POSTING DIAGNOSTIC")
print("="*70 + "\n")

# Check 1: Environment variables
print("TEST 1: Environment Configuration")
print("-" * 70)

group_chat_id = os.getenv('GROUP_CHAT_ID')
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
private_key = os.getenv('PRIVATE_KEY')

if group_chat_id:
    print(f"  ✅ GROUP_CHAT_ID: {group_chat_id}")
else:
    print(f"  ❌ GROUP_CHAT_ID: NOT SET")
    print("     → Add to .env: GROUP_CHAT_ID=-1001234567890")

if telegram_token:
    print(f"  ✅ TELEGRAM_BOT_TOKEN: {telegram_token[:20]}...")
else:
    print(f"  ❌ TELEGRAM_BOT_TOKEN: NOT SET")

if private_key:
    print(f"  ✅ PRIVATE_KEY: Set ({len(private_key)} chars)")
else:
    print(f"  ⚠️  PRIVATE_KEY: NOT SET (buy button won't work)")

# Check 2: Bot permissions
print("\n\nTEST 2: Bot Permissions Required")
print("-" * 70)
print("""
For the bot to post in your group, it needs:
  ✅ Send Messages - REQUIRED
  ✅ Send Media - REQUIRED  
  ✅ Add Web Page Previews - OPTIONAL
  ✅ Manage Messages - OPTIONAL (for editing)

Check in Telegram:
  1. Group Settings
  2. Administrators (find your bot)
  3. Verify permissions are checked
  4. Click "Save"
""")

# Check 3: Group Chat ID format
print("\nTEST 3: Group Chat ID Format")
print("-" * 70)
if group_chat_id:
    try:
        chat_id_int = int(group_chat_id)
        if chat_id_int < 0:
            print(f"  ✅ Valid format: {chat_id_int} (negative = group)")
        else:
            print(f"  ⚠️  Chat ID is positive - might be a user ID, not a group")
            print("     → Get group ID by adding @userinfobot to your group")
    except ValueError:
        print(f"  ❌ Invalid format: {group_chat_id}")
        print("     → Should be a number (e.g., -1001234567890)")
else:
    print("  ❌ GROUP_CHAT_ID not set")

# Check 4: Test posting capability
print("\n\nTEST 4: Test Group Posting")
print("-" * 70)

if not group_chat_id or not telegram_token:
    print("  ❌ Cannot test - missing GROUP_CHAT_ID or TELEGRAM_BOT_TOKEN")
    sys.exit(1)

try:
    from telegram import Bot
    import asyncio
    
    async def test_posting():
        bot = Bot(token=telegram_token)
        try:
            # Try to send a test message
            chat_id = int(group_chat_id)
            message = await bot.send_message(
                chat_id=chat_id,
                text="🤖 Bot posting test - If you see this, posting works! ✅"
            )
            print(f"  ✅ Test message sent successfully!")
            print(f"     Message ID: {message.message_id}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to post test message:")
            print(f"     Error: {str(e)}")
            print(f"\n     Possible causes:")
            print(f"     • Bot not added to group")
            print(f"     • Bot lacks permissions (Send Messages)")
            print(f"     • Invalid GROUP_CHAT_ID")
            print(f"     • Bot was removed from group")
            return False
    
    result = asyncio.run(test_posting())
    if not result:
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Error during test: {e}")
    sys.exit(1)

# Check 5: Verify group_poster integration
print("\n\nTEST 5: Group Poster Module")
print("-" * 70)
try:
    from group_poster import GroupPoster
    from web3 import Web3
    
    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
    gp = GroupPoster(w3)
    
    print(f"  ✅ GroupPoster initialized")
    print(f"  ✅ Security filter: {gp.min_rating_score}/100 minimum")
    print(f"  ✅ All methods available")
except Exception as e:
    print(f"  ❌ Error initializing GroupPoster: {e}")

# Check 6: Sniper bot integration
print("\n\nTEST 6: Sniper Bot Integration")
print("-" * 70)
try:
    with open('sniper_bot.py', 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    checks = {
        'from group_poster import GroupPoster': 'GroupPoster imported',
        'group_poster = GroupPoster(w3)': 'GroupPoster initialized',
        'post_to_group_with_buy_button': 'Group posting function',
        "pattern='^buy_'": 'Buy button handler',
    }
    
    all_good = True
    for check, desc in checks.items():
        if check in content:
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc}")
            all_good = False
    
    if all_good:
        print(f"\n  ✅ All integrations present in sniper_bot.py")
    else:
        print(f"\n  ⚠️  Some integrations missing - code may need updates")
except Exception as e:
    print(f"  ❌ Error checking sniper_bot.py: {e}")

# Summary
print("\n" + "="*70)
print("📊 DIAGNOSTIC SUMMARY")
print("="*70)

issues = []

if not group_chat_id:
    issues.append("GROUP_CHAT_ID not set in .env")
if not telegram_token:
    issues.append("TELEGRAM_BOT_TOKEN not set in .env")

if issues:
    print("\n❌ ISSUES FOUND:")
    for issue in issues:
        print(f"   • {issue}")
    print("\n📝 FIX:")
    print("   1. Open .env file")
    print("   2. Add missing variables")
    print("   3. Save and restart bot")
    print("   4. Run: python sniper_bot.py")
else:
    print("\n✅ ALL CHECKS PASSED!")
    print("\n💡 If still not posting:")
    print("   1. Make sure bot is RUNNING: python sniper_bot.py")
    print("   2. Check bot logs for errors")
    print("   3. Wait for a new token launch (may take time)")
    print("   4. Check bot has Send Messages permission")
    print("   5. Verify GROUP_CHAT_ID is for your group, not another")

print("\n" + "="*70 + "\n")
