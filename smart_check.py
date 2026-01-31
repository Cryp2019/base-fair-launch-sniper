#!/usr/bin/env python3
"""
Smart token/pair checker - Automatically finds pairs if given a token address
Usage: python smart_check.py <token_or_pair_address>
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
    w3,
    USDC_ADDRESS,
    WETH_ADDRESS,
    ERC20_ABI,
    FACTORY_ADDRESS
)

# Uniswap V3 Factory ABI (just the function we need)
FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def find_pairs_for_token(token_address):
    """Find Uniswap V3 pairs for a token"""
    print(f"\n[*] Searching for Uniswap V3 pairs...")
    
    factory = w3.eth.contract(address=FACTORY_ADDRESS, abi=FACTORY_ABI)
    
    # Common fee tiers in Uniswap V3
    fee_tiers = [500, 3000, 10000]  # 0.05%, 0.3%, 1%
    
    pairs_found = []
    
    # Check USDC pairs
    print(f"   Checking USDC pairs...")
    for fee in fee_tiers:
        try:
            pool = factory.functions.getPool(token_address, USDC_ADDRESS, fee).call()
            if pool != "0x0000000000000000000000000000000000000000":
                pairs_found.append({
                    'address': pool,
                    'type': 'USDC',
                    'fee': fee / 10000
                })
                print(f"   [OK] Found USDC pair ({fee/10000}% fee): {pool}")
        except Exception as e:
            continue
    
    # Check WETH pairs
    print(f"   Checking WETH pairs...")
    for fee in fee_tiers:
        try:
            pool = factory.functions.getPool(token_address, WETH_ADDRESS, fee).call()
            if pool != "0x0000000000000000000000000000000000000000":
                pairs_found.append({
                    'address': pool,
                    'type': 'WETH',
                    'fee': fee / 10000
                })
                print(f"   [OK] Found WETH pair ({fee/10000}% fee): {pool}")
        except Exception as e:
            continue
    
    return pairs_found

def get_token_info(address):
    """Get token name and symbol"""
    try:
        token = w3.eth.contract(address=address, abi=ERC20_ABI)
        name = token.functions.name().call()
        symbol = token.functions.symbol().call()
        return name, symbol
    except:
        return None, None

def print_analysis(analysis, token_name=None, token_symbol=None):
    """Pretty print analysis results"""
    if not analysis:
        print("\n[X] Analysis returned None - pair might not have enough data")
        return
    
    print("\n" + "=" * 70)
    print("FAIR LAUNCH ANALYSIS")
    print("=" * 70)
    
    name = token_name or analysis.get('name', 'Unknown')
    symbol = token_symbol or analysis.get('symbol', '???')
    
    print(f"\nToken: {name} (${symbol})")
    print(f"Token Address: {analysis['token_address']}")
    print(f"Pair Address: {analysis['pair_address']}")
    
    print(f"\n--- FAIR LAUNCH CHECKS ---")
    print(f"[{'OK' if analysis['renounced'] else 'X'}] Ownership Renounced: {analysis['renounced']}")
    print(f"[{'OK' if analysis['premine_ratio'] <= 5 else 'X'}] Pre-mine: {analysis['premine_ratio']:.2f}%")
    print(f"[{'OK' if analysis['liquidity_locked'] else 'X'}] LP Locked: {analysis['liquidity_locked']}")
    
    if analysis['liquidity_locked']:
        print(f"    Days: {analysis['lock_days']}")
        if analysis.get('lock_percent'):
            print(f"    Percent: {analysis['lock_percent']}%")
        if analysis.get('locker_name'):
            print(f"    Locker: {analysis['locker_name']}")
    
    print(f"[{'OK' if not analysis['is_honeypot'] else 'X'}] Honeypot: {'PASSED' if not analysis['is_honeypot'] else 'FAILED'}")
    if analysis['is_honeypot']:
        print(f"    Reason: {analysis.get('honeypot_reason')}")
    
    print(f"[{'OK' if analysis['buy_tax'] <= 5 else 'X'}] Buy Tax: {analysis['buy_tax']}%")
    print(f"[{'OK' if analysis['sell_tax'] <= 5 else 'X'}] Sell Tax: {analysis['sell_tax']}%")
    
    print(f"\n--- VERDICT ---")
    if analysis['is_fair']:
        print("[OK] FAIR LAUNCH - All checks passed!")
    else:
        print("[X] NOT A FAIR LAUNCH")
        print("\nFailed checks:")
        if not analysis['renounced']:
            print("  - Ownership not renounced")
        if analysis['premine_ratio'] > 5:
            print(f"  - Pre-mine too high ({analysis['premine_ratio']:.2f}%)")
        if not analysis['liquidity_locked']:
            print("  - Liquidity not locked")
        elif analysis['lock_days'] < 30:
            print(f"  - Lock too short ({analysis['lock_days']} days)")
        if analysis['is_honeypot']:
            print(f"  - Honeypot: {analysis.get('honeypot_reason')}")
        if analysis['buy_tax'] > 5 or analysis['sell_tax'] > 5:
            print(f"  - Tax too high")
    
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        print("Usage: python smart_check.py <token_or_pair_address>")
        print("\nExample:")
        print("  python smart_check.py 0x29cc30f9d113b356ce408667aa6433589cecbdca")
        print("\nThis tool automatically:")
        print("  - Detects if you provided a token or pair address")
        print("  - Finds Uniswap pairs if you gave a token address")
        print("  - Analyzes with all enhanced sniping functions")
        sys.exit(1)
    
    address = sys.argv[1].strip()
    
    if not address.startswith('0x') or len(address) != 42:
        print(f"[X] Invalid address: {address}")
        sys.exit(1)
    
    print("=" * 70)
    print("SMART TOKEN/PAIR CHECKER")
    print("=" * 70)
    print(f"\nAddress: {address}")
    
    # Try to detect if it's a token
    token_name, token_symbol = get_token_info(address)
    
    if token_name:
        # It's a token - find pairs
        print(f"\n[OK] Detected as TOKEN: {token_name} (${token_symbol})")
        
        pairs = find_pairs_for_token(address)
        
        if not pairs:
            print(f"\n[X] No Uniswap V3 pairs found for this token")
            print(f"\nPossible reasons:")
            print(f"  - Token doesn't have USDC or WETH pairs")
            print(f"  - Pairs exist on different DEX")
            print(f"  - Token is very new")
            sys.exit(0)
        
        print(f"\n[OK] Found {len(pairs)} pair(s)!")
        
        # Analyze the first (most liquid) pair
        pair_to_analyze = pairs[0]
        print(f"\n[*] Analyzing {pair_to_analyze['type']} pair ({pair_to_analyze['fee']}% fee)...")
        print(f"    This may take 10-30 seconds...")
        
        pair_address = pair_to_analyze['address']
    else:
        # Assume it's a pair address
        print(f"\n[*] Detected as PAIR address")
        pair_address = address
        token_name = None
        token_symbol = None
    
    # Analyze
    try:
        analysis = analyze_new_pair(pair_address)
        print_analysis(analysis, token_name, token_symbol)
    except Exception as e:
        print(f"\n[X] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
