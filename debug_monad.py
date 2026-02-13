import os
import time
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
MONAD_RPC = os.getenv('MONAD_RPC_URL', 'https://rpc.monad.xyz')
FACTORY_ADDRESS = '0x204faca1764b154221e35c0d20abb3c525710498'  # Uniswap V3 Monad
EVENT_TOPIC = '0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118'  # PoolCreated

def debug_monad():
    logger.info(f"connecting to Monad RPC: {MONAD_RPC}")
    w3 = Web3(Web3.HTTPProvider(MONAD_RPC))
    
    if not w3.is_connected():
        logger.error("❌ Failed to connect to Monad RPC")
        return

    logger.info("✅ Connected to Monad RPC")
    
    try:
        current_block = w3.eth.block_number
        logger.info(f"🟣 Current Monad Block: {current_block}")
        
        # Scan last 1000 blocks for activity
        from_block = current_block - 1000
        logger.info(f"🔍 Scanning blocks {from_block} to {current_block} for PoolCreated events...")
        
        logs = w3.eth.get_logs({
            'fromBlock': hex(from_block),
            'toBlock': hex(current_block),
            'address': Web3.to_checksum_address(FACTORY_ADDRESS),
            'topics': [EVENT_TOPIC]
        })
        
        logger.info(f"✨ Found {len(logs)} events in last 1000 blocks")
        
        if len(logs) > 0:
            logger.info("✅ Factory is active! Recent event:")
            logger.info(logs[0])
        else:
            logger.warning("⚠️ No events found. Factory might be quiet or address incorrect.")
            
    except Exception as e:
        logger.error(f"❌ Error during scan: {e}")

if __name__ == "__main__":
    debug_monad()
