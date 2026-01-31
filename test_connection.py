#!/usr/bin/env python3
"""
Quick test to verify Alchemy connection with updated key
"""
import os

# Load .env manually
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

print("=" * 60)
print("ALCHEMY API KEY TEST")
print("=" * 60)

alchemy_key = os.getenv('ALCHEMY_BASE_KEY')
print(f"\nAlchemy Key: {alchemy_key}")
print(f"Key Length: {len(alchemy_key) if alchemy_key else 0}")
print(f"Key Valid: {'✅ Yes' if alchemy_key and len(alchemy_key) > 20 else '❌ No'}")

if alchemy_key and len(alchemy_key) > 20:
    from web3 import Web3
    
    rpc_url = f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}"
    print(f"\nRPC URL: {rpc_url[:50]}...")
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        block = w3.eth.block_number
        print(f"\n✅ SUCCESS! Connected to Base chain")
        print(f"Current block: {block}")
        
        # Test getting recent blocks
        print(f"\nFetching last 5 blocks...")
        for i in range(5):
            block_num = block - i
            block_data = w3.eth.get_block(block_num)
            print(f"  Block {block_num}: {block_data['timestamp']} ({len(block_data['transactions'])} txs)")
        
        print("\n✅ All tests passed! Bot is ready to run.")
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
else:
    print("\n❌ Invalid or missing Alchemy key")
    print("Please check your .env file")
