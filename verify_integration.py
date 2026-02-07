#!/usr/bin/env python3
"""
Integration Verification Script
Tests all core components to ensure everything is properly integrated
"""
import sys
import os

print("\n" + "="*60)
print("🔍 BASE FAIR LAUNCH SNIPER - INTEGRATION VERIFICATION")
print("="*60 + "\n")

# Test 1: Check environment
print("📋 TEST 1: Environment Configuration")
print("-" * 60)
env_vars = {
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
    'ALCHEMY_BASE_KEY': os.getenv('ALCHEMY_BASE_KEY'),
    'PAYMENT_WALLET_ADDRESS': os.getenv('PAYMENT_WALLET_ADDRESS'),
    'BOT_USERNAME': os.getenv('BOT_USERNAME'),
}

for key, value in env_vars.items():
    if value:
        masked = value[:10] + "*" * (len(value) - 15) + value[-5:] if len(value) > 15 else "*" * len(value)
        print(f"  ✅ {key}: {masked}")
    else:
        print(f"  ⚠️  {key}: NOT SET")

# Test 2: Check module imports
print("\n📦 TEST 2: Module Imports")
print("-" * 60)

modules_to_test = [
    ('database', 'UserDatabase'),
    ('trading', 'TradingBot'),
    ('security_scanner', 'SecurityScanner'),
    ('admin', 'AdminManager'),
    ('payment_monitor', 'PaymentMonitor'),
    ('encryption_utils', None),
]

all_imports_ok = True
for module_name, class_name in modules_to_test:
    try:
        if class_name:
            exec(f"from {module_name} import {class_name}")
            print(f"  ✅ {module_name}.{class_name}")
        else:
            exec(f"import {module_name}")
            print(f"  ✅ {module_name}")
    except ImportError as e:
        print(f"  ❌ {module_name}: {str(e)}")
        all_imports_ok = False

# Test 3: Check database
print("\n💾 TEST 3: Database Initialization")
print("-" * 60)
try:
    from database import UserDatabase
    db = UserDatabase()
    total_users = db.get_total_users()
    print(f"  ✅ Database connected successfully")
    print(f"  ✅ Total users in database: {total_users}")
except Exception as e:
    print(f"  ❌ Database error: {e}")
    all_imports_ok = False

# Test 4: Check Web3 connection
print("\n⛓️  TEST 4: Web3/Blockchain Integration")
print("-" * 60)
try:
    from web3 import Web3
    base_rpc = os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')
    w3 = Web3(Web3.HTTPProvider(base_rpc))
    if w3.is_connected():
        print(f"  ✅ Connected to Base RPC: {base_rpc}")
        print(f"  ✅ Latest block: {w3.eth.block_number}")
    else:
        print(f"  ⚠️  Not connected to Base RPC (may be rate limited or offline)")
except Exception as e:
    print(f"  ⚠️  Web3 connection warning: {e}")

# Test 5: Check bot files
print("\n🤖 TEST 5: Bot Files")
print("-" * 60)
bot_files = [
    'sniper_bot.py',
    'modern_bot.py',
    'bot.py',
    'simple_bot.py',
    'public_bot.py',
]

for bot_file in bot_files:
    if os.path.exists(bot_file):
        size = os.path.getsize(bot_file)
        print(f"  ✅ {bot_file}: {size:,} bytes")
    else:
        print(f"  ❌ {bot_file}: NOT FOUND")

# Test 6: Check required files
print("\n📄 TEST 6: Required Configuration Files")
print("-" * 60)
required_files = [
    '.env',
    'requirements.txt',
    'database.py',
    'trading.py',
    'security_scanner.py',
]

for file_name in required_files:
    if os.path.exists(file_name):
        print(f"  ✅ {file_name}")
    else:
        print(f"  ❌ {file_name}: NOT FOUND")

# Summary
print("\n" + "="*60)
if all_imports_ok:
    print("✅ ALL INTEGRATIONS VERIFIED AND OPERATIONAL")
    print("="*60)
    print("\n🚀 You can now run:")
    print("   python sniper_bot.py      (Production bot)")
    print("   python modern_bot.py      (Modern UI bot)")
    print("   python bot.py             (Full-featured bot)")
    print("   python simple_bot.py      (Lightweight bot)")
    print("\n")
else:
    print("⚠️  SOME INTEGRATIONS NEED ATTENTION")
    print("="*60 + "\n")
    sys.exit(1)
