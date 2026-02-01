#!/usr/bin/env python3
"""
🚀 Base Fair Launch Sniper Bot - Complete Edition
Scans ALL new token launches on Base chain and sends beautiful alerts
"""
import os
import sys
import asyncio
import logging
import time
from datetime import datetime
from web3 import Web3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import UserDatabase
from trading import TradingBot
from security_scanner import SecurityScanner
from admin import AdminManager
from payment_monitor import PaymentMonitor

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'base_fair_launch_bot')
ALCHEMY_KEY = os.getenv('ALCHEMY_BASE_KEY')
BASE_RPC = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

# Base chain addresses
FACTORY_ADDRESS = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"  # Uniswap V3 Factory
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913".lower()
WETH_ADDRESS = "0x4200000000000000000000000000000000000006".lower()

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize
logger.info("🚀 Initializing Base Fair Launch Sniper Bot...")
db = UserDatabase()
logger.info(f"✅ Database connected: {db.db_path}")

w3 = Web3(Web3.HTTPProvider(BASE_RPC))
if w3.is_connected():
    logger.info(f"✅ Connected to Base RPC")
else:
    logger.error(f"❌ Failed to connect to Base RPC!")
    
trading_bot = TradingBot(w3)
security_scanner = SecurityScanner(w3)
admin_manager = AdminManager(db, w3)

# ABIs
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}
]

POOL_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"}
]

# ===== SCANNING FUNCTIONS =====

def get_new_pairs(last_block: int = None) -> list:
    """Scan for new Uniswap V3 pairs on Base"""
    if last_block is None:
        current_block = w3.eth.block_number
        last_block = current_block - 5  # Alchemy free tier: max 10 block range

    pool_created_topic = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"

    try:
        # Alchemy free tier limits eth_getLogs to 10 block range
        # So we scan from last_block to last_block + 10
        current_block = w3.eth.block_number
        to_block = min(last_block + 10, current_block)

        from_block_hex = hex(last_block)
        to_block_hex = hex(to_block)

        logs = w3.eth.get_logs({
            'fromBlock': from_block_hex,
            'toBlock': to_block_hex,
            'address': Web3.to_checksum_address(FACTORY_ADDRESS),
            'topics': [pool_created_topic]
        })

        pools = []
        for log in logs:
            try:
                if len(log['topics']) >= 4:
                    token0 = '0x' + log['topics'][1].hex()[-40:]
                    token1 = '0x' + log['topics'][2].hex()[-40:]
                    pool_address = '0x' + log['data'].hex()[-40:]

                    # Only track USDC or WETH pairs
                    if (token0.lower() == USDC_ADDRESS or token1.lower() == USDC_ADDRESS or
                        token0.lower() == WETH_ADDRESS or token1.lower() == WETH_ADDRESS):

                        pair_type = "USDC" if (token0.lower() == USDC_ADDRESS or token1.lower() == USDC_ADDRESS) else "WETH"

                        pools.append({
                            'address': pool_address,
                            'token0': token0,
                            'token1': token1,
                            'block': log['blockNumber'],
                            'pair_type': pair_type
                        })
                        logger.info(f"🔍 Found new {pair_type} pair: {pool_address}")
            except Exception as e:
                logger.warning(f"Failed to decode log: {e}")
                continue

        pools.sort(key=lambda x: x['block'], reverse=True)
        return pools

    except Exception as e:
        logger.error(f"Failed to fetch pairs: {e}")
        logger.debug(f"Last block: {last_block}, Factory: {FACTORY_ADDRESS}")
        return []

def analyze_token(pair_address: str, token0: str, token1: str, premium_analytics: bool = False) -> dict:
    """Analyze a new token launch"""
    try:
        # Identify the new token (not USDC/WETH)
        if token0.lower() == USDC_ADDRESS or token0.lower() == WETH_ADDRESS:
            new_token = token1
            base_token = "USDC" if token0.lower() == USDC_ADDRESS else "WETH"
            base_token_address = token0
        else:
            new_token = token0
            base_token = "USDC" if token1.lower() == USDC_ADDRESS else "WETH"
            base_token_address = token1

        # Get token info
        token_contract = w3.eth.contract(address=new_token, abi=ERC20_ABI)

        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            total_supply = token_contract.functions.totalSupply().call()
            decimals = token_contract.functions.decimals().call()
        except:
            return None  # Not a valid ERC20

        # Check ownership
        owner = "0x0"
        renounced = False
        try:
            owner = token_contract.functions.owner().call()
            burn_addresses = ["0x0000000000000000000000000000000000000000",
                            "0x0000000000000000000000000000000000000001",
                            "0x000000000000000000000000000000000000dEaD"]
            renounced = owner.lower() in [a.lower() for a in burn_addresses]
        except:
            renounced = True  # No owner function = likely renounced

        result = {
            'token_address': new_token,
            'pair_address': pair_address,
            'name': name,
            'symbol': symbol,
            'total_supply': total_supply,
            'decimals': decimals,
            'base_token': base_token,
            'renounced': renounced,
            'owner': owner,
            'timestamp': datetime.utcnow().isoformat()
        }

        # PREMIUM ANALYTICS - Only for premium users
        if premium_analytics:
            try:
                # Get liquidity in the pool
                base_contract = w3.eth.contract(address=base_token_address, abi=ERC20_ABI)
                liquidity_balance = base_contract.functions.balanceOf(pair_address).call()
                base_decimals = base_contract.functions.decimals().call()
                liquidity_formatted = liquidity_balance / (10 ** base_decimals)

                # Get holder count (approximate by checking top holders)
                # This is a simplified version - real implementation would use an indexer
                result['premium'] = {
                    'liquidity': liquidity_formatted,
                    'liquidity_token': base_token,
                    'initial_liquidity': f"{liquidity_formatted:.2f} {base_token}"
                }
            except Exception as e:
                logger.warning(f"Premium analytics failed: {e}")
                result['premium'] = None

        return result

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None

# ===== ENHANCED METRICS FUNCTIONS =====

async def get_dexscreener_data(token_address: str) -> dict:
    """Fetch volume, price, and market cap data from DexScreener API"""
    try:
        # Use the /tokens/ endpoint which accepts token contract addresses
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            # The /tokens/ endpoint returns an array of pairs
            pairs = data.get('pairs', [])
            
            if pairs and len(pairs) > 0:
                # Get the first pair (usually the most liquid one)
                # Or find the pair with highest liquidity
                pair = max(pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0)) if p.get('liquidity') else 0)
                
                logger.info(f"DexScreener found pair: {pair.get('pairAddress', 'unknown')} with ${float(pair.get('liquidity', {}).get('usd', 0)):,.2f} liquidity")
                
                return {
                    'price_usd': float(pair.get('priceUsd', 0)),
                    'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                    'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                    'market_cap': float(pair.get('fdv', 0)),  # Fully diluted valuation
                    'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                    'ath': float(pair.get('ath', 0)) if pair.get('ath') else None
                }
            else:
                logger.warning(f"DexScreener: No pairs found for token {token_address}")
    except Exception as e:
        logger.warning(f"DexScreener API failed: {e}")
    
    return {
        'price_usd': 0,
        'volume_24h': 0,
        'liquidity_usd': 0,
        'market_cap': 0,
        'price_change_24h': 0,
        'ath': None
    }

