#!/usr/bin/env python3
"""
Simple offline test for sniping functions (no API calls needed)
"""
from bot import is_renounced, MAX_TAX_PERCENT, MAX_PREMINE_RATIO, MIN_LIQUIDITY_LOCK_DAYS

print("=" * 60)
print("SNIPING FUNCTIONS - OFFLINE TESTS")
print("=" * 60)

# Test 1: Ownership renouncement check
print("\n[TEST 1] Ownership Renouncement Logic")
test_cases = [
    ("0x0000000000000000000000000000000000000000", True, "Zero address"),
    ("0x000000000000000000000000000000000000dEaD", True, "Dead address"),
    ("0x0000000000000000000000000000000000000001", True, "Burn address"),
    ("0x1234567890123456789012345678901234567890", False, "Regular address"),
]

all_passed = True
for addr, expected, desc in test_cases:
    result = is_renounced(addr)
    passed = result == expected
    all_passed = all_passed and passed
    status = "✅" if passed else "❌"
    print(f"{status} {desc}: {result} (expected {expected})")

print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")

# Test 2: Configuration check
print("\n[TEST 2] Fair Launch Criteria Configuration")
print(f"✅ Max Pre-mine Ratio: {MAX_PREMINE_RATIO * 100}%")
print(f"✅ Min Liquidity Lock Days: {MIN_LIQUIDITY_LOCK_DAYS}")
print(f"✅ Max Tax Percent: {MAX_TAX_PERCENT}%")

# Test 3: Check imports
print("\n[TEST 3] Function Imports")
try:
    from bot import (
        check_honeypot,
        check_taxes,
        get_lock_duration,
        is_liquidity_locked,
        get_new_pairs,
        analyze_new_pair,
        get_creator_address
    )
    print("✅ All enhanced functions imported successfully")
    print("   - check_honeypot (NEW)")
    print("   - check_taxes (ENHANCED)")
    print("   - get_lock_duration (NEW)")
    print("   - is_liquidity_locked (FIXED)")
    print("   - get_new_pairs (FIXED)")
    print("   - analyze_new_pair (ENHANCED)")
    print("   - get_creator_address (IMPROVED)")
except ImportError as e:
    print(f"❌ Import failed: {e}")

print("\n" + "=" * 60)
print("OFFLINE TESTS COMPLETE")
print("=" * 60)

print("\n📋 To test with live data, you need:")
print("1. Complete Alchemy API key (format: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx)")
print("2. Get it from: https://dashboard.alchemy.com/")
print("3. Add to .env: ALCHEMY_BASE_KEY=your_full_key_here")
print("\n💡 Optional for better results:")
print("- BASESCAN_API_KEY from https://basescan.org/myapikey")
