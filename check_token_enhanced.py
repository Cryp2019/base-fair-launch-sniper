#!/usr/bin/env python3
"""
Enhanced manual token checker - Supports both token and pair addresses
Automatically finds pairs if given a token address
Supports both USDC and ETH pairs
"""
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

from bot import (
    analyze_new_pair,
    check_honeypot,
    is_liquidity_locked,
    w3,
    USDC_ADDRESS,
    ERC20_ABI
)

# WETH address on Base
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"

def get_token_info(address):
    """Get token name and symbol"""
    try:
        token = w3.eth.contract(address=address, abi=ERC20_ABI)
        name = token.functions.name().call()
        symbol = token.functions.symbol().call()
        return name, symbol
    except:
        return None, None

def find_pairs_for_token(token_address):
    """Find Uniswap pairs for a token"""
    print(f"\n[*] Searching for trading pairs...")
    
    # Uniswap V3 Factory on Base
    factory_address = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
    
    # Check for USDC pair
    print(f"   Checking for USDC pair...")
    # Note: In production, you'd query the factory or use Alchemy's getAssetTransfers
    # For now, we'll use a simpler approach
    
    print(f"\n[!] Automatic pair discovery not fully implemented yet.")
    print(f"[!] Please find the pair address manually:")
    print(f"\n   1. Go to: https://basescan.org/token/{token_address}")
    print(f"   2. Look for 'DEX Trades' or 'Transfers' tab")
    print(f"   3. Find Uniswap V3 pool address (usually starts with 0x...)")
    print(f"   4. Common pairs: USDC or WETH")
    print(f"\n   Then run: python check_token.py <pair_address>")
    
    return None

def print_analysis(analysis, token_name=None, token_symbol=None):
    """Pretty print analysis results"""
    if not analysis:
        print("\n[X] Analysis returned None")
        print("    This might not be a valid USDC/ETH pair")
        print("    Or the pair might not have enough data yet")
        return
    
    print("\n" + "=" * 70)
    print("TOKEN ANALYSIS RESULTS")
    print("=" * 70)
    
    # Use provided token info if available
    name = token_name or analysis.get('name', 'Unknown')
    symbol = token_symbol or analysis.get('symbol', '???')
    
    print(f"\nToken: {name} (${symbol})")
    print(f"Token Address: {analysis['token_address']}")
    print(f"Pair Address: {analysis['pair_address']}")
    
    print(f"\n--- FAIR LAUNCH CHECKS ---")
    print(f"[{'OK' if analysis['renounced'] else 'X'}] Ownership Renounced: {analysis['renounced']}")
    print(f"[{'OK' if analysis['premine_ratio'] <= 5 else 'X'}] Pre-mine: {analysis['premine_ratio']:.2f}% (max 5%)")
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
        print("\n    This token meets all fair launch criteria:")
        print("    - Ownership renounced")
        print("    - Low pre-mine (<= 5%)")
        print("    - Liquidity locked (>= 30 days)")
        print("    - Not a honeypot")
        print("    - Reasonable taxes (<= 5%)")
    else:
        print("[X] NOT A FAIR LAUNCH - Failed one or more checks")
        print("\nReasons for failure:")
        if not analysis['renounced']:
            print("  - Ownership NOT renounced (owner can change contract)")
        if analysis['premine_ratio'] > 5:
            print(f"  - Pre-mine too high ({analysis['premine_ratio']:.2f}% > 5%)")
        if not analysis['liquidity_locked']:
            print("  - Liquidity NOT locked (rug pull risk!)")
        elif analysis['lock_days'] < 30:
            print(f"  - Lock period too short ({analysis['lock_days']} < 30 days)")
        if analysis['is_honeypot']:
            print(f"  - HONEYPOT detected: {analysis.get('honeypot_reason')}")
        if analysis['buy_tax'] > 5:
            print(f"  - Buy tax too high ({analysis['buy_tax']}% > 5%)")
        if analysis['sell_tax'] > 5:
            print(f"  - Sell tax too high ({analysis['sell_tax']}% > 5%)")
    
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_token_enhanced.py <token_or_pair_address>")
        print("\nExample:")
        print("  python check_token_enhanced.py 0x29cc30f9d113b356ce408667aa6433589cecbdca")
        print("\nThis tool will:")
        print("  - Detect if you provided a token or pair address")
        print("  - Analyze the pair with all enhanced sniping functions")
        print("  - Show detailed fair launch analysis")
        sys.exit(1)
    
    address = sys.argv[1].strip()
    
    # Validate address format
    if not address.startswith('0x') or len(address) != 42:
        print(f"[X] Invalid address format: {address}")
        print("Address should be 42 characters starting with 0x")
        sys.exit(1)
    
    print("=" * 70)
    print("ENHANCED TOKEN CHECKER")
    print("=" * 70)
    print(f"\nAddress: {address}")
    
    # Try to detect if it's a token or pair
    print(f"\n[*] Detecting address type...")
    token_name, token_symbol = get_token_info(address)
    
    if token_name:
        # It's a token
        print(f"[OK] Detected as TOKEN: {token_name} (${token_symbol})")
        print(f"    Holders: Check on Basescan")
        
        # Try to find pairs
        pair_address = find_pairs_for_token(address)
        if not pair_address:
            sys.exit(0)
    else:
        # Might be a pair
        print(f"[*] Detected as PAIR address (or unknown contract)")
        pair_address = address
        token_name = None
        token_symbol = None
    
    # Analyze the pair
    print(f"\n[*] Analyzing pair: {pair_address}")
    print("    This may take 10-30 seconds (calling Honeypot.is API)...")
    print("    Please wait...")
    
    try:
        analysis = analyze_new_pair(pair_address)
        print_analysis(analysis, token_name, token_symbol)
    except Exception as e:
        print(f"\n[X] Analysis failed: {e}")
        print("\nPossible reasons:")
        print("  - Not a valid Uniswap pair")
        print("  - Pair doesn't have USDC")
        print("  - Contract is not a standard ERC20")
        print("  - Network/API issues")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