async def calculate_pool_price(pair_address: str, token_address: str, base_token_address: str) -> float:
    """Calculate token price from pool reserves (fallback if DexScreener fails)"""
    try:
        # Get pool reserves
        pool_abi = [
            {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
            {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
        ]
        
        pool_contract = w3.eth.contract(address=pair_address, abi=pool_abi)
        token0 = pool_contract.functions.token0().call().lower()
        token1 = pool_contract.functions.token1().call().lower()
        
        # Get balances
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        base_contract = w3.eth.contract(address=base_token_address, abi=ERC20_ABI)
        
        token_balance = token_contract.functions.balanceOf(pair_address).call()
        base_balance = base_contract.functions.balanceOf(pair_address).call()
        
        token_decimals = token_contract.functions.decimals().call()
        base_decimals = base_contract.functions.decimals().call()
        
        # Calculate price
        if token_balance > 0:
            price = (base_balance / (10 ** base_decimals)) / (token_balance / (10 ** token_decimals))
            return price
    except Exception as e:
        logger.warning(f"Pool price calculation failed: {e}")
    
    return 0

async def check_transfer_limits(token_address: str) -> dict:
    """Check if token has transfer amount limits"""
    try:
        # Check for common limit functions
        limit_abi = [
            {"constant":True,"inputs":[],"name":"_maxTxAmount","outputs":[{"name":"","type":"uint256"}],"type":"function"},
            {"constant":True,"inputs":[],"name":"maxTransactionAmount","outputs":[{"name":"","type":"uint256"}],"type":"function"},
            {"constant":True,"inputs":[],"name":"_maxWalletSize","outputs":[{"name":"","type":"uint256"}],"type":"function"},
        ]
        
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI + limit_abi)
        
        # Try to get total supply for percentage calculation
        total_supply = contract.functions.totalSupply().call()
        
        has_limits = False
        limit_details = []
        
        # Check max transaction amount
        try:
            max_tx = contract.functions._maxTxAmount().call()
            if max_tx > 0 and max_tx < total_supply:
                has_limits = True
                limit_pct = (max_tx / total_supply) * 100
                limit_details.append(f"Max TX: {limit_pct:.2f}%")
        except:
            try:
                max_tx = contract.functions.maxTransactionAmount().call()
                if max_tx > 0 and max_tx < total_supply:
                    has_limits = True
                    limit_pct = (max_tx / total_supply) * 100
                    limit_details.append(f"Max TX: {limit_pct:.2f}%")
            except:
                pass
        
        # Check max wallet size
        try:
            max_wallet = contract.functions._maxWalletSize().call()
            if max_wallet > 0 and max_wallet < total_supply:
                has_limits = True
                limit_pct = (max_wallet / total_supply) * 100
                limit_details.append(f"Max Wallet: {limit_pct:.2f}%")
        except:
            pass
        
        return {
            'has_limits': has_limits,
            'details': ', '.join(limit_details) if limit_details else 'No limits'
        }
    except Exception as e:
        logger.debug(f"Transfer limit check failed: {e}")
    
    return {'has_limits': False, 'details': 'No limits'}

async def calculate_clog_percentage(token_address: str, pair_address: str) -> float:
    """Calculate network clog percentage based on recent transactions"""
    try:
        # Get recent transactions for the pair
        url = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "fromBlock": "latest",
                "toBlock": "latest",
                "contractAddresses": [token_address],
                "category": ["erc20"],
                "maxCount": "0x5",
                "withMetadata": True
            }]
        }
        
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            transfers = data.get('result', {}).get('transfers', [])
            
            if transfers:
                # Calculate average gas used
                total_gas = 0
                count = 0
                for tx in transfers:
                    if tx.get('metadata', {}).get('gasUsed'):
                        total_gas += int(tx['metadata']['gasUsed'], 16)
                        count += 1
                
                if count > 0:
                    avg_gas = total_gas / count
                    # Clog percentage: (avg_gas / 300000) * 100
                    # 300000 is typical max gas for a swap
                    clog_pct = min((avg_gas / 300000) * 100, 100)
                    return round(clog_pct, 2)
    except Exception as e:
        logger.debug(f"Clog calculation failed: {e}")
    
    return 0.03  # Default minimal clog

async def detect_airdrops(token_address: str) -> list:
    """Detect if token has airdrop functionality or recent batch transfers"""
    airdrops = []
    
    try:
        # Check for airdrop-related functions
        airdrop_abi = [
            {"constant":False,"inputs":[{"name":"recipients","type":"address[]"},{"name":"amounts","type":"uint256[]"}],"name":"airdrop","outputs":[],"type":"function"},
            {"constant":False,"inputs":[{"name":"recipients","type":"address[]"},{"name":"amount","type":"uint256"}],"name":"multiTransfer","outputs":[],"type":"function"},
        ]
        
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI + airdrop_abi)
        
        # Check if airdrop function exists
        if hasattr(contract.functions, 'airdrop'):
            airdrops.append("Airdrop function detected")
        
        if hasattr(contract.functions, 'multiTransfer'):
            airdrops.append("Multi-transfer function detected")
        
        # Check recent transactions for batch transfers
        url = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "fromBlock": "latest",
                "toBlock": "latest",
                "contractAddresses": [token_address],
                "category": ["erc20"],
                "maxCount": "0xa",
                "withMetadata": True
            }]
        }
        
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            transfers = data.get('result', {}).get('transfers', [])
            
            # Group by transaction hash
            tx_groups = {}
            for transfer in transfers:
                tx_hash = transfer.get('hash')
                if tx_hash:
                    if tx_hash not in tx_groups:
                        tx_groups[tx_hash] = 0
                    tx_groups[tx_hash] += 1
            
            # If any transaction has 5+ transfers, it's likely an airdrop
            for tx_hash, count in tx_groups.items():
                if count >= 5:
                    airdrops.append(f"Batch transfer detected ({count} recipients)")
                    break
    
    except Exception as e:
        logger.debug(f"Airdrop detection failed: {e}")
    
    return airdrops

async def get_comprehensive_metrics(token_address: str, pair_address: str, base_token_address: str, 
                                   total_supply: int, decimals: int, premium: bool = False) -> dict:
    """Get all comprehensive metrics for a token"""
    metrics = {
        'price_usd': 0,
        'market_cap': 0,
        'liquidity_usd': 0,
        'volume_24h': 0,
        'ath': None,
        'has_limits': False,
        'limit_details': 'No limits',
        'clog_percentage': 0.03,
        'airdrops': []
    }
    
    try:
        # Get DexScreener data (price, volume, liquidity, MC)
        dex_data = await get_dexscreener_data(pair_address)
        metrics.update(dex_data)
        
        # If DexScreener didn't return price, calculate from pool
        if metrics['price_usd'] == 0:
            pool_price = await calculate_pool_price(pair_address, token_address, base_token_address)
            metrics['price_usd'] = pool_price
            
            # Calculate market cap manually if we have price
            if pool_price > 0:
                supply_formatted = total_supply / (10 ** decimals)
                metrics['market_cap'] = pool_price * supply_formatted
        
        # Get transfer limits
        limits = await check_transfer_limits(token_address)
        metrics['has_limits'] = limits['has_limits']
        metrics['limit_details'] = limits['details']
        
        # Get clog percentage
        metrics['clog_percentage'] = await calculate_clog_percentage(token_address, pair_address)
        
        # Detect airdrops
        metrics['airdrops'] = await detect_airdrops(token_address)
        
    except Exception as e:
        logger.error(f"Error getting comprehensive metrics: {e}")
    
    return metrics

# ===== ALERT FUNCTIONS =====

