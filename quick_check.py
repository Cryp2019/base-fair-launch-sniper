#!/usr/bin/env python3
"""
Quick contract checker - Just shows basic token info
Usage: python quick_check.py <token_address>
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

from web3 import Web3

BASE_RPC = f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_BASE_KEY')}"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
]

if len(sys.argv) < 2:
    print("Usage: python quick_check.py <token_address>")
    print("\nExample: python quick_check.py 0x29cc30f9d113b356ce408667aa6433589cecbdca")
    sys.exit(1)

address = sys.argv[1].strip()

print(f"\nChecking: {address}\n")

try:
    token = w3.eth.contract(address=address, abi=ERC20_ABI)
    
    name = token.functions.name().call()
    symbol = token.functions.symbol().call()
    total_supply = token.functions.totalSupply().call()
    decimals = token.functions.decimals().call()
    
    print(f"[OK] This is a TOKEN contract")
    print(f"\nToken: {name}")
    print(f"Symbol: ${symbol}")
    print(f"Decimals: {decimals}")
    print(f"Total Supply: {total_supply / (10**decimals):,.0f} {symbol}")
    
    print(f"\n" + "="*60)
    print("IMPORTANT: The bot needs the PAIR address, not token!")
    print("="*60)
    print(f"\nTo analyze this token:")
    print(f"1. Find the Uniswap pair on Basescan:")
    print(f"   https://basescan.org/token/{address}")
    print(f"\n2. Look for 'DEX Trades' or pool address")
    print(f"\n3. Then run:")
    print(f"   python check_token_enhanced.py <pair_address>")
    
except Exception as e:
    print(f"[X] Failed to read contract: {e}")
    print(f"\nThis might not be a standard ERC20 token")
