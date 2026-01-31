#!/usr/bin/env python3
"""
Manual token checker - Test a specific token or pair address
Usage: python check_token.py <address>
"""
import os
import sys
import asyncio

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from bot import (
    analyze_new_pair,
    check_honeypot,
    is_liquidity_locked,
    get_creator_address,
    w3,
    USDC_ADDRESS,
    UNISWAP_POOL_ABI,
    ERC20_ABI
)

def print_analysis(analysis):
    """Pretty print analysis results"""
    if not analysis:
        print("\n[X] Analysis returned None - might not be a valid USDC pair")
        return
    
    print("\n" + "=" * 70)
    print("TOKEN ANALYSIS RESULTS")
    print("=" * 70)
    
    print(f"\nToken: {analysis['name']} (${analysis['symbol']})")
    print(f"Address: {analysis['token_address']}")
    print(f"Pair: {analysis['pair_address']}")
    
    print(f"\n--- FAIR LAUNCH CHECKS ---")
    print(f"[{'OK' if analysis['renounced'] else 'X'}] Ownership Renounced: {analysis['renounced']}")
    print(f"[{'OK' if analysis['premine_ratio'] <= 5 else 'X'}] Pre-mine: {analysis['premine_ratio']}% (max 5%)")
    print(f"[{'OK' if analysis['liquidity_locked'] else 'X'}] LP Locked: {analysis['liquidity_locked']}")
    
    if analysis['liquidity_locked']:
        print(f"    Lock Days: {analysis['lock_days']}")
        if analysis.get('lock_percent'):
            print(f"    Lock %: {analysis['lock_percent']}%")
        if analysis.get('locker_name'):
            print(f"    Locker: {analysis['locker_name']}")
    
    print(f"[{'OK' if not analysis['is_honeypot'] else 'X'}] Honeypot Check: {'PASSED' if not analysis['is_honeypot'] else 'FAILED'}")
    if analysis['is_honeypot']:
        print(f"    Reason: {analysis.get('honeypot_reason', 'Unknown')}")
    
    print(f"[{'OK' if analysis['buy_tax'] <= 5 else 'X'}] Buy Tax: {analysis['buy_tax']}% (max 5%)")
    print(f"[{'OK' if analysis['sell_tax'] <= 5 else 'X'}] Sell Tax: {analysis['sell_tax']}% (max 5%)")
    
    print(f"\n--- FINAL VERDICT ---")
    if analysis['is_fair']:
        print("[OK] FAIR LAUNCH - All checks passed!")
    else:
        print("[X] NOT A FAIR LAUNCH - Failed one or more checks")
        print("\nReasons:")
        if not analysis['renounced']:
            print("  - Ownership not renounced")
        if analysis['premine_ratio'] > 5:
            print(f"  - Pre-mine too high ({analysis['premine_ratio']}%)")
        if not analysis['liquidity_locked']:
            print("  - Liquidity not locked")
        elif analysis['lock_days'] < 30:
            print(f"  - Lock period too short ({analysis['lock_days']} days)")
        if analysis['is_honeypot']:
            print(f"  - Honeypot detected: {analysis.get('honeypot_reason')}")
        if analysis['buy_tax'] > 5:
            print(f"  - Buy tax too high ({analysis['buy_tax']}%)")
        if analysis['sell_tax'] > 5:
            print(f"  - Sell tax too high ({analysis['sell_tax']}%)")
    
    print("=" * 70)

def check_token_address(address):
    """Check if address is a token and find/create pair"""
    print(f"\nChecking if {address} is a token contract...")
    
    try:
        # Try to read as ERC20 token
        token_contract = w3.eth.contract(address=address, abi=ERC20_ABI)
        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        
        print(f"[OK] Found token: {name} (${symbol})")
        print(f"\n[!] This is a token address, not a pair address.")
        print(f"[!] The bot needs the Uniswap pair address to analyze.")
        print(f"\nTo find the pair address:")
        print(f"1. Go to https://basescan.org/token/{address}")
        print(f"2. Look for 'Uniswap V3' or 'Uniswap V2' pair with USDC")
        print(f"3. Use that pair address with this tool")
        
        return None
    except Exception as e:
        # Not a token, might be a pair
        return address

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_token.py <token_or_pair_address>")
        print("\nExample:")
        print("  python check_token.py 0x1234567890123456789012345678901234567890")
        sys.exit(1)
    
    address = sys.argv[1].strip()
    
    # Validate address format
    if not address.startswith('0x') or len(address) != 42:
        print(f"[X] Invalid address format: {address}")
        print("Address should be 42 characters starting with 0x")
        sys.exit(1)
    
    print("=" * 70)
    print("MANUAL TOKEN CHECKER")
    print("=" * 70)
    print(f"\nAddress: {address}")
    
    # Check if it's a token or pair
    pair_address = check_token_address(address)
    if not pair_address:
        sys.exit(0)
    
    # Analyze the pair
    print(f"\nAnalyzing pair: {pair_address}")
    print("This may take 10-30 seconds (calling Honeypot.is API)...")
    
    try:
        analysis = analyze_new_pair(pair_address)
        print_analysis(analysis)
    except Exception as e:
        print(f"\n[X] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
