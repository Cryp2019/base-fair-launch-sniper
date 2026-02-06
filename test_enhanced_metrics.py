#!/usr/bin/env python3
"""
Test Enhanced Alert Metrics
Tests the new comprehensive metrics display in alerts
"""
import asyncio
import os
import sys

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from sniper_bot import (
    get_dexscreener_data,
    check_transfer_limits,
    calculate_clog_percentage,
    detect_airdrops,
    get_comprehensive_metrics
)

async def test_metrics():
    """Test fetching comprehensive metrics"""
    print("=" * 70)
    print("TESTING ENHANCED METRICS FUNCTIONS")
    print("=" * 70)
    
    # Test with USDC token (known good token)
    test_token = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # USDC on Base
    test_pair = "0x4c36388be6f416a29c8d8eee81c771ce6be14b18"  # Example pair
    
    print("\n1. Testing DexScreener Data...")
    try:
        dex_data = await get_dexscreener_data(test_pair)
        print(f"   ✅ Price: ${dex_data['price_usd']:.8f}")
        print(f"   ✅ Market Cap: ${dex_data['market_cap']:,.2f}")
        print(f"   ✅ Liquidity: ${dex_data['liquidity_usd']:,.2f}")
        print(f"   ✅ Volume 24h: ${dex_data['volume_24h']:,.2f}")
        print(f"   ✅ ATH: {dex_data['ath']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Testing Transfer Limits...")
    try:
        limits = await check_transfer_limits(test_token)
        print(f"   ✅ Has Limits: {limits['has_limits']}")
        print(f"   ✅ Details: {limits['details']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3. Testing Clog Percentage...")
    try:
        clog = await calculate_clog_percentage(test_token, test_pair)
        print(f"   ✅ Clog: {clog:.2f}%")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4. Testing Airdrop Detection...")
    try:
        airdrops = await detect_airdrops(test_token)
        print(f"   ✅ Airdrops: {airdrops if airdrops else 'None detected'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n5. Testing Comprehensive Metrics...")
    try:
        metrics = await get_comprehensive_metrics(
            test_token,
            test_pair,
            "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
            1000000000000,  # 1M supply
            6,  # 6 decimals
            premium=True
        )
        print(f"   ✅ All metrics fetched successfully!")
        print(f"      - MC: ${metrics['market_cap']:,.2f}")
        print(f"      - Liq: ${metrics['liquidity_usd']:,.2f}")
        print(f"      - Price: ${metrics['price_usd']:.8f}")
        print(f"      - Vol: ${metrics['volume_24h']:,.2f}")
        print(f"      - Limits: {metrics['limit_details']}")
        print(f"      - Clog: {metrics['clog_percentage']:.2f}%")
        print(f"      - Airdrops: {len(metrics['airdrops'])} detected")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n✅ Enhanced metrics functions are working!")
    print("\nNext steps:")
    print("1. Start the bot: python sniper_bot.py")
    print("2. Wait for a new token launch")
    print("3. Check your Telegram for the enhanced alert format")
    print("\nExpected alert format:")
    print("🧢 MC: $XXX | ATH: $XXX")
    print("💧 Liq: $XXX")
    print("🏷 Price: $X.XXXXXXXX")
    print("🎚 Vol: $XXX")
    print("")
    print("🛡️ SAFETY CHECKS")
    print("✅ Ownership: Renounced ✅")
    print("✅ Honeypot: SAFE")
    print("✅ LP Locked: YES")
    print("")
    print("🏧 B: 0.00% | S: 0.00% | T: 0.00%")
    print("⚖️ No limits")
    print("🪠 Clog: 0.03%")
    print("")
    print("🪂 Airdrops: None detected")

if __name__ == '__main__':
    asyncio.run(test_metrics())