async def send_launch_alert(app: Application, analysis: dict):
    """Send beautiful alert for new token launch - with premium features"""

    # Get all users with alerts enabled
    users = db.get_users_with_alerts()

    # Separate premium and free users for priority delivery
    premium_users = []
    free_users = []

    for user in users:
        user_data = db.get_user(user['user_id'])
        if user_data and user_data['tier'] == 'premium':
            premium_users.append(user)
        else:
            free_users.append(user)

    # Fetch comprehensive metrics
    try:
        metrics = await get_comprehensive_metrics(
            analysis['token_address'],
            analysis['pair_address'],
            USDC_ADDRESS if analysis['base_token'] == 'USDC' else WETH_ADDRESS,
            analysis['total_supply'],
            analysis['decimals'],
            premium=True
        )
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        metrics = {
            'price_usd': 0,
            'market_cap': 0,
            'liquidity_usd': 0,
            'volume_24h': 0,
            'ath': None,
            'has_limits': False,
            'limit_details': 'No limits',
            'clog_percentage': 0.03,
            'airdrops': []
        }

    # Format numbers
    def format_number(num):
        if num >= 1_000_000:
            return f"${num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num/1_000:.2f}K"
        else:
            return f"${num:.2f}"

    mc_str = format_number(metrics['market_cap']) if metrics['market_cap'] > 0 else "N/A"
    ath_str = format_number(metrics['ath']) if metrics.get('ath') else "N/A"
    liq_str = format_number(metrics['liquidity_usd']) if metrics['liquidity_usd'] > 0 else "N/A"
    price_str = f"${metrics['price_usd']:.8f}" if metrics['price_usd'] > 0 else "N/A"
    vol_str = format_number(metrics['volume_24h']) if metrics['volume_24h'] > 0 else "N/A"

    # Get tax info from analysis
    buy_tax = analysis.get('buy_tax', 0)
    sell_tax = analysis.get('sell_tax', 0)
    transfer_tax = analysis.get('transfer_tax', 0)
    total_tax = buy_tax + sell_tax + transfer_tax

    # Safety check emoji
    status_emoji = "✅" if analysis['renounced'] else "⚠️"

    # Airdrop info
    airdrop_str = ", ".join(metrics['airdrops']) if metrics['airdrops'] else "None detected"

    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton("🔍 View Token", url=f"https://basescan.org/token/{analysis['token_address']}"),
            InlineKeyboardButton("💧 View Pair", url=f"https://basescan.org/address/{analysis['pair_address']}")
        ],
        [
            InlineKeyboardButton("📊 DexScreener", url=f"https://dexscreener.com/base/{analysis['pair_address']}"),
            InlineKeyboardButton("🦄 Uniswap", url=f"https://app.uniswap.org/#/tokens/base/{analysis['token_address']}")
        ]
    ]

    sent_count = 0

    # PRIORITY ALERTS: Send to premium users FIRST (5-10 seconds faster)
    for user in premium_users:
        try:
            message = (
                f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃                                                    ┃\n"
                f"┃    🚀 *NEW LAUNCH* 💎       ┃\n"
                f"┃                                                    ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"*PREMIUM ALERT - Priority Delivery*\n\n"
                f"┌─────────────────────┐\n"
                f"│  💎 *TOKEN INFO*     │\n"
                f"└─────────────────────┘\n\n"
                f"Name: *{analysis['name']}*\n"
                f"Symbol: *${analysis['symbol'].upper()}*\n"
                f"Pair: *{analysis['base_token']}*\n\n"
                f"🧢 MC: {mc_str}     | ATH: {ath_str}\n"
                f"💧 Liq: {liq_str}\n"
                f"🏷 Price: {price_str}\n"
                f"🎚 Vol: {vol_str}\n\n"
                f"┌─────────────────────┐\n"
                f"│  🛡️ *SAFETY CHECKS*  │\n"
                f"└─────────────────────┘\n\n"
                f"{status_emoji} Ownership: *{'Renounced ✅' if analysis['renounced'] else 'NOT Renounced ⚠️'}*\n"
                f"{'✅' if not analysis.get('is_honeypot') else '🚨'} Honeypot: *{'SAFE' if not analysis.get('is_honeypot') else 'DETECTED ⚠️'}*\n"
                f"{'✅' if analysis.get('liquidity_locked') else '❌'} LP Locked: *{'YES' if analysis.get('liquidity_locked') else 'NO'}*"
            )
            
            if analysis.get('liquidity_locked'):
                message += f"\n   └ {analysis.get('lock_days', 0)} days via {analysis.get('locker_name', 'Unknown')}"
            
            message += (
                f"\n\n🏧 B: {buy_tax:.2f}% | S: {sell_tax:.2f}% | T: {total_tax:.2f}%\n"
                f"⚖️ {metrics['limit_details']}\n"
                f"🪠 Clog: {metrics['clog_percentage']:.2f}%\n\n"
                f"🪂 Airdrops: {airdrop_str}\n\n"
                f"┌─────────────────────┐\n"
                f"│  📍 *CONTRACT*       │\n"
                f"└─────────────────────┘\n\n"
                f"`{analysis['token_address']}`\n\n"
                f"⚠️ *DYOR! Not financial advice.*"
            )

            await app.bot.send_message(
                chat_id=user['user_id'],
                text=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            sent_count += 1
            await asyncio.sleep(0.03)  # Faster for premium
        except Exception as e:
            logger.warning(f"Failed to send to premium user {user['user_id']}: {e}")

    # Standard message for free users
    free_message = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      🚀 *NEW LAUNCH*          ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  💎 *TOKEN INFO*     │\n"
        f"└─────────────────────┘\n\n"
        f"Name: *{analysis['name']}*\n"
        f"Symbol: *${analysis['symbol'].upper()}*\n"
        f"Pair: *{analysis['base_token']}*\n\n"
        f"🧢 MC: {mc_str}\n"
        f"💧 Liq: {liq_str}\n"
        f"🏷 Price: {price_str}\n"
        f"🎚 Vol: {vol_str}\n\n"
        f"┌─────────────────────┐\n"
        f"│  🛡️ *SAFETY CHECKS*  │\n"
        f"└─────────────────────┘\n\n"
        f"{status_emoji} Ownership: *{'Renounced ✅' if analysis['renounced'] else 'NOT Renounced ⚠️'}*\n"
        f"{'✅' if not analysis.get('is_honeypot') else '🚨'} Honeypot: *{'SAFE' if not analysis.get('is_honeypot') else 'DETECTED ⚠️'}*\n"
        f"{'✅' if analysis.get('liquidity_locked') else '❌'} LP Locked: *{'YES' if analysis.get('liquidity_locked') else 'NO'}*\n\n"
        f"🏧 B: {buy_tax:.2f}% | S: {sell_tax:.2f}% | T: {total_tax:.2f}%\n"
        f"⚖️ {metrics['limit_details']}\n"
        f"🪠 Clog: {metrics['clog_percentage']:.2f}%\n\n"
        f"┌─────────────────────┐\n"
        f"│  📍 *CONTRACT*       │\n"
        f"└─────────────────────┘\n\n"
        f"`{analysis['token_address']}`\n\n"
        f"💡 *Upgrade for ATH tracking & airdrops!*\n\n"
        f"⚠️ *DYOR! Not financial advice.*"
    )

    # Send to free users (after premium users get priority)
    for user in free_users:
        try:
            await app.bot.send_message(
                chat_id=user['user_id'],
                text=free_message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            sent_count += 1
            await asyncio.sleep(0.05)  # Standard rate limiting
        except Exception as e:
            logger.warning(f"Failed to send to user {user['user_id']}: {e}")

    logger.info(f"📢 Alert sent to {sent_count} users ({len(premium_users)} premium, {len(free_users)} free) for ${analysis['symbol']}")

# ===== BOT UI FUNCTIONS =====

def create_main_menu():
    """Create main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Snipe Token", callback_data="snipe"),
            InlineKeyboardButton("🔍 Check Token", callback_data="checktoken")
        ],
        [
            InlineKeyboardButton("👛 My Wallets", callback_data="wallets"),
            InlineKeyboardButton("📊 My Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("🎁 Referrals", callback_data="refer"),
            InlineKeyboardButton("🔔 Alerts", callback_data="alerts")
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
            InlineKeyboardButton("💎 Upgrade", callback_data="upgrade")
        ],
        [
            InlineKeyboardButton("ℹ️ How It Works", callback_data="howitworks")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_back_button():
    """Create back button"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])

# ===== COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user = update.effective_user
    args = context.args

    referrer_code = args[0] if args else None

    result = db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referrer_code=referrer_code
    )

    # Auto-upgrade @cccryp to permanent premium
    if user.username and user.username.lower() == 'cccryp':
        db.update_tier(user.id, 'premium')
        logger.info(f"✅ Auto-upgraded @cccryp to premium")

    # Check if referrer should be upgraded to premium (10+ referrals)
    if result['success'] and result.get('referred_by'):
        referrer_id = result['referred_by']
        if db.check_and_upgrade_premium(referrer_id):
            # Notify referrer they got premium
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        "🎉 *CONGRATULATIONS!*\n\n"
                        "You've reached 10 referrals!\n"
                        "You've been upgraded to *PREMIUM* for 1 month! 💎\n\n"
                        "Premium features unlocked:\n"
                        "• Advanced analytics\n"
                        "• Custom filters\n"
                        "• Priority alerts\n\n"
                        "Thank you for spreading the word! 🚀"
                    ),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Failed to notify referrer {referrer_id}: {e}")

    total_users = db.get_total_users()

    # Check if user is premium
    user_data = db.get_user(user.id)
    is_premium = user_data and user_data['tier'] == 'premium'

    # Premium badge for premium users
    premium_badge = " 💎" if is_premium else ""

    welcome_msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃        🚀 *BASE SNIPER*{premium_badge}        ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"*Welcome, {user.first_name}!* 👋\n\n"
        f"Your 24/7 Base chain token scanner.\n"
        f"Never miss a launch again.\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⚡ *WHAT I DO*           │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Scan Base every 10 seconds\n"
        f"▸ Alert ALL new token launches\n"
        f"▸ Check ownership & safety\n"
        f"▸ Analyze any token on demand\n\n"
        f"┌─────────────────────┐\n"
        f"│  📊 *NETWORK STATS*  │\n"
        f"└─────────────────────┘\n\n"
        f"👥 Active Users: *{total_users:,}*\n"
        f"🔔 Your Alerts: *{'ON' if user_data and user_data['alerts_enabled'] else 'OFF'}*\n"
    )

    if is_premium:
        welcome_msg += f"💎 Status: *PREMIUM*\n"

    welcome_msg += "\n"

    if result.get('referred_by'):
        welcome_msg += f"✨ *Referred by User {result['referred_by']}*\n\n"

    welcome_msg += (
        f"┌─────────────────────┐\n"
        f"│  ⚠️  *DISCLAIMER*        │\n"
        f"└─────────────────────┘\n\n"
        f"Not financial advice.\n"
        f"Most new tokens fail.\n"
        f"Always DYOR!\n\n"
        f"👇 Choose an option:"
    )

    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_data = db.get_user(user.id)
    is_premium = user_data and user_data['tier'] == 'premium'
    premium_badge = " 💎" if is_premium else ""

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃        📱 *MENU*{premium_badge}                ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"*What would you like to do?*\n\n"
        f"👇 Choose an option below:"
    )

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_main_menu())

