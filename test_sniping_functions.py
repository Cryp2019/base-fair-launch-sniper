#!/usr/bin/env python3
"""
Test script for enhanced sniping functions
Tests each function individually to verify improvements
"""
import os
import sys
from bot import (
    is_renounced,
    get_creator_address,
    check_honeypot,
    check_taxes,
    get_lock_duration,
    is_liquidity_locked,
    get_new_pairs,
    analyze_new_pair,
    w3
)

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

print("=" * 60)
print("SNIPING FUNCTIONS TEST SUITE")
print("=" * 60)

# Test 1: Check Web3 connection
print("\n[TEST 1] Web3 Connection")
try:
    block_number = w3.eth.block_number
    print(f"✅ Connected to Base chain - Current block: {block_number}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Test 2: Test is_renounced function
print("\n[TEST 2] Ownership Renouncement Check")
test_addresses = [
    ("0x0000000000000000000000000000000000000000", True, "Zero address"),
    ("0x000000000000000000000000000000000000dEaD", True, "Dead address"),
    ("0x0000000000000000000000000000000000000001", True, "Burn address"),
    ("0x1234567890123456789012345678901234567890", False, "Regular address")
]
for addr, expected, desc in test_addresses:
    result = is_renounced(addr)
    status = "✅" if result == expected else "❌"
    print(f"{status} {desc}: {result}")

# Test 3: Get new pairs
print("\n[TEST 3] Fetching New Pairs (last 50 blocks)")
try:
    current_block = w3.eth.block_number
    pairs = get_new_pairs(current_block - 50)
    print(f"✅ Found {len(pairs)} new pairs in last 50 blocks")
    for i, pair in enumerate(pairs[:3], 1):
        print(f"   {i}. {pair}")
except Exception as e:
    print(f"❌ Failed to get pairs: {e}")

# Test 4: Test honeypot detection (if pairs found)
if pairs:
    print("\n[TEST 4] Honeypot Detection on First Pair")
    try:
        test_pair = pairs[0]
        print(f"Testing pair: {test_pair}")
        
        # Get token address from pair
        from bot import UNISWAP_POOL_ABI
        pair_contract = w3.eth.contract(address=test_pair, abi=UNISWAP_POOL_ABI)
        token0 = pair_contract.functions.token0().call().lower()
        token1 = pair_contract.functions.token1().call().lower()
        
        # Get non-USDC token
        from bot import USDC_ADDRESS
        test_token = token0 if token1 == USDC_ADDRESS else token1
        
        print(f"Token address: {test_token}")
        
        honeypot_result = check_honeypot(test_token, test_pair)
        print(f"Is Honeypot: {honeypot_result['is_honeypot']}")
        print(f"Buy Tax: {honeypot_result['buy_tax']}%")
        print(f"Sell Tax: {honeypot_result['sell_tax']}%")
        if honeypot_result['honeypot_reason']:
            print(f"Reason: {honeypot_result['honeypot_reason']}")
        print("✅ Honeypot detection working")
    except Exception as e:
        print(f"⚠️ Honeypot check failed (may be expected): {e}")

# Test 5: Test liquidity lock detection
if pairs:
    print("\n[TEST 5] Liquidity Lock Detection")
    try:
        test_pair = pairs[0]
        lock_info = is_liquidity_locked(test_pair)
        print(f"Locked: {lock_info['locked']}")
        print(f"Days: {lock_info['days']}")
        print(f"Percent Locked: {lock_info.get('percent_locked', 0)}%")
        if lock_info.get('locker_name'):
            print(f"Locker: {lock_info['locker_name']}")
        print("✅ Lock detection working")
    except Exception as e:
        print(f"⚠️ Lock check failed: {e}")

# Test 6: Full analysis on first pair
if pairs:
    print("\n[TEST 6] Full Fair Launch Analysis")
    try:
        test_pair = pairs[0]
        print(f"Analyzing: {test_pair}")
        analysis = analyze_new_pair(test_pair)
        
        if analysis:
            print(f"\n📊 ANALYSIS RESULTS:")
            print(f"   Token: {analysis['name']} (${analysis['symbol']})")
            print(f"   Address: {analysis['token_address']}")
            print(f"   Renounced: {'✅' if analysis['renounced'] else '❌'}")
            print(f"   Pre-mine: {analysis['premine_ratio']}%")
            print(f"   LP Locked: {'✅' if analysis['liquidity_locked'] else '❌'} ({analysis['lock_days']} days)")
            print(f"   Honeypot: {'❌' if analysis['is_honeypot'] else '✅'}")
            print(f"   Buy Tax: {analysis['buy_tax']}%")
            print(f"   Sell Tax: {analysis['sell_tax']}%")
            print(f"\n   🎯 FAIR LAUNCH: {'✅ YES' if analysis['is_fair'] else '❌ NO'}")
            print("\n✅ Full analysis working!")
        else:
            print("⚠️ Analysis returned None (may be USDC-only pair)")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

# Test 7: Creator address detection
if pairs:
    print("\n[TEST 7] Creator Address Detection")
    try:
        # Use token from previous test
        from bot import UNISWAP_POOL_ABI
        pair_contract = w3.eth.contract(address=pairs[0], abi=UNISWAP_POOL_ABI)
        token0 = pair_contract.functions.token0().call().lower()
        token1 = pair_contract.functions.token1().call().lower()
        
        from bot import USDC_ADDRESS
        test_token = token0 if token1 == USDC_ADDRESS else token1
        
        creator = get_creator_address(test_token)
        if creator:
            print(f"✅ Creator found: {creator}")
        else:
            print("⚠️ Creator not found (may be expected for some tokens)")
    except Exception as e:
        print(f"⚠️ Creator detection failed: {e}")

print("\n" + "=" * 60)
print("TEST SUITE COMPLETE")
print("=" * 60)
print("\n💡 Next Steps:")
print("1. Review test results above")
print("2. If all tests pass, the bot is ready to detect fair launches")
print("3. Monitor bot logs when running to see live detections")
print("4. Consider adding BASESCAN_API_KEY to .env for better results")
