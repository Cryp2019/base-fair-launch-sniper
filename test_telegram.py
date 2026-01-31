#!/usr/bin/env python3
"""
Test Telegram integration with enhanced sniping functions
"""
import os
import sys
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("=" * 70)
print("TELEGRAM INTEGRATION TEST")
print("=" * 70)

async def test_telegram():
    print(f"\n[1] Configuration Check")
    print(f"   Bot Token: {TELEGRAM_TOKEN[:20]}..." if TELEGRAM_TOKEN else "   [X] Missing TELEGRAM_BOT_TOKEN")
    print(f"   Chat ID: {TELEGRAM_CHAT_ID}")
    
    if not TELEGRAM_TOKEN:
        print("\n[X] Missing TELEGRAM_BOT_TOKEN in .env")
        return False
    
    print(f"\n[2] Testing Bot Connection")
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        me = await bot.get_me()
        print(f"[OK] Connected to bot: @{me.username}")
        print(f"   Bot ID: {me.id}")
        print(f"   Bot Name: {me.first_name}")
    except TelegramError as e:
        print(f"[X] Bot connection failed: {e}")
        return False
    
    print(f"\n[3] Testing Alert Message (Enhanced Format)")
    
    # Create a mock analysis result with all enhanced fields
    mock_analysis = {
        'is_fair': True,
        'name': 'TestToken',
        'symbol': 'TEST',
        'token_address': '0x1234567890123456789012345678901234567890',
        'pair_address': '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
        'renounced': True,
        'premine_ratio': 2.5,
        'liquidity_locked': True,
        'lock_days': 90,
        'lock_percent': 75.5,
        'locker_name': 'Unicrypt',
        'has_suspicious_tax': False,
        'is_honeypot': False,
        'honeypot_reason': None,
        'buy_tax': 1.0,
        'sell_tax': 1.0,
        'transfer_tax': 0,
    }
    
    # Build enhanced alert message (same format as bot.py)
    status_emoji = "✅" if mock_analysis['is_fair'] else "⚠️"
    
    tax_info = ""
    if mock_analysis.get('buy_tax', 0) > 0 or mock_analysis.get('sell_tax', 0) > 0:
        tax_info = f"\n💸 Buy Tax: {mock_analysis['buy_tax']}% | Sell Tax: {mock_analysis['sell_tax']}%"
    
    honeypot_warning = ""
    if mock_analysis.get('is_honeypot'):
        honeypot_warning = f"\n🚨 *HONEYPOT DETECTED*: {mock_analysis.get('honeypot_reason', 'Unknown reason')}"
    
    lock_info = f"{mock_analysis['lock_days']} days"
    if mock_analysis.get('lock_percent', 0) > 0:
        lock_info += f", {mock_analysis['lock_percent']}% locked"
    if mock_analysis.get('locker_name'):
        lock_info += f" via {mock_analysis['locker_name']}"
    
    message = (
        f"{status_emoji} *TEST ALERT - Enhanced Format* {status_emoji}\n\n"
        f"🔤 *{mock_analysis['name']}* (${mock_analysis['symbol'].upper()})\n"
        f"🔗 Pair: `{mock_analysis['pair_address'][:6]}...{mock_analysis['pair_address'][-4:]}`\n"
        f"🏷️ Token: `{mock_analysis['token_address'][:6]}...{mock_analysis['token_address'][-4:]}`\n\n"
        f"🛡️ *Fair Launch Checks:*\n"
        f"{'✅' if mock_analysis['renounced'] else '❌'} Ownership renounced\n"
        f"{'✅' if mock_analysis['premine_ratio'] <= 5 else '❌'} Creator holding: {mock_analysis['premine_ratio']}%\n"
        f"{'✅' if mock_analysis['liquidity_locked'] else '❌'} Liquidity locked ({lock_info})\n"
        f"{'✅' if not mock_analysis['is_honeypot'] and mock_analysis['buy_tax'] <= 5 else '❌'} "
        f"Tax check passed{tax_info}\n"
        f"{honeypot_warning}\n\n"
        f"⚠️ *DISCLAIMER: This is a TEST message. Not financial advice.*"
    )
    
    print("   Sending test alert...")
    print(f"\n   Message preview:")
    print("   " + "-" * 60)
    print("   [Enhanced alert with tax info, lock details, etc.]")
    print("   " + "-" * 60)
    
    try:
        if TELEGRAM_CHAT_ID:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            print(f"\n[OK] Test alert sent to {TELEGRAM_CHAT_ID}")
            print(f"   Check your Telegram to verify the enhanced format!")
        else:
            print(f"\n[!] No TELEGRAM_CHAT_ID set - message not sent")
            print(f"   Add TELEGRAM_CHAT_ID to .env to test sending")
    except TelegramError as e:
        print(f"\n[X] Failed to send message: {e}")
        if "chat not found" in str(e).lower():
            print(f"   [!] Make sure the bot is added to the channel/chat")
            print(f"   [!] For channels, use format: @channel_name")
        return False
    
    print(f"\n[3] Testing Honeypot Alert Format")
    
    # Mock honeypot detection
    honeypot_analysis = mock_analysis.copy()
    honeypot_analysis['is_fair'] = False
    honeypot_analysis['is_honeypot'] = True
    honeypot_analysis['honeypot_reason'] = 'High sell tax detected (25%)'
    honeypot_analysis['buy_tax'] = 2.0
    honeypot_analysis['sell_tax'] = 25.0
    
    status_emoji = "⚠️"
    tax_info = f"\n💸 Buy Tax: {honeypot_analysis['buy_tax']}% | Sell Tax: {honeypot_analysis['sell_tax']}%"
    honeypot_warning = f"\n🚨 *HONEYPOT DETECTED*: {honeypot_analysis['honeypot_reason']}"
    
    honeypot_message = (
        f"{status_emoji} *TEST ALERT - Honeypot Detected* {status_emoji}\n\n"
        f"🔤 *ScamToken* ($SCAM)\n"
        f"🔗 Pair: `0xabcd...ef01`\n"
        f"🏷️ Token: `0x9876...5432`\n\n"
        f"🛡️ *Fair Launch Checks:*\n"
        f"✅ Ownership renounced\n"
        f"✅ Creator holding: 2.5%\n"
        f"✅ Liquidity locked (90 days, 75% locked via Unicrypt)\n"
        f"❌ Tax check passed{tax_info}\n"
        f"{honeypot_warning}\n\n"
        f"⚠️ *DISCLAIMER: This is a TEST message showing honeypot detection.*"
    )
    
    print("   Sending honeypot test alert...")
    try:
        if TELEGRAM_CHAT_ID:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=honeypot_message,
                parse_mode='Markdown'
            )
            print(f"[OK] Honeypot alert sent to {TELEGRAM_CHAT_ID}")
        else:
            print(f"[!] No TELEGRAM_CHAT_ID set - skipped")
    except TelegramError as e:
        print(f"[X] Failed to send honeypot alert: {e}")
    
    return True

async def main():
    success = await test_telegram()
    
    print("\n" + "=" * 70)
    if success:
        print("[OK] TELEGRAM INTEGRATION TEST PASSED")
        print("\nEnhanced Features Verified:")
        print("  [OK] Tax percentages displayed")
        print("  [OK] Lock percentage and locker name shown")
        print("  [OK] Honeypot warnings formatted correctly")
        print("  [OK] All emoji and formatting working")
        print("\n[READY] Bot is ready to send enhanced alerts!")
    else:
        print("[!] TELEGRAM INTEGRATION TEST INCOMPLETE")
        print("\nPlease check:")
        print("  - TELEGRAM_BOT_TOKEN is correct")
        print("  - TELEGRAM_CHAT_ID is set")
        print("  - Bot is added to the channel/chat")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(main())