async def howitworks_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain how it works"""
    query = update.callback_query
    await query.answer()

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃     🔍 *HOW IT WORKS*          ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⚡ *AUTO SCANNING*  │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Monitors Uniswap V3 on Base\n"
        f"▸ Scans every 10 seconds\n"
        f"▸ Detects ALL new token pairs\n"
        f"▸ Sends instant alerts\n\n"
        f"┌─────────────────────┐\n"
        f"│  🔍 *MANUAL CHECK*   │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Paste any token address\n"
        f"▸ Get instant analysis\n"
        f"▸ Check ownership status\n"
        f"▸ View safety metrics\n\n"
        f"┌─────────────────────┐\n"
        f"│  🛡️ *SAFETY FIRST*   │\n"
        f"└─────────────────────┘\n\n"
        f"✓ Ownership verification\n"
        f"✓ Direct Basescan links\n"
        f"✓ DexScreener charts\n"
        f"✓ Uniswap trading links\n\n"
        f"⚠️ *Always DYOR!*\n"
        f"Most new tokens fail."
    )

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_back_button())

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user stats"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_stats = db.get_user_stats(user.id)

    if not user_stats:
        await query.edit_message_text("❌ User not found. Use /start first!", reply_markup=create_back_button())
        return

    user_data = user_stats['user']
    is_premium = user_data['tier'] == 'premium'
    premium_badge = " 💎" if is_premium else ""

    # Get active and pending referrals
    active_refs = user_stats.get('total_referrals', 0)
    pending_refs = user_stats.get('pending_referrals', 0)

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      📊 *YOUR STATS*{premium_badge}       ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  👤 *PROFILE*        │\n"
        f"└─────────────────────┘\n\n"
        f"Name: *{user_data['first_name']}*\n"
        f"Joined: *{user_data['joined_date'][:10]}*\n"
        f"Status: *{user_data['tier'].upper()}*{premium_badge}\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⚙️ *SETTINGS*       │\n"
        f"└─────────────────────┘\n\n"
        f"Alerts: *{'✅ ON' if user_data['alerts_enabled'] else '❌ OFF'}*\n"
        f"Active Referrals: *{active_refs}* (traded)\n"
        f"Pending Referrals: *{pending_refs}* (not traded yet)\n"
    )

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_back_button())

async def refer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral link"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_data = db.get_user(user.id)

    if not user_data:
        await query.edit_message_text("❌ User not found!", reply_markup=create_back_button())
        return

    referral_code = user_data['referral_code']
    referral_link = f"https://t.me/{BOT_USERNAME}?start={referral_code}"

    # Calculate progress to premium
    total_refs = user_data['total_referrals']
    refs_needed = max(0, 10 - total_refs)
    progress_bar = "█" * min(total_refs, 10) + "░" * refs_needed

    # Check if user already has premium
    is_premium = user_data['tier'] == 'premium'

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃     🎁 *REFERRAL LINK*       ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  🔗 *YOUR LINK*      │\n"
        f"└─────────────────────┘\n\n"
        f"`{referral_link}`\n\n"
        f"┌─────────────────────┐\n"
        f"│  📊 *PROGRESS*       │\n"
        f"└─────────────────────┘\n\n"
    )

    if is_premium:
        msg += f"✅ *Status: PREMIUM* 💎\n"
        msg += f"Referrals: *{total_refs}*\n\n"
    elif total_refs >= 10:
        msg += f"🎉 *You qualify for premium!*\n"
        msg += f"Referrals: *{total_refs}/10* ✅\n\n"
    else:
        msg += f"Referrals: *{total_refs}/10*\n"
        msg += f"{progress_bar}\n"
        msg += f"*{refs_needed} more* for FREE premium!\n\n"

    msg += (
        f"┌─────────────────────┐\n"
        f"│  🎁 *REWARDS*        │\n"
        f"└─────────────────────┘\n\n"
        f"▸ 10 referrals = 1 month FREE premium\n"
        f"▸ Premium features unlocked\n"
        f"▸ Priority alerts & analytics\n\n"
        f"💡 *Share your link to earn!*"
    )

    keyboard = [
        [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={referral_link}&text=🚀 Get instant alerts for new Base token launches!")],
        [InlineKeyboardButton("« Back", callback_data="menu")]
    ]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard"""
    query = update.callback_query
    await query.answer()

    leaders = db.get_leaderboard(limit=10)
    total_users = db.get_total_users()

    leaderboard_text = ""
    medals = ['🥇', '🥈', '🥉']

    for i, leader in enumerate(leaders, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = leader['first_name'] or f"User {leader['user_id']}"
        leaderboard_text += f"{medal} *{name}* - {leader['total_referrals']}\n"

    if not leaders:
        leaderboard_text = "No referrals yet!"

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      🏆 *LEADERBOARD*        ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  📊 *TOP REFERRERS*  │\n"
        f"└─────────────────────┘\n\n"
        f"{leaderboard_text}\n\n"
        f"┌─────────────────────┐\n"
        f"│  👥 *COMMUNITY*      │\n"
        f"└─────────────────────┘\n\n"
        f"Total Users: *{total_users:,}*"
    )

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_back_button())

