#!/usr/bin/env python3
"""
Diagnostic script to check why the bot isn't sending alerts
"""
import os
import sys
from web3 import Web3
from database import UserDatabase

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

ALCHEMY_KEY = os.getenv('ALCHEMY_BASE_KEY')
BASE_RPC = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

print("=" * 60)
print("🔍 BOT DIAGNOSTIC TOOL")
print("=" * 60)
print()

# 1. Check database
print("1️⃣ Checking database...")
try:
    db = UserDatabase()
    print(f"   ✅ Database path: {db.db_path}")
    print(f"   ✅ Database exists: {os.path.exists(db.db_path)}")
    
    # Check users
    users_with_alerts = db.get_users_with_alerts()
    print(f"   📊 Users with alerts enabled: {len(users_with_alerts)}")
    
    if len(users_with_alerts) == 0:
        print("   ⚠️  WARNING: No users have alerts enabled!")
        print("   💡 Solution: Send /start to the bot and enable alerts")
    else:
        print(f"   ✅ Alert recipients: {[u['user_id'] for u in users_with_alerts]}")
        
except Exception as e:
    print(f"   ❌ Database error: {e}")

print()

# 2. Check RPC connection
print("2️⃣ Checking Base RPC connection...")
try:
    w3 = Web3(Web3.HTTPProvider(BASE_RPC))
    if w3.is_connected():
        block = w3.eth.block_number
        print(f"   ✅ Connected to Base")
        print(f"   📦 Current block: {block:,}")
    else:
        print(f"   ❌ Failed to connect to Base RPC")
except Exception as e:
    print(f"   ❌ RPC error: {e}")

print()

# 3. Check for recent pairs
print("3️⃣ Checking for recent pair creations...")
try:
    from sniper_bot import get_new_pairs, FACTORIES
    
    current_block = w3.eth.block_number
    last_block = current_block - 1000  # Check last 1000 blocks (~30 minutes)
    
    print(f"   🔍 Scanning blocks {last_block:,} to {current_block:,}")
    print(f"   📊 Monitoring {len(FACTORIES)} DEXs:")
    for dex_id, config in FACTORIES.items():
        if config.get('enabled', True):
            print(f"      {config['emoji']} {config['name']}")
    
    print()
    print("   ⏳ Scanning... (this may take a moment)")
    
    pairs = get_new_pairs(last_block)
    
    if len(pairs) > 0:
        print(f"   ✅ Found {len(pairs)} pair(s) in last 1000 blocks:")
        for pair in pairs[:5]:  # Show first 5
            print(f"      {pair.get('dex_emoji', '🔷')} {pair.get('dex_name', 'Unknown')}: {pair['address'][:10]}... ({pair['pair_type']})")
        if len(pairs) > 5:
            print(f"      ... and {len(pairs) - 5} more")
    else:
        print(f"   ⚠️  No new pairs found in last 1000 blocks")
        print(f"   💡 This is normal if there haven't been recent launches")
        
except Exception as e:
    print(f"   ❌ Scanning error: {e}")
    import traceback
    traceback.print_exc()

print()

# 4. Check Telegram token
print("4️⃣ Checking Telegram configuration...")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if TELEGRAM_TOKEN:
    print(f"   ✅ Telegram token configured")
    print(f"   🤖 Token starts with: {TELEGRAM_TOKEN[:10]}...")
else:
    print(f"   ❌ TELEGRAM_BOT_TOKEN not set!")

print()

# 5. Summary
print("=" * 60)
print("📋 SUMMARY")
print("=" * 60)

issues = []
if len(users_with_alerts) == 0:
    issues.append("No users have alerts enabled")
if not w3.is_connected():
    issues.append("RPC connection failed")
if not TELEGRAM_TOKEN:
    issues.append("Telegram token not configured")

if len(issues) == 0:
    print("✅ All checks passed!")
    print()
    print("💡 If bot still not sending alerts:")
    print("   1. Check Railway logs for errors")
    print("   2. Verify bot is running (not stopped)")
    print("   3. Wait for a new token launch (may take time)")
    print("   4. Test with /checktoken command")
else:
    print("⚠️  Issues found:")
    for issue in issues:
        print(f"   - {issue}")
    print()
    print("💡 Fix these issues and try again")

print()
print("=" * 60)
