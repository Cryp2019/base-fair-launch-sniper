import os
from web3 import Web3

# Load .env
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

key = os.getenv('ALCHEMY_BASE_KEY')
print(f"API Key loaded: {key[:10]}... (length: {len(key)})")

w3 = Web3(Web3.HTTPProvider(f'https://base-mainnet.g.alchemy.com/v2/{key}'))
block = w3.eth.block_number
print(f"✅ SUCCESS! Connected to Base - Block: {block}")