async def alerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle alerts"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    new_state = db.toggle_alerts(user.id)

    status_emoji = "✅" if new_state else "❌"
    status_text = "ON" if new_state else "OFF"

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃       🔔 *ALERTS*              ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⚙️ *STATUS*         │\n"
        f"└─────────────────────┘\n\n"
        f"Alerts: {status_emoji} *{status_text}*\n\n"
    )

    if new_state:
        msg += (
            f"┌─────────────────────┐\n"
            f"│  ✅ *ENABLED*        │\n"
            f"└─────────────────────┘\n\n"
            f"▸ You'll receive instant alerts\n"
            f"▸ For ALL new token launches\n"
            f"▸ On Base chain via Uniswap V3"
        )
    else:
        msg += (
            f"┌─────────────────────┐\n"
            f"│  ❌ *DISABLED*       │\n"
            f"└─────────────────────┘\n\n"
            f"▸ You won't receive alerts\n"
            f"▸ Enable anytime from menu\n"
            f"▸ Manual token checks still work"
        )

    keyboard = [
        [InlineKeyboardButton(f"{'🔕 Disable' if new_state else '🔔 Enable'}", callback_data="alerts")],
        [InlineKeyboardButton("« Back", callback_data="menu")]
    ]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upgrade info with payment instructions"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_data = db.get_user(user.id)

    current_tier = user_data['tier'] if user_data else 'free'

    # If already premium, show confirmation
    if current_tier == 'premium':
        msg = (
            f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃                                                    ┃\n"
            f"┃    ✅ *YOU HAVE PREMIUM!* 💎   ┃\n"
            f"┃                                                    ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"┌─────────────────────┐\n"
            f"│  💎 *YOUR BENEFITS*  │\n"
            f"└─────────────────────┘\n\n"
            f"✓ Priority alerts (5-10s faster)\n"
            f"✓ ATH (All-Time High) tracking\n"
            f"✓ Airdrop detection\n"
            f"✓ Comprehensive metrics (MC, Liq, Price, Vol)\n"
            f"✓ Enhanced safety checks (Honeypot, LP Lock)\n"
            f"✓ Tax percentages & transfer limits\n"
            f"✓ Premium badge 💎\n\n"
            f"Thank you for being premium! 🚀"
        )
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_back_button())
        return

    # Get payment wallet from environment
    payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS', 'Not configured')

    # Calculate progress
    total_refs = user_data['total_referrals']
    refs_needed = max(0, 10 - total_refs)
    progress_bar = "█" * min(total_refs, 10) + "░" * refs_needed

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃   💎 *UPGRADE TO PREMIUM*    ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⭐ *FEATURES*       │\n"
        f"└─────────────────────┘\n\n"
        f"✓ Priority alerts (5-10s faster)\n"
        f"✓ ATH (All-Time High) tracking\n"
        f"✓ Airdrop detection\n"
        f"✓ Comprehensive metrics (MC, Liq, Price, Vol)\n"
        f"✓ Enhanced safety checks (Honeypot, LP Lock)\n"
        f"✓ Tax percentages & transfer limits\n"
        f"✓ Premium badge 💎\n\n"
        f"┌─────────────────────┐\n"
        f"│  💰 *OPTION 1: PAY*  │\n"
        f"└─────────────────────┘\n\n"
        f"Price: *$4/month*\n\n"
        f"Send *4 USDC* on Base to:\n"
        f"`{payment_wallet}`\n\n"
        f"Then DM me your TX hash!\n\n"
        f"┌─────────────────────┐\n"
        f"│  🎁 *OPTION 2: FREE* │\n"
        f"└─────────────────────┘\n\n"
        f"Refer 10 users = 1 month FREE!\n\n"
        f"Progress: *{total_refs}/10*\n"
        f"{progress_bar}\n"
        f"*{refs_needed} more* to unlock!\n\n"
        f"💡 Get your referral link below!"
    )

    keyboard = [
        [InlineKeyboardButton("🎁 My Referral Link", callback_data="refer")],
        [InlineKeyboardButton("« Back", callback_data="menu")]
    ]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def wallets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's wallets and wallet management options"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    wallets = db.get_user_wallets(user.id)

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      👛 *MY WALLETS*          ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    )

    if wallets:
        msg += (
            f"┌─────────────────────┐\n"
            f"│  💼 *YOUR WALLETS*   │\n"
            f"└─────────────────────┘\n\n"
        )

        for i, wallet in enumerate(wallets, 1):
            created = wallet['created_date'][:10]
            msg += f"{i}. `{wallet['wallet_address']}`\n"
            msg += f"   Created: {created}\n\n"

        msg += (
            f"┌─────────────────────┐\n"
            f"│  ⚠️ *SECURITY*       │\n"
            f"└─────────────────────┘\n\n"
            f"▸ Keep private keys safe\n"
            f"▸ Never share with anyone\n"
            f"▸ Bot stores encrypted keys\n\n"
            f"💡 Use wallets to receive snipe profits!"
        )
    else:
        msg += (
            f"┌─────────────────────┐\n"
            f"│  📝 *NO WALLETS*     │\n"
            f"└─────────────────────┘\n\n"
            f"You haven't created any wallets yet.\n\n"
            f"┌─────────────────────┐\n"
            f"│  💡 *WHY CREATE?*    │\n"
            f"└─────────────────────┘\n\n"
            f"▸ Receive snipe profits\n"
            f"▸ Auto-buy new tokens\n"
            f"▸ Manage funds easily\n\n"
            f"Click below to create your first wallet!"
        )

    keyboard = [
        [InlineKeyboardButton("➕ Create New Wallet", callback_data="create_wallet")],
    ]

    if wallets:
        keyboard.append([InlineKeyboardButton("🔑 Export Private Key", callback_data="export_key")])

    keyboard.append([InlineKeyboardButton("« Back", callback_data="menu")])

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def create_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new wallet for the user"""
    query = update.callback_query
    await query.answer()

    user = query.from_user

    # Show creating message
    await query.edit_message_text(
        "⏳ *Creating your wallet...*\n\nPlease wait...",
        parse_mode='Markdown'
    )

    try:
        # Import eth_account for wallet creation
        from eth_account import Account
        import secrets

        # Generate new wallet
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        wallet_address = account.address

        # Save to database
        result = db.create_wallet(user.id, wallet_address, private_key)

        if result['success']:
            msg = (
                f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                f"┃                                                    ┃\n"
                f"┃    ✅ *WALLET CREATED!*      ┃\n"
                f"┃                                                    ┃\n"
                f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                f"┌─────────────────────┐\n"
                f"│  💼 *YOUR WALLET*    │\n"
                f"└─────────────────────┘\n\n"
                f"Address:\n"
                f"`{wallet_address}`\n\n"
                f"┌─────────────────────┐\n"
                f"│  🔑 *PRIVATE KEY*    │\n"
                f"└─────────────────────┘\n\n"
                f"⚠️ *SAVE THIS SECURELY!*\n\n"
                f"`{private_key}`\n\n"
                f"┌─────────────────────┐\n"
                f"│  ⚠️ *IMPORTANT*      │\n"
                f"└─────────────────────┘\n\n"
                f"▸ Never share your private key\n"
                f"▸ Store it in a safe place\n"
                f"▸ You can export it later\n"
                f"▸ Fund this wallet to start sniping\n\n"
                f"💡 Send ETH/Base tokens to this address!"
            )

            keyboard = [
                [InlineKeyboardButton("👛 My Wallets", callback_data="wallets")],
                [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
            ]

            await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text(
                f"❌ *Error creating wallet*\n\n{result['message']}\n\nTry again later.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="wallets")]])
            )

    except Exception as e:
        logger.error(f"Wallet creation error: {e}")
        await query.edit_message_text(
            f"❌ *Error creating wallet*\n\n`{str(e)}`\n\nTry again later.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="wallets")]])
        )

async def export_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export private key for user's wallet"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    wallets = db.get_user_wallets(user.id)

    if not wallets:
        await query.edit_message_text(
            "❌ No wallets found!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="wallets")]])
        )
        return

    # For now, show the first wallet's key
    # In production, you'd want to let user select which wallet
    wallet_address = wallets[0]['wallet_address']
    private_key = db.get_wallet_private_key(user.id, wallet_address)

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      🔑 *PRIVATE KEY*        ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  💼 *WALLET*         │\n"
        f"└─────────────────────┘\n\n"
        f"`{wallet_address}`\n\n"
        f"┌─────────────────────┐\n"
        f"│  🔑 *PRIVATE KEY*    │\n"
        f"└─────────────────────┘\n\n"
        f"`{private_key}`\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⚠️ *SECURITY*       │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Never share this key\n"
        f"▸ Anyone with this key controls your funds\n"
        f"▸ Delete this message after saving\n\n"
        f"⚠️ *This message will self-destruct in 60 seconds!*"
    )

    keyboard = [[InlineKeyboardButton("« Back", callback_data="wallets")]]

    sent_msg = await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    # Auto-delete after 60 seconds for security
    await asyncio.sleep(60)
    try:
        await sent_msg.edit_message_text(
            "🔒 *Private key message deleted for security.*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        pass  # Message might already be deleted

async def snipe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual snipe - prompt user to enter token address to snipe"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_data = db.get_user(user.id)
    wallets = db.get_user_wallets(user.id)

    if not wallets:
        msg = (
            f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃                                                    ┃\n"
            f"┃      🎯 *MANUAL SNIPE*        ┃\n"
            f"┃                                                    ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"┌─────────────────────┐\n"
            f"│  ⚠️  *NO WALLET*      │\n"
            f"└─────────────────────┘\n\n"
            f"You need a wallet to snipe tokens!\n\n"
            f"Create a wallet first:\n"
            f"1. Click 'My Wallets'\n"
            f"2. Create new wallet\n"
            f"3. Fund it with ETH\n"
            f"4. Come back to snipe!\n\n"
            f"💡 You need ETH on Base to buy tokens."
        )

        keyboard = [
            [InlineKeyboardButton("👛 Create Wallet", callback_data="wallets")],
            [InlineKeyboardButton("« Back", callback_data="menu")]
        ]

        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      🎯 *MANUAL SNIPE*        ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  📝 *INSTRUCTIONS*   │\n"
        f"└─────────────────────┘\n\n"
        f"Paste the token contract address\n"
        f"you want to snipe:\n\n"
        f"*Example:*\n"
        f"`0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`\n\n"
        f"┌─────────────────────┐\n"
        f"│  💰 *YOUR WALLET*    │\n"
        f"└─────────────────────┘\n\n"
        f"`{wallets[0]['wallet_address']}`\n\n"
        f"┌─────────────────────┐\n"
        f"│  🎯 *WHAT I DO*      │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Analyze the token\n"
        f"▸ Check liquidity\n"
        f"▸ Estimate gas fees\n"
        f"▸ Execute buy order\n"
        f"▸ Send confirmation\n\n"
        f"┌─────────────────────┐\n"
        f"│  ⚠️  *IMPORTANT*     │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Make sure wallet has ETH\n"
        f"▸ High gas = faster execution\n"
        f"▸ Always DYOR first\n"
        f"▸ Not financial advice\n\n"
        f"💡 Paste token address below!"
    )

    # Set user state to waiting for snipe address
    context.user_data['waiting_for_snipe'] = True
    context.user_data['snipe_wallet'] = wallets[0]['wallet_address']

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_back_button())

async def checktoken_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to enter token contract address"""
    query = update.callback_query
    await query.answer()

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      🔍 *CHECK TOKEN*         ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  📝 *INSTRUCTIONS*   │\n"
        f"└─────────────────────┘\n\n"
        f"Paste a token contract address\n"
        f"from Base chain below:\n\n"
        f"*Example:*\n"
        f"`0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`\n\n"
        f"┌─────────────────────┐\n"
        f"│  🔍 *WHAT I CHECK*   │\n"
        f"└─────────────────────┘\n\n"
        f"▸ Token name & symbol\n"
        f"▸ Total supply & decimals\n"
        f"▸ Ownership status\n"
        f"▸ Advanced analytics 💎\n\n"
        f"💡 Just paste the contract address below!"
    )

    # Set user state to waiting for token address
    context.user_data['waiting_for_token'] = True

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=create_back_button())

