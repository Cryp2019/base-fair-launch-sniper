import time
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

MONAD_RPCS = [
    'https://rpc.monad.xyz',
    'https://rpc-mainnet.monadinfra.com',
    'https://monad-mainnet.api.onfinality.io/public',
    'https://api-monad-mainnet-full.n.dwellir.com/d8d3c1c5-c22e-40f3-8407-50fa0e01eef9'
]

FACTORY_ADDRESS = '0x204faca1764b154221e35c0d20abb3c525710498'

def test_rpcs():
    logger.info("🧪 Testing Monad RPC endpoints...")
    
    for rpc in MONAD_RPCS:
        logger.info(f"\nTesting: {rpc}")
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 5}))
            start_time = time.time()
            
            if w3.is_connected():
                latency = (time.time() - start_time) * 1000
                chain_id = w3.eth.chain_id
                block = w3.eth.block_number
                
                logger.info(f"✅ CONNECTED! Latency: {latency:.2f}ms")
                logger.info(f"   Chain ID: {chain_id}")
                logger.info(f"   Block Height: {block}")
                
                # Try to get code from factory
                code = w3.eth.get_code(Web3.to_checksum_address(FACTORY_ADDRESS))
                if len(code) > 2:
                    logger.info("   ✅ Uniswap V3 Factory found at address")
                else:
                    logger.warning("   ⚠️  Factory address has NO CODE (might be wrong address for this chain)")
                    
            else:
                logger.error("❌ Failed to connect (is_connected=False)")
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_rpcs()