async def handle_snipe_input(update: Update, context: ContextTypes.DEFAULT_TYPE, token_address: str):
    """Handle manual snipe execution"""
    user = update.effective_user

    # Clear the waiting state
    context.user_data['waiting_for_snipe'] = False
    wallet_address = context.user_data.get('snipe_wallet')

    # Validate address format
    if not token_address.startswith('0x') or len(token_address) != 42:
        await update.message.reply_text(
            "❌ Invalid address format!\n\n"
            "Please send a valid token address:\n"
            "`0x1234567890abcdef1234567890abcdef12345678`\n\n"
            "Use /start to try again.",
            parse_mode='Markdown'
        )
        return

    # Send "preparing snipe" message
    snipe_msg = await update.message.reply_text(
        "🎯 *PREPARING SNIPE...*\n\n"
        "⏳ Analyzing token...",
        parse_mode='Markdown'
    )

    try:
        # Get token contract
        token_address_checksum = w3.to_checksum_address(token_address)
        token_contract = w3.eth.contract(address=token_address_checksum, abi=ERC20_ABI)

        # Get token info
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            await snipe_msg.edit_text(
                "❌ *Error: Not a valid ERC20 token*\n\n"
                "This contract doesn't appear to be a standard token.\n\n"
                f"Error: `{str(e)[:100]}`",
                parse_mode='Markdown'
            )
            return

        # Check ownership
        try:
            owner = token_contract.functions.owner().call()
            is_renounced = owner == '0x0000000000000000000000000000000000000000'
        except:
            is_renounced = False

        # Get current block for gas estimation
        current_block = w3.eth.block_number
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')

        # Estimate costs
        estimated_gas = 200000  # Typical swap gas
        gas_cost_eth = w3.from_wei(gas_price * estimated_gas, 'ether')

        # Run security scan
        await snipe_msg.edit_text(
            "🎯 *PREPARING SNIPE...*\n\n"
            "🛡️ Running security scan...",
            parse_mode='Markdown'
        )

        security_results = security_scanner.scan_token(token_address_checksum)
        security_report = security_scanner.format_security_report(security_results)

        # Get wallet balance
        eth_balance_data = trading_bot.get_eth_balance(wallet_address)
        eth_balance = eth_balance_data.get('balance_eth', 0) if eth_balance_data['success'] else 0

        # Get token balance
        token_balance_data = trading_bot.get_token_balance(token_address_checksum, wallet_address)
        token_balance = token_balance_data.get('balance_formatted', 0) if token_balance_data['success'] else 0

        # Store token address in context for buy/sell callbacks
        context.user_data['current_token'] = token_address_checksum
        context.user_data['current_token_symbol'] = symbol

        # Build snipe summary with security report
        msg = (
            f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃                                                    ┃\n"
            f"┃      🎯 *SNIPE READY*         ┃\n"
            f"┃                                                    ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"┌─────────────────────┐\n"
            f"│  💎 *TOKEN INFO*     │\n"
            f"└─────────────────────┘\n\n"
            f"Name: *{name}*\n"
            f"Symbol: *${symbol}*\n"
            f"Decimals: {decimals}\n"
            f"Ownership: {'✅ Renounced' if is_renounced else '⚠️ NOT Renounced'}\n\n"
            f"{security_report}\n\n"
            f"┌─────────────────────┐\n"
            f"│  💰 *YOUR BALANCES*  │\n"
            f"└─────────────────────┘\n\n"
            f"ETH: *{eth_balance:.6f} ETH*\n"
            f"${symbol}: *{token_balance:,.2f}*\n\n"
            f"┌─────────────────────┐\n"
            f"│  ⛽ *GAS ESTIMATE*   │\n"
            f"└─────────────────────┘\n\n"
            f"Gas Price: {gas_price_gwei:.2f} Gwei\n"
            f"Estimated Cost: ~{gas_cost_eth:.6f} ETH\n\n"
            f"┌─────────────────────┐\n"
            f"│  📍 *TOKEN ADDRESS*  │\n"
            f"└─────────────────────┘\n\n"
            f"`{token_address_checksum}`\n\n"
            f"┌─────────────────────┐\n"
            f"│  ⚡ *QUICK ACTIONS*  │\n"
            f"└─────────────────────┘\n\n"
            f"Choose an action below:\n"
            f"▸ *BUY* - Purchase tokens with ETH\n"
            f"▸ *SELL* - Sell your tokens for ETH\n"
            f"▸ *APPROVE* - Approve token for trading\n\n"
            f"⚠️ *Not financial advice. Trade at your own risk!*"
        )

        keyboard = [
            [
                InlineKeyboardButton("💰 Buy 0.01 ETH", callback_data=f"buy_0.01_{token_address_checksum}"),
                InlineKeyboardButton("💰 Buy 0.05 ETH", callback_data=f"buy_0.05_{token_address_checksum}")
            ],
            [
                InlineKeyboardButton("💰 Buy 0.1 ETH", callback_data=f"buy_0.1_{token_address_checksum}"),
                InlineKeyboardButton("💰 Buy Custom", callback_data=f"buy_custom_{token_address_checksum}")
            ],
            [
                InlineKeyboardButton("📉 Sell 25%", callback_data=f"sell_25_{token_address_checksum}"),
                InlineKeyboardButton("📉 Sell 50%", callback_data=f"sell_50_{token_address_checksum}")
            ],
            [
                InlineKeyboardButton("📉 Sell 75%", callback_data=f"sell_75_{token_address_checksum}"),
                InlineKeyboardButton("📉 Sell 100%", callback_data=f"sell_100_{token_address_checksum}")
            ],
            [InlineKeyboardButton("✅ Approve Token", callback_data=f"approve_{token_address_checksum}")],
            [InlineKeyboardButton("🔍 View on Basescan", url=f"https://basescan.org/token/{token_address_checksum}")],
            [InlineKeyboardButton("📊 DexScreener", url=f"https://dexscreener.com/base/{token_address_checksum}")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
        ]

        await snipe_msg.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Snipe preparation error: {e}")
        await snipe_msg.edit_text(
            f"❌ *Error preparing snipe*\n\n"
            f"Could not analyze this token. Make sure:\n"
            f"• Address is correct\n"
            f"• Token is on Base chain\n"
            f"• Contract is verified\n\n"
            f"Error: `{str(e)[:100]}`",
            parse_mode='Markdown'
        )

async def handle_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's token contract address input"""
    user = update.effective_user
    text = update.message.text.strip()

    # Check if user is waiting for snipe input
    if context.user_data.get('waiting_for_snipe'):
        await handle_snipe_input(update, context, text)
        return

    # Check if user is waiting for token input
    if not context.user_data.get('waiting_for_token'):
        return

    # Clear the waiting state
    context.user_data['waiting_for_token'] = False

    # Validate address format
    if not text.startswith('0x') or len(text) != 42:
        await update.message.reply_text(
            "❌ Invalid address format!\n\n"
            "Please send a valid Ethereum address:\n"
            "`0x1234567890abcdef1234567890abcdef12345678`\n\n"
            "Use /start to try again.",
            parse_mode='Markdown'
        )
        return

    # Send "analyzing" message
    analyzing_msg = await update.message.reply_text("🔍 Analyzing token... Please wait...")

    try:
        # Check if user is premium
        user_data = db.get_user(user.id)
        is_premium = user_data and user_data['tier'] == 'premium'

        # Get token contract
        token_address = w3.to_checksum_address(text)
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

        # Get basic token info
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            total_supply = token_contract.functions.totalSupply().call()
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            await analyzing_msg.edit_text(
                "❌ *Error: Not a valid ERC20 token*\n\n"
                "This contract doesn't appear to be a standard token.\n\n"
                f"Error: `{str(e)[:100]}`",
                parse_mode='Markdown'
            )
            return

        # Check ownership
        owner = "Unknown"
        renounced = False
        try:
            owner = token_contract.functions.owner().call()
            burn_addresses = [
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000001",
                "0x000000000000000000000000000000000000dEaD"
            ]
            renounced = owner.lower() in [a.lower() for a in burn_addresses]
        except:
            renounced = True  # No owner function = likely renounced
        # Format supply
        supply_formatted = total_supply / (10 ** decimals)

        # ===== FETCH COMPREHENSIVE METRICS =====
        metrics = {
            'price_usd': 0,
            'market_cap': 0,
            'liquidity_usd': 0,
            'volume_24h': 0,
            'ath': None,
            'has_limits': False,
            'limit_details': 'No limits',
            'clog_percentage': 0.03,
            'airdrops': []
        }
        
        # Try to fetch comprehensive metrics
        try:
            # Get DexScreener data
            dex_data = await get_dexscreener_data(token_address)
            metrics.update(dex_data)
            
            # Get transfer limits
            limits = await check_transfer_limits(token_address)
            metrics['has_limits'] = limits['has_limits']
            metrics['limit_details'] = limits['details']
            
            # Get clog percentage
            metrics['clog_percentage'] = await calculate_clog_percentage(token_address, token_address)
            
            # Detect airdrops (premium only)
            if is_premium:
                metrics['airdrops'] = await detect_airdrops(token_address)
        except Exception as e:
            logger.debug(f"Could not fetch all metrics: {e}")

        # ===== SECURITY SCAN =====
        is_honeypot = False
        buy_tax = 0
        sell_tax = 0
        transfer_tax = 0
        liquidity_locked = False
        lock_days = 0
        locker_name = "Unknown"
        
        try:
            from security_scanner import SecurityScanner
            scanner = SecurityScanner(w3)
            
            # Check honeypot
            honeypot_result = scanner.check_honeypot(token_address)
            is_honeypot = honeypot_result.get('is_honeypot', False)
            buy_tax = honeypot_result.get('buy_tax', 0)
            sell_tax = honeypot_result.get('sell_tax', 0)
            
            # Check liquidity lock
            lock_result = scanner.check_liquidity_lock(token_address)
            liquidity_locked = lock_result.get('is_locked', False)
            lock_days = lock_result.get('lock_days', 0)
            locker_name = lock_result.get('locker_name', 'Unknown')
        except Exception as e:
            logger.debug(f"Security scan failed: {e}")

        total_tax = buy_tax + sell_tax + transfer_tax

        # Format numbers
        def format_number(num):
            if num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"${num/1_000:.2f}K"
            else:
                return f"${num:.2f}"

        mc_str = format_number(metrics['market_cap']) if metrics['market_cap'] > 0 else "N/A"
        ath_str = format_number(metrics['ath']) if metrics.get('ath') and is_premium else ("Premium Only" if not is_premium else "N/A")
        liq_str = format_number(metrics['liquidity_usd']) if metrics['liquidity_usd'] > 0 else "N/A"
        price_str = f"${metrics['price_usd']:.8f}" if metrics['price_usd'] > 0 else "N/A"
        vol_str = format_number(metrics['volume_24h']) if metrics['volume_24h'] > 0 else "N/A"
        airdrop_str = ", ".join(metrics['airdrops']) if is_premium and metrics['airdrops'] else ("None detected" if is_premium else "Premium Only")

        # Build response message with comprehensive security scan
        status_emoji = "✅" if renounced else "⚠️"

        msg = (
            f"╔═══════════════════════╗\n"
            f"   🔍 *TOKEN ANALYSIS*\n"
            f"╚═══════════════════════╝\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *TOKEN INFO*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Name: *{name}*\n"
            f"Symbol: *${symbol.upper()}*\n"
            f"Decimals: *{decimals}*\n"
            f"Total Supply: *{supply_formatted:,.0f}*\n\n"
            f"🧢 MC: {mc_str}     | ATH: {ath_str}\n"
            f"💧 Liq: {liq_str}\n"
            f"🏷 Price: {price_str}\n"
            f"🎚 Vol: {vol_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ *SAFETY CHECKS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{status_emoji} Ownership: *{'Renounced ✅' if renounced else 'NOT Renounced ⚠️'}*\n"
            f"{'✅' if not is_honeypot else '🚨'} Honeypot: *{'SAFE' if not is_honeypot else 'DETECTED ⚠️'}*\n"
            f"{'✅' if liquidity_locked else '❌'} LP Locked: *{'YES' if liquidity_locked else 'NO'}*"
        )

        if liquidity_locked:
            msg += f"\n   └ {lock_days} days via {locker_name}"

        msg += (
            f"\n\n🏧 B: {buy_tax:.2f}% | S: {sell_tax:.2f}% | T: {total_tax:.2f}%\n"
            f"⚖️ {metrics['limit_details']}\n"
            f"🪠 Clog: {metrics['clog_percentage']:.2f}%\n\n"
        )

        if is_premium:
            msg += f"🪂 Airdrops: {airdrop_str}\n\n"
        else:
            msg += f"💡 *Upgrade to Premium* for ATH tracking & airdrop detection!\n\n"

        msg += (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 *CONTRACT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`{token_address}`\n\n"
            f"⚠️ *DYOR! Not financial advice.*\n"
            f"Always verify before investing!"
        )

        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔍 View on Basescan", url=f"https://basescan.org/token/{token_address}"),
            ],
            [
                InlineKeyboardButton("📊 DexScreener", url=f"https://dexscreener.com/base/{token_address}"),
                InlineKeyboardButton("🦄 Uniswap", url=f"https://app.uniswap.org/#/tokens/base/{token_address}")
            ],
            [
                InlineKeyboardButton("« Back to Menu", callback_data="menu")
            ]
        ]

        await analyzing_msg.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Token analysis error: {e}")
        await analyzing_msg.edit_text(
            f"❌ *Error analyzing token*\n\n"
            f"Could not analyze this contract. Make sure:\n"
            f"• Address is correct\n"
            f"• Token is on Base chain\n"
            f"• Contract is verified\n\n"
            f"Error: `{str(e)[:100]}`",
            parse_mode='Markdown'
        )

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, eth_amount: float, token_address: str):
    """Handle buy transaction"""
    query = update.callback_query
    user = query.from_user

    # Get user's wallet
    wallets = db.get_user_wallets(user.id)
    if not wallets:
        await query.answer("❌ No wallet found!", show_alert=True)
        return

    wallet_address = wallets[0]['wallet_address']
    private_key = db.get_wallet_private_key(user.id, wallet_address)

    if not private_key:
        await query.answer("❌ Could not retrieve private key!", show_alert=True)
        return

    # Show processing message
    await query.edit_message_text(
        f"⏳ *EXECUTING BUY ORDER...*\n\n"
        f"Amount: *{eth_amount} ETH*\n"
        f"Token: `{token_address}`\n\n"
        f"Please wait...",
        parse_mode='Markdown'
    )

    # Execute buy with fee
    result = trading_bot.buy_token(
        token_address,
        private_key,
        eth_amount,
        fee_wallet=admin_manager.fee_wallet,
        fee_percentage=admin_manager.fee_percentage
    )

    if result['success']:
        # Mark user as having traded (for referral tracking)
        referrer_id = db.mark_user_traded(user.id)

        # Check if referrer should be upgraded to premium
        if referrer_id:
            if db.check_and_upgrade_premium(referrer_id):
                # Notify referrer they got premium
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=(
                            "🎉 *CONGRATULATIONS!*\n\n"
                            "One of your referrals just made their first trade!\n"
                            "You've reached *10 active referrals*!\n\n"
                            "✅ You've been upgraded to *PREMIUM* for 1 month! 💎\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                            "⭐ *PREMIUM FEATURES UNLOCKED*\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "✓ Advanced analytics\n"
                            "✓ Initial liquidity data\n"
                            "✓ Priority alerts (5-10s faster)\n"
                            "✓ Premium badge 💎\n\n"
                            "Thank you for spreading the word! 🚀"
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify referrer {referrer_id}: {e}")

        msg = (
            f"✅ *BUY ORDER SUBMITTED!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *TRANSACTION DETAILS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Amount Spent: *{eth_amount} ETH*\n"
            f"TX Hash: `{result['tx_hash']}`\n\n"
            f"🔍 View on Basescan:\n"
            f"https://basescan.org/tx/{result['tx_hash']}\n\n"
            f"⏳ *Transaction is processing...*\n"
            f"Check Basescan for confirmation!"
        )
        keyboard = [
            [InlineKeyboardButton("🔍 View TX", url=f"https://basescan.org/tx/{result['tx_hash']}")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
        ]
    else:
        msg = (
            f"❌ *BUY ORDER FAILED!*\n\n"
            f"Error: `{result['message']}`\n\n"
            f"Possible reasons:\n"
            f"▸ Insufficient ETH balance\n"
            f"▸ Token not tradeable\n"
            f"▸ Liquidity too low\n"
            f"▸ Gas price too low\n\n"
            f"Try again or check token on Basescan."
        )
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu")]]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def handle_sell(update: Update, context: ContextTypes.DEFAULT_TYPE, percentage: float, token_address: str):
    """Handle sell transaction"""
    query = update.callback_query
    user = query.from_user

    # Get user's wallet
    wallets = db.get_user_wallets(user.id)
    if not wallets:
        await query.answer("❌ No wallet found!", show_alert=True)
        return

    wallet_address = wallets[0]['wallet_address']
    private_key = db.get_wallet_private_key(user.id, wallet_address)

    if not private_key:
        await query.answer("❌ Could not retrieve private key!", show_alert=True)
        return

    # Show processing message
    await query.edit_message_text(
        f"⏳ *EXECUTING SELL ORDER...*\n\n"
        f"Selling: *{percentage}%*\n"
        f"Token: `{token_address}`\n\n"
        f"Please wait...",
        parse_mode='Markdown'
    )

    # Execute sell
    result = trading_bot.sell_token(token_address, private_key, percentage)

    if result['success']:
        # Mark user as having traded (for referral tracking)
        referrer_id = db.mark_user_traded(user.id)

        # Check if referrer should be upgraded to premium
        if referrer_id:
            if db.check_and_upgrade_premium(referrer_id):
                # Notify referrer they got premium
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=(
                            "🎉 *CONGRATULATIONS!*\n\n"
                            "One of your referrals just made their first trade!\n"
                            "You've reached *10 active referrals*!\n\n"
                            "✅ You've been upgraded to *PREMIUM* for 1 month! 💎\n\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                            "⭐ *PREMIUM FEATURES UNLOCKED*\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            "✓ Advanced analytics\n"
                            "✓ Initial liquidity data\n"
                            "✓ Priority alerts (5-10s faster)\n"
                            "✓ Premium badge 💎\n\n"
                            "Thank you for spreading the word! 🚀"
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify referrer {referrer_id}: {e}")

        msg = (
            f"✅ *SELL ORDER SUBMITTED!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *TRANSACTION DETAILS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Percentage Sold: *{percentage}%*\n"
            f"TX Hash: `{result['tx_hash']}`\n\n"
            f"🔍 View on Basescan:\n"
            f"https://basescan.org/tx/{result['tx_hash']}\n\n"
            f"⏳ *Transaction is processing...*\n"
            f"Check Basescan for confirmation!"
        )
        keyboard = [
            [InlineKeyboardButton("🔍 View TX", url=f"https://basescan.org/tx/{result['tx_hash']}")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
        ]
    else:
        msg = (
            f"❌ *SELL ORDER FAILED!*\n\n"
            f"Error: `{result['message']}`\n\n"
            f"Possible reasons:\n"
            f"▸ No tokens to sell\n"
            f"▸ Token not approved\n"
            f"▸ Liquidity too low\n"
            f"▸ Gas price too low\n\n"
            f"Try approving the token first."
        )
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu")]]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def handle_approve(update: Update, context: ContextTypes.DEFAULT_TYPE, token_address: str):
    """Handle token approval"""
    query = update.callback_query
    user = query.from_user

    # Get user's wallet
    wallets = db.get_user_wallets(user.id)
    if not wallets:
        await query.answer("❌ No wallet found!", show_alert=True)
        return

    wallet_address = wallets[0]['wallet_address']
    private_key = db.get_wallet_private_key(user.id, wallet_address)

    if not private_key:
        await query.answer("❌ Could not retrieve private key!", show_alert=True)
        return

    # Show processing message
    await query.edit_message_text(
        f"⏳ *APPROVING TOKEN...*\n\n"
        f"Token: `{token_address}`\n\n"
        f"Please wait...",
        parse_mode='Markdown'
    )

    # Execute approval
    result = trading_bot.approve_token(token_address, private_key)

    if result['success']:
        msg = (
            f"✅ *TOKEN APPROVED!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *TRANSACTION DETAILS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"TX Hash: `{result['tx_hash']}`\n\n"
            f"🔍 View on Basescan:\n"
            f"https://basescan.org/tx/{result['tx_hash']}\n\n"
            f"✅ You can now sell this token!"
        )
        keyboard = [
            [InlineKeyboardButton("🔍 View TX", url=f"https://basescan.org/tx/{result['tx_hash']}")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
        ]
    else:
        msg = (
            f"❌ *APPROVAL FAILED!*\n\n"
            f"Error: `{result['message']}`\n\n"
            f"Try again later."
        )
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu")]]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel (admin only)"""
    user = update.effective_user

    if not admin_manager.is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return

    stats = admin_manager.get_admin_stats()

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      👑 *ADMIN PANEL*         ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  📊 *USER STATS*     │\n"
        f"└─────────────────────┘\n\n"
        f"Total Users: *{stats.get('total_users', 0):,}*\n"
        f"Premium Users: *{stats.get('premium_users', 0):,}*\n"
        f"Free Users: *{stats.get('free_users', 0):,}*\n"
        f"Total Referrals: *{stats.get('total_referrals', 0):,}*\n"
        f"Total Wallets: *{stats.get('total_wallets', 0):,}*\n\n"
        f"┌─────────────────────┐\n"
        f"│  💰 *FEE SETTINGS*   │\n"
        f"└─────────────────────┘\n\n"
        f"Trading Fee: *{stats.get('current_fee_percentage', 0)}%*\n"
        f"Fees Collected: *{stats.get('total_fees_collected', 0):.6f} ETH*\n\n"
        f"┌─────────────────────┐\n"
        f"│  💳 *WALLETS*        │\n"
        f"└─────────────────────┘\n\n"
        f"Payment Wallet:\n`{stats.get('payment_wallet', 'Not set')}`\n\n"
        f"Fee Collection Wallet:\n`{stats.get('fee_wallet', 'Not set')}`\n\n"
        f"Use the buttons below to manage:"
    )

    keyboard = [
        [
            InlineKeyboardButton("💳 Update Payment Address", callback_data="admin_update_payment"),
            InlineKeyboardButton("💰 Update Fee %", callback_data="admin_update_fee")
        ],
        [
            InlineKeyboardButton("👑 Grant Premium", callback_data="admin_grant_premium"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📊 Refresh Stats", callback_data="admin_panel"),
            InlineKeyboardButton("« Back to Menu", callback_data="menu")
        ]
    ]

    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel via callback"""
    query = update.callback_query
    user = query.from_user

    if not admin_manager.is_admin(user.id, user.username):
        await query.answer("❌ Access denied. Admin only.", show_alert=True)
        return

    stats = admin_manager.get_admin_stats()

    msg = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃                                                    ┃\n"
        f"┃      👑 *ADMIN PANEL*         ┃\n"
        f"┃                                                    ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"┌─────────────────────┐\n"
        f"│  📊 *USER STATS*     │\n"
        f"└─────────────────────┘\n\n"
        f"Total Users: *{stats.get('total_users', 0):,}*\n"
        f"Premium Users: *{stats.get('premium_users', 0):,}*\n"
        f"Free Users: *{stats.get('free_users', 0):,}*\n"
        f"Total Referrals: *{stats.get('total_referrals', 0):,}*\n"
        f"Total Wallets: *{stats.get('total_wallets', 0):,}*\n\n"
        f"┌─────────────────────┐\n"
        f"│  💰 *FEE SETTINGS*   │\n"
        f"└─────────────────────┘\n\n"
        f"Trading Fee: *{stats.get('current_fee_percentage', 0)}%*\n"
        f"Fees Collected: *{stats.get('total_fees_collected', 0):.6f} ETH*\n\n"
        f"┌─────────────────────┐\n"
        f"│  💳 *WALLETS*        │\n"
        f"└─────────────────────┘\n\n"
        f"Payment Wallet:\n`{stats.get('payment_wallet', 'Not set')}`\n\n"
        f"Fee Collection Wallet:\n`{stats.get('fee_wallet', 'Not set')}`\n\n"
        f"Use the buttons below to manage:"
    )

    keyboard = [
        [
            InlineKeyboardButton("💳 Update Payment Address", callback_data="admin_update_payment"),
            InlineKeyboardButton("💰 Update Fee %", callback_data="admin_update_fee")
        ],
        [
            InlineKeyboardButton("👑 Grant Premium", callback_data="admin_grant_premium"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📊 Refresh Stats", callback_data="admin_panel"),
            InlineKeyboardButton("« Back to Menu", callback_data="menu")
        ]
    ]

    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route callbacks"""
    query = update.callback_query

    # Handle buy/sell/approve callbacks
    if query.data.startswith('buy_'):
        parts = query.data.split('_')
        if parts[1] == 'custom':
            await query.answer("Custom buy amount coming soon!", show_alert=True)
            return
        eth_amount = float(parts[1])
        token_address = '_'.join(parts[2:])
        await handle_buy(update, context, eth_amount, token_address)
        return

    if query.data.startswith('sell_'):
        parts = query.data.split('_')
        percentage = float(parts[1])
        token_address = '_'.join(parts[2:])
        await handle_sell(update, context, percentage, token_address)
        return

    if query.data.startswith('approve_'):
        token_address = query.data.replace('approve_', '')
        await handle_approve(update, context, token_address)
        return

    # Handle admin callbacks
    if query.data.startswith('admin_'):
        if not admin_manager.is_admin(query.from_user.id, query.from_user.username):
            await query.answer("❌ Access denied. Admin only.", show_alert=True)
            return

        if query.data == 'admin_panel':
            await admin_panel_callback(update, context)
            return
        elif query.data == 'admin_update_payment':
            await query.answer("Send new payment address in format:\n/setpayment 0x...", show_alert=True)
            return
        elif query.data == 'admin_update_fee':
            await query.answer("Send new fee % in format:\n/setfee 0.5", show_alert=True)
            return
        elif query.data == 'admin_grant_premium':
            await query.answer("Send user ID in format:\n/grantpremium 123456789", show_alert=True)
            return
        elif query.data == 'admin_broadcast':
            await query.answer("Send broadcast message in format:\n/broadcast Your message here", show_alert=True)
            return

    handlers = {
        'menu': menu,
        'howitworks': howitworks_callback,
        'stats': stats_callback,
        'refer': refer_callback,
        'leaderboard': leaderboard_callback,
        'alerts': alerts_callback,
        'upgrade': upgrade_callback,
        'checktoken': checktoken_callback,
        'snipe': snipe_callback,
        'wallets': wallets_callback,
        'create_wallet': create_wallet_callback,
        'export_key': export_key_callback
    }

    handler = handlers.get(query.data)
    if handler:
        await handler(update, context)
    else:
        await query.answer("Unknown command!")

# ===== SCANNING LOOP =====

async def scan_loop(app: Application):
    """Continuous scanning for new launches"""
    logger.info("🔍 Starting scan loop...")

    # Start from current block
    last_block = w3.eth.block_number
    scanned_pairs = set()

    while True:
        try:
            # Get new pairs (scans 10 blocks at a time due to Alchemy free tier limit)
            pairs = get_new_pairs(last_block)

            for pair in pairs:
                pair_address = pair['address']

                # Skip if already scanned
                if pair_address in scanned_pairs:
                    continue

                scanned_pairs.add(pair_address)

                # Analyze the token with premium analytics enabled
                # (Premium analytics will be included in the data, sent only to premium users)
                analysis = analyze_token(pair_address, pair['token0'], pair['token1'], premium_analytics=True)

                if analysis:
                    logger.info(f"🚀 New launch detected: ${analysis['symbol']} ({analysis['name']})")

                    # Send alert to all users (premium users get priority + extra data)
                    await send_launch_alert(app, analysis)

                # Small delay between analyses
                await asyncio.sleep(1)

            # Update last block to current (we'll scan the next 10 blocks from here)
            current_block = w3.eth.block_number
            if current_block > last_block + 10:
                last_block = last_block + 10  # Move forward by 10 blocks
            else:
                last_block = current_block  # Caught up, use current block

            # Wait before next scan (10 seconds - faster since we're scanning smaller ranges)
            await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in scan loop: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# ===== MAIN =====

async def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN in .env!")
        return

    if not ALCHEMY_KEY:
        logger.error("❌ Missing ALCHEMY_BASE_KEY in .env!")
        return

    logger.info("╔═══════════════════════════════════╗")
    logger.info("   🚀 BASE FAIR LAUNCH SNIPER BOT")
    logger.info("╚═══════════════════════════════════╝")
    logger.info("")
    logger.info("✅ Initializing...")

    # Test Web3 connection
    try:
        block = w3.eth.block_number
        logger.info(f"✅ Connected to Base (Block: {block:,})")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Base: {e}")
        return

    # Create application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_callback))
    # Handle text messages (for token address input)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_input))

    logger.info(f"✅ Bot username: @{BOT_USERNAME}")
    logger.info("✅ Database initialized")

    # Check payment wallet configuration
    payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS')
    if payment_wallet:
        logger.info(f"💰 Payment wallet: {payment_wallet}")
    else:
        logger.warning("⚠️ PAYMENT_WALLET_ADDRESS not set - premium payments disabled")

    logger.info("")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🔍 Starting real-time scanning...")
    logger.info("📢 Alerts will be sent to all users")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    # Initialize bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # Start payment monitor if wallet is configured
    payment_monitor_task = None
    if payment_wallet:
        try:
            payment_monitor = PaymentMonitor(w3, db, payment_wallet, app)
            payment_monitor_task = asyncio.create_task(payment_monitor.start_monitoring())
            logger.info("💰 Payment monitor started - auto-upgrades enabled!")
        except Exception as e:
            logger.error(f"Failed to start payment monitor: {e}")

    # Start scanning loop
    try:
        await scan_loop(app)
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
    finally:
        if payment_monitor_task:
            payment_monitor_task.cancel()
        await app.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

