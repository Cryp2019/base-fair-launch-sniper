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
from datetime import datetime, timezone
from web3 import Web3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeAllGroupChats
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ChatMemberHandler
from database import UserDatabase
from trading import TradingBot
from security_scanner import SecurityScanner
from admin import AdminManager
from payment_monitor import PaymentMonitor
import html

# Setup logging early for import errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import sponsorship modules (optional for premium features)
try:
    from project_sponsors import SponsoredProjects
    from sponsorship_processor import AutomatedSponsorshipProcessor
    from performers_tracker import register_top_performers_handlers
    SPONSORSHIP_AVAILABLE = True
except ImportError as e:
    SPONSORSHIP_AVAILABLE = False
    logger.warning(f"⚠️ Sponsorship modules not available: {e}")
    SponsoredProjects = None
    AutomatedSponsorshipProcessor = None
    register_top_performers_handlers = None

# Try to import group poster (optional for group posting feature)
try:
    from group_poster import GroupPoster
    GROUP_POSTER_AVAILABLE = True
except ImportError:
    GROUP_POSTER_AVAILABLE = False
    GroupPoster = None

# Import on-chain analyzer for Soul Scanner-style analytics
try:
    from onchain_analyzer import OnChainAnalyzer, format_onchain_section_html, format_onchain_section_markdown
    ONCHAIN_AVAILABLE = True
except ImportError as e:
    ONCHAIN_AVAILABLE = False
    logger.warning(f"⚠️ On-chain analyzer not available: {e}")

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Match Railway variable name
BOT_USERNAME = os.getenv('BOT_USERNAME', 'base_fair_launch_bot')
ALCHEMY_KEY = os.getenv('ALCHEMY_BASE_KEY', '')  # Match Railway variable name
# Use public Base RPC by default (no rate limits), fall back to Alchemy if BASE_RPC_URL is explicitly set to Alchemy
BASE_RPC = os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')

# Payment wallet for sponsorship/payment monitoring (optional)
payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS') or None

# Sponsored/Promoted projects tracker
# Key = lowercase token address, Value = {'name': str, 'tier': str, 'expires': timestamp}
sponsored_projects = {}

# ETH advertising tiers
AD_TIERS = {
    0.05: {'name': 'Bronze', 'duration_days': 1, 'emoji': '🥉'},
    0.1:  {'name': 'Silver', 'duration_days': 3, 'emoji': '🥈'},
    0.25: {'name': 'Gold', 'duration_days': 7, 'emoji': '🥇'},
    0.5:  {'name': 'Diamond', 'duration_days': 14, 'emoji': '💎'},
}

# Base chain addresses
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913".lower()
WETH_ADDRESS = "0x4200000000000000000000000000000000000006".lower()

# Multi-DEX Factory Configuration
FACTORIES = {
    'uniswap_v3': {
        'address': '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
        'type': 'v3',
        'name': 'Uniswap V3',
        'emoji': '🦄',
        'event_topic': '0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118',  # PoolCreated
        'enabled': True
    },
    'uniswap_v2': {
        'address': '0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6',
        'type': 'v2',
        'name': 'Uniswap V2',
        'emoji': '🦄',
        'event_topic': '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9',  # PairCreated
        'enabled': True
    },
    'sushiswap': {
        'address': '0x71524B4f93c58fcbF659783284E38825f0622859',
        'type': 'v2',
        'name': 'SushiSwap',
        'emoji': '🍣',
        'event_topic': '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9',  # PairCreated
        'enabled': True
    },
    'aerodrome': {
        'address': '0x420DD381b31aEf6683db6B902084cB0FFECe40Da',
        'type': 'velodrome',
        'name': 'Aerodrome',
        'emoji': '✈️',
        'event_topic': '0xc4805696c66d7cf352fc1d6bb633ad5ee82f6cb577c453024b6e0eb8306c6fc9',  # PairCreated
        'enabled': True
    },
    'baseswap': {
        'address': '0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB',
        'type': 'v2',
        'name': 'BaseSwap',
        'emoji': '🔷',
        'event_topic': '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9',  # PairCreated
        'enabled': True
    },
    'swapbased': {
        'address': '0x04C9f118d21e8B767D2e50C946f0cC9F6C367300',
        'type': 'v2',
        'name': 'SwapBased',
        'emoji': '🔵',
        'event_topic': '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9',  # PairCreated
        'enabled': True
    }
}

# Keep old FACTORY_ADDRESS for backward compatibility
FACTORY_ADDRESS = FACTORIES['uniswap_v3']['address']

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
onchain_analyzer = OnChainAnalyzer(w3) if ONCHAIN_AVAILABLE else None
if onchain_analyzer:
    logger.info("✅ On-chain analyzer initialized")
admin_manager = AdminManager(db, w3)

# Initialize group poster if available
if GROUP_POSTER_AVAILABLE:
    group_poster = GroupPoster(w3)
else:
    group_poster = None
    logger.warning("⚠️  GroupPoster not available - group posting disabled")

# ===== SCORING FUNCTIONS =====

def calculate_token_scores(analysis: dict, metrics: dict) -> dict:
    """Calculate comprehensive scores for a token"""
    
    # Social Score (0-100) - based on liquidity and holder activity
    social_score = 0
    try:
        # Liquidity indicates community size
        if metrics['liquidity_usd'] > 50000:
            social_score += 30
        elif metrics['liquidity_usd'] > 10000:
            social_score += 20
        elif metrics['liquidity_usd'] > 1000:
            social_score += 10
        
        # Volume indicates active trading
        if metrics['volume_24h'] > 10000:
            social_score += 30
        elif metrics['volume_24h'] > 1000:
            social_score += 20
        elif metrics['volume_24h'] > 100:
            social_score += 10
        
        # Good liquidity/MC ratio = healthy community
        if metrics['market_cap'] > 0:
            liq_ratio = metrics['liquidity_usd'] / metrics['market_cap']
            if liq_ratio > 0.3:
                social_score += 20
            elif liq_ratio > 0.1:
                social_score += 10
        
        # Bonus for established tokens
        if metrics['volume_24h'] > 0 and metrics['liquidity_usd'] > 0:
            social_score += 20
    except:
        pass
    
    # Viral Score (0-100) - based on momentum and growth
    viral_score = 0
    try:
        # Price change indicates viral potential
        price_change = abs(metrics.get('price_change_24h', 0))
        if price_change > 100:
            viral_score += 40
        elif price_change > 50:
            viral_score += 30
        elif price_change > 20:
            viral_score += 20
        elif price_change > 10:
            viral_score += 10
        
        # High volume = viral activity
        if metrics['volume_24h'] > 50000:
            viral_score += 40
        elif metrics['volume_24h'] > 10000:
            viral_score += 30
        elif metrics['volume_24h'] > 1000:
            viral_score += 20
        elif metrics['volume_24h'] > 100:
            viral_score += 10
        
        # Small cap + high volume = viral potential
        if metrics['market_cap'] < 100000 and metrics['volume_24h'] > 1000:
            viral_score += 20
    except:
        pass
    
    # Security Score (0-100) - based on safety checks
    security_score = 0
    try:
        # Ownership renounced = safer
        if analysis.get('renounced'):
            security_score += 30
        
        # Not a honeypot = safe to trade
        if not analysis.get('is_honeypot'):
            security_score += 30
        
        # LP locked = can't rug
        if analysis.get('liquidity_locked'):
            security_score += 25
            
            # Bonus for long lock duration
            lock_days = analysis.get('lock_days', 0)
            if lock_days > 365:
                security_score += 15
            elif lock_days > 90:
                security_score += 10
            elif lock_days > 30:
                security_score += 5
        
        # Low taxes = not a scam
        buy_tax = analysis.get('buy_tax', 0)
        sell_tax = analysis.get('sell_tax', 0)
        if buy_tax < 5 and sell_tax < 5:
            security_score += 10
    except:
        pass
    
    # Overall Score - weighted average
    # Security is most important (40%), then Viral (35%), then Social (25%)
    overall_score = int(
        (social_score * 0.25) + 
        (viral_score * 0.35) + 
        (security_score * 0.40)
    )
    
    # Cap all scores at 100
    social_score = min(social_score, 100)
    viral_score = min(viral_score, 100)
    security_score = min(security_score, 100)
    overall_score = min(overall_score, 100)
    
    return {
        'social_score': social_score,
        'viral_score': viral_score,
        'security_score': security_score,
        'overall_score': overall_score
    }

def get_score_emoji(score: int) -> str:
    """Get color emoji based on score"""
    if score >= 75:
        return "🟢"  # Green - Excellent
    elif score >= 50:
        return "🟡"  # Yellow - Good
    elif score >= 25:
        return "🟠"  # Orange - Caution
    else:
        return "🔴"  # Red - Poor

def format_score(score: int) -> str:
    """Format score with emoji and value"""
    emoji = get_score_emoji(score)
    return f"{emoji} {score}/100"

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
    """Scan for new pairs across multiple DEXs on Base"""
    if last_block is None:
        current_block = w3.eth.block_number
        last_block = current_block - 5  # Alchemy free tier: max 10 block range

    all_pools = []
    
    # Alchemy free tier limits eth_getLogs to 10 block range
    current_block = w3.eth.block_number
    to_block = min(last_block + 10, current_block)
    from_block_hex = hex(last_block)
    to_block_hex = hex(to_block)

    # Scan each enabled DEX factory
    for dex_id, config in FACTORIES.items():
        if not config.get('enabled', True):
            continue
            
        try:
            logs = w3.eth.get_logs({
                'fromBlock': from_block_hex,
                'toBlock': to_block_hex,
                'address': Web3.to_checksum_address(config['address']),
                'topics': [config['event_topic']]
            })

            for log in logs:
                try:
                    pool_data = parse_pair_event(log, config['type'], dex_id, config)
                    if pool_data:
                        all_pools.append(pool_data)
                        logger.info(f"{config['emoji']} Found new {config['name']} {pool_data['pair_type']} pair: {pool_data['address']}")
                except Exception as e:
                    logger.warning(f"Failed to decode {config['name']} log: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to scan {config['name']}: {e}")
            continue

    all_pools.sort(key=lambda x: x['block'], reverse=True)
    return all_pools


def parse_pair_event(log, dex_type: str, dex_id: str, config: dict) -> dict:
    """Parse pair creation event based on DEX type"""
    
    if dex_type == 'v2':
        # V2 DEXs (Uniswap V2, SushiSwap, BaseSwap, SwapBased)
        # Event: PairCreated(address indexed token0, address indexed token1, address pair, uint)
        if len(log['topics']) >= 3:
            token0 = '0x' + log['topics'][1].hex()[-40:]
            token1 = '0x' + log['topics'][2].hex()[-40:]
            # Pair address is in the data field
            pair_address = '0x' + log['data'].hex()[-40:]
            
    elif dex_type == 'v3':
        # V3 DEXs (Uniswap V3)
        # Event: PoolCreated(address indexed token0, address indexed token1, uint24 indexed fee, int24 tickSpacing, address pool)
        if len(log['topics']) >= 4:
            token0 = '0x' + log['topics'][1].hex()[-40:]
            token1 = '0x' + log['topics'][2].hex()[-40:]
            # Pool address is in the data field
            pair_address = '0x' + log['data'].hex()[-40:]
            
    elif dex_type == 'velodrome':
        # Velodrome-style DEXs (Aerodrome)
        # Event: PairCreated(address indexed token0, address indexed token1, bool stable, address pair, uint)
        if len(log['topics']) >= 3:
            token0 = '0x' + log['topics'][1].hex()[-40:]
            token1 = '0x' + log['topics'][2].hex()[-40:]
            # Pair address is in the data field (after stable bool)
            pair_address = '0x' + log['data'].hex()[-40:]
    else:
        return None

    # Only track USDC or WETH pairs
    if not (token0.lower() == USDC_ADDRESS or token1.lower() == USDC_ADDRESS or
            token0.lower() == WETH_ADDRESS or token1.lower() == WETH_ADDRESS):
        return None

    pair_type = "USDC" if (token0.lower() == USDC_ADDRESS or token1.lower() == USDC_ADDRESS) else "WETH"

    return {
        'address': pair_address,
        'token0': token0,
        'token1': token1,
        'block': log['blockNumber'],
        'pair_type': pair_type,
        'dex_id': dex_id,
        'dex_name': config['name'],
        'dex_emoji': config['emoji']
    }

def analyze_token(pair_address: str, token0: str, token1: str, premium_analytics: bool = False, dex_name: str = "Unknown", dex_emoji: str = "🔷", dex_id: str = "unknown") -> dict:
    """Analyze a new token launch"""
    try:
        # Convert addresses to checksum format (Web3.py requirement)
        pair_address = w3.to_checksum_address(pair_address)
        token0 = w3.to_checksum_address(token0)
        token1 = w3.to_checksum_address(token1)
        
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
            'timestamp': datetime.utcnow().isoformat(),
            'dex_name': dex_name,
            'dex_emoji': dex_emoji,
            'dex_id': dex_id
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
        # IMPORTANT: DexScreener API expects token address, not pair address
        dex_data = await get_dexscreener_data(token_address)
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

# Group posting cooldown tracker
_group_post_count = 0
_group_post_cooldown_until = 0  # timestamp when cooldown ends

async def _auto_delete_message(app: Application, chat_id: int, message_id: int, delay: int = 300):
    """Delete a message after delay seconds (default 5 minutes)"""
    try:
        await asyncio.sleep(delay)
        await app.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(f"🗑️ Auto-deleted message {message_id} from group {chat_id}")
    except Exception as e:
        logger.debug(f"Could not auto-delete message {message_id}: {e}")

async def post_to_group_with_buy_button(app: Application, analysis: dict, metrics: dict):
    """Post ALL projects to groups - formats messages directly (no external dependencies)"""
    global _group_post_count, _group_post_cooldown_until
    
    try:
        # Check cooldown: after 5 posts, pause for 2 minutes
        now = time.time()
        if _group_post_cooldown_until > now:
            remaining = int(_group_post_cooldown_until - now)
            logger.info(f"⏳ Group post cooldown active ({remaining}s remaining). Skipping: {analysis.get('name')}")
            return
        
        # Get security score for display
        contract = analysis.get('token_address', '')
        score = analysis.get('security_score', 50)
        
        # Format numbers
        def fmt(num):
            if num >= 1_000_000: return f"${num/1_000_000:.1f}M"
            elif num >= 1_000: return f"${num/1_000:.1f}K"
            elif num > 0: return f"${num:.2f}"
            return "N/A"
        
        name = analysis.get('name', 'Unknown')
        symbol = analysis.get('symbol', 'N/A').upper()
        
        # Check if this is a sponsored project
        is_sponsored = contract.lower() in sponsored_projects
        sponsor_badge = "⭐ SPONSORED ⭐ " if is_sponsored else ""
        
        dex_name = analysis.get('dex_name', 'Unknown')
        dex_emoji = analysis.get('dex_emoji', '🔷')
        mc = fmt(metrics.get('market_cap', 0))
        liq = fmt(metrics.get('liquidity_usd', 0))
        vol = fmt(metrics.get('volume_24h', 0))
        
        # Score emoji
        if score >= 75: score_emoji = "🟢"
        elif score >= 50: score_emoji = "🟡"
        elif score >= 25: score_emoji = "🔴"
        else: score_emoji = "⛔"
        
        # Safety details
        renounced = analysis.get('renounced', False)
        honeypot = analysis.get('is_honeypot', False)
        lp_locked = analysis.get('liquidity_locked', False)
        lock_days = analysis.get('lock_days', 0)
        buy_tax = analysis.get('buy_tax', 0)
        sell_tax = analysis.get('sell_tax', 0)
        
        # Status emojis
        own_emoji = '✅' if renounced else '⚠️'
        hp_emoji = '✅' if not honeypot else '🚨'
        lp_emoji = '✅' if lp_locked else '❌'
        
        launch_time = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        # Price info
        price_usd = metrics.get('price_usd', 0)
        price_str = f"${price_usd:.8f}" if price_usd > 0 else "N/A"
        price_change = metrics.get('price_change_24h', 0)
        change_emoji = "🟢" if price_change > 0 else "🔴" if price_change < 0 else "⚪"
        change_str = f"{change_emoji} {'+' if price_change > 0 else ''}{price_change:.2f}%"
        
        # Token scores (reuse from analysis if available)
        try:
            scores = calculate_token_scores(analysis, metrics)
            social_score = format_score(scores['social_score'])
            viral_score = format_score(scores['viral_score'])
            security_score_str = format_score(scores['security_score'])
            overall_score = format_score(scores['overall_score'])
        except Exception:
            social_score = "N/A"
            viral_score = "N/A"
            security_score_str = f"{score_emoji} {score}/100"
            overall_score = f"{score_emoji} {score}/100"
        
        # Build message (HTML format - matching DM design)
        message_text = (
            f"{sponsor_badge}🚀 <b>NEW TOKEN LAUNCH</b> {'💎' if is_sponsored else ''}\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"<b>{name}</b> (${symbol})\n\n"
            f"📊 <b>LIVE MARKET DATA</b>\n"
            f"💰 Price: {price_str}\n"
            f"🏦 Market Cap: <b>{mc}</b>\n"
            f"📊 Volume (24h): {vol}\n"
            f"💧 Liquidity: {liq}\n"
            f"📉 Change (24h): {change_str}\n"
            f"🏪 DEX: {dex_name} {dex_emoji}\n"
            f"🚀 Release: {launch_time}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🎱 <b>TOKEN SCORES</b>\n"
            f"📱 Social Score: {social_score}\n"
            f"🚀 Viral Score: {viral_score}\n"
            f"🔒 Security Score: {security_score_str}\n"
            f"⭐️ Overall Score: {overall_score}\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"🛡️ <b>SAFETY CHECKS</b>\n"
            f"{own_emoji} Ownership: {'Renounced ✅' if renounced else 'NOT Renounced ⚠️'}\n"
            f"{hp_emoji} Honeypot: {'SAFE' if not honeypot else 'DETECTED ⚠️'}\n"
            f"{lp_emoji} LP Locked: {'YES' if lp_locked else 'NO'}"
            f"{f' ({lock_days} days)' if lp_locked and lock_days else ''}\n"
            f"🏧 Taxes: B:{buy_tax:.1f}% S:{sell_tax:.1f}%\n"
        )
        
        # Add on-chain analytics section
        if onchain_analyzer:
            try:
                onchain_data = onchain_analyzer.analyze_token_onchain(
                    contract,
                    pair_address=analysis.get('pair_address'),
                    total_supply=analysis.get('total_supply', 0),
                    decimals=analysis.get('decimals', 18)
                )
                message_text += format_onchain_section_html(onchain_data)
            except Exception as e:
                logger.warning(f"On-chain analysis failed for group post: {e}")
        
        message_text += (
            f"━━━━━━━━━━━━━━━━\n\n"
            f"📍 <b>CONTRACT</b>\n"
            f"<code>{contract}</code>\n\n"
            f"⚠️ <i>DYOR! Not financial advice.</i>\n\n"
            f"📣 <b>Want your project featured?</b>\n"
            f"Contact @{BOT_USERNAME} for promoted listings!\n"
            f"🚀 Reach 1000s of active Base traders"
        )
        
        # Action buttons - all redirect to DM for privacy
        keyboard = [
            [
                InlineKeyboardButton("📊 Chart", url=f"https://dexscreener.com/base/{contract}"),
                InlineKeyboardButton("🔍 Scan", url=f"https://t.me/{BOT_USERNAME}?start=scan_{contract}"),
            ],
            [
                InlineKeyboardButton("🦄 Swap", url=f"https://app.uniswap.org/#/tokens/base/{contract}"),
                InlineKeyboardButton("🎯 Buy", url=f"https://t.me/{BOT_USERNAME}?start=buy_{contract}"),
            ],
            [
                InlineKeyboardButton("📣 Advertise Your Project", url=f"https://t.me/{BOT_USERNAME}?start=advertise"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get all auto-detected groups
        all_groups = db.get_all_groups()
        
        # Also check for manually configured GROUP_CHAT_ID
        group_chat_id = os.getenv('GROUP_CHAT_ID')
        if group_chat_id and group_chat_id.strip():
            # Avoid duplicates
            manual_id = int(group_chat_id)
            if not any(g['group_id'] == manual_id for g in all_groups):
                all_groups.append({'group_id': manual_id, 'group_name': 'manual', 'group_title': 'Manual Config'})
        
        if not all_groups:
            logger.info(f"No groups configured. Add bot to a group for auto-posting!")
            return
        
        logger.info(f"📢 Posting {name} (${symbol}) to {len(all_groups)} group(s) (score: {score}/100)")
        
        # Post to each group
        for group in all_groups:
            try:
                sent_msg = await app.bot.send_message(
                    chat_id=group['group_id'],
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                db.update_group_post_count(group['group_id'])
                logger.info(f"📢 Posted to group {group['group_id']}: {name} (score: {score}/100)")
                
                # Schedule auto-delete after 5 minutes (skip for sponsored)
                if not is_sponsored:
                    asyncio.create_task(_auto_delete_message(app, group['group_id'], sent_msg.message_id, delay=300))
                else:
                    logger.info(f"⭐ Sponsored post stays permanently: {name}")
                
            except Exception as e:
                logger.warning(f"Failed to post to group {group['group_id']}: {e}")
        
        # Increment post counter and check cooldown
        _group_post_count += 1
        if _group_post_count >= 3:
            _group_post_cooldown_until = time.time() + 300  # 5 minute cooldown
            _group_post_count = 0
            logger.info(f"⏳ Cooldown activated: 3 posts sent, pausing group posts for 5 minutes")
    except Exception as e:
        logger.error(f"Error in group posting: {e}")
        import traceback
        traceback.print_exc()


async def send_launch_alert(app: Application, analysis: dict):
    """Send alert for new token launch - includes safety score for user reference"""

    # Get security score for display (NOT for filtering)
    contract = analysis.get('token_address')
    try:
        rating = security_scanner.scan_token(contract) if security_scanner else {}
    except Exception as e:
        logger.warning(f"Security scan error for {contract}: {e}")
        rating = {}
    score = rating.get('score', 50)  # Default to 50 if scan fails
    analysis['security_score'] = score
    analysis['security_rating'] = rating
    
    # Enrich analysis with security details for group posting
    rug_data = rating.get('rug_detection', {})
    hp_data = rating.get('honeypot', {})
    analysis['is_honeypot'] = hp_data.get('is_honeypot', False)
    analysis['risk_level'] = rating.get('risk_level', 'UNKNOWN')
    analysis['warnings'] = rating.get('warnings', [])
    # Only override renounced if scanner found a result
    if 'ownership_renounced' in rug_data:
        analysis['renounced'] = rug_data['ownership_renounced']
    
    logger.info(f"📢 Sending alert for {analysis.get('name')} (safety score: {score}/100)")

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

    # Get price change emoji
    price_change = metrics.get('price_change_24h', 0)
    change_emoji = "🟢" if price_change > 0 else "🔴" if price_change < 0 else "⚪"
    change_str = f"{change_emoji} {'+' if price_change > 0 else ''}{price_change:.2f}%"
    
    # Calculate time since release
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    pair_created_at = metrics.get('pair_created_at', 0)
    if pair_created_at > 0:
        created_time = datetime.fromtimestamp(pair_created_at / 1000, tz=timezone.utc)
        time_diff = now - created_time
        if time_diff.total_seconds() < 3600:
            release_time = f"{int(time_diff.total_seconds() / 60)}m"
        elif time_diff.total_seconds() < 86400:
            release_time = f"{int(time_diff.total_seconds() / 3600)}h"
        else:
            release_time = f"{int(time_diff.total_seconds() / 86400)}d"
        release_date = created_time.strftime("%b %d, %Y")
    else:
        release_time = "Just now"
        release_date = now.strftime("%b %d, %Y")
    
    # Calculate token scores
    scores = calculate_token_scores(analysis, metrics)
    
    # Run on-chain analysis once (shared across all DM alerts)
    onchain_section_md = ""
    if onchain_analyzer:
        try:
            onchain_data = onchain_analyzer.analyze_token_onchain(
                analysis['token_address'],
                pair_address=analysis.get('pair_address'),
                total_supply=analysis.get('total_supply', 0),
                decimals=analysis.get('decimals', 18)
            )
            onchain_section_md = format_onchain_section_markdown(onchain_data)
        except Exception as e:
            logger.warning(f"On-chain analysis failed for DM alerts: {e}")
    
    # PRIORITY ALERTS: Send to premium users FIRST (5-10 seconds faster)
    for user in premium_users:
        try:
            message = (
                f"🚀 *NEW TOKEN LAUNCH* 💎\n"
                f"━━━━━━━━━━━━━━━━\n\n"
                f"*{analysis['name']}* (${analysis['symbol'].upper()})\n\n"
                f"📊 *LIVE MARKET DATA*\n"
                f"💰 Price: {price_str}\n"
                f"🏦 Market Cap: {mc_str}\n"
                f"📊 Volume (24h): {vol_str}\n"
                f"💧 Liquidity: {liq_str}\n"
                f"📉 Change (24h): {change_str}\n"
                f"🏪 DEX: {analysis.get('dex_name', 'Unknown')} {analysis.get('dex_emoji', '🔷')}\n"
                f"🚀 Release: {release_date} ({release_time})\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🎱 *TOKEN SCORES*\n"
                f"📱 Social Score: {format_score(scores['social_score'])}\n"
                f"🚀 Viral Score: {format_score(scores['viral_score'])}\n"
                f"🔒 Security Score: {format_score(scores['security_score'])}\n"
                f"⭐️ Overall Score: {format_score(scores['overall_score'])}\n"
                f"━━━━━━━━━━━━━━━━\n\n"
                f"🛡️ *SAFETY CHECKS*\n"
                f"{status_emoji} Ownership: {'Renounced ✅' if analysis['renounced'] else 'NOT Renounced ⚠️'}\n"
                f"{'✅' if not analysis.get('is_honeypot') else '🚨'} Honeypot: {'SAFE' if not analysis.get('is_honeypot') else 'DETECTED ⚠️'}\n"
                f"{'✅' if analysis.get('liquidity_locked') else '❌'} LP Locked: {'YES' if analysis.get('liquidity_locked') else 'NO'}"
            )
            
            if analysis.get('liquidity_locked'):
                message += f" ({analysis.get('lock_days', 0)} days)"
            
            message += f"\n🏧 Taxes: B:{buy_tax:.1f}% S:{sell_tax:.1f}%\n"
            
            # Add on-chain analytics
            if onchain_section_md:
                message += onchain_section_md
            
            message += (
                f"━━━━━━━━━━━━━━━━\n\n"
                f"📍 *CONTRACT*\n"
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
        f"🚀 *NEW TOKEN LAUNCH*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"*{analysis['name']}* (${analysis['symbol'].upper()})\n\n"
        f"📊 *LIVE MARKET DATA*\n"
        f"💰 Price: {price_str}\n"
        f"🏦 Market Cap: {mc_str}\n"
        f"📊 Volume (24h): {vol_str}\n"
        f"💧 Liquidity: {liq_str}\n"
        f"📉 Change (24h): {change_str}\n"
        f"🏪 DEX: {analysis.get('dex_name', 'Unknown')} {analysis.get('dex_emoji', '🔷')}\n"
        f"🚀 Release: {release_date} ({release_time})\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ *SAFETY*\n"
        f"{status_emoji} Ownership: {'Renounced ✅' if analysis['renounced'] else 'NOT Renounced ⚠️'}\n"
        f"{'✅' if not analysis.get('is_honeypot') else '🚨'} Honeypot: {'SAFE' if not analysis.get('is_honeypot') else 'DETECTED ⚠️'}\n"
    )
    
    # Add on-chain analytics to free alerts too
    if onchain_section_md:
        free_message += onchain_section_md
    
    free_message += (
        f"━━━━━━━━━━━━━━━━\n\n"
        f"📍 `{analysis['token_address']}`\n\n"
        f"💡 *Upgrade to Premium for advanced metrics!*\n"
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
    
    # Post to group if rating is good
    await post_to_group_with_buy_button(app, analysis, metrics)

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

# ===== HELPER FUNCTIONS =====

def is_group_chat(update: Update) -> bool:
    """Check if message is from a group or supergroup"""
    if not update.effective_chat:
        return False
    return update.effective_chat.type in ['group', 'supergroup']

# ===== COMMAND HANDLERS =====


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    user = update.effective_user
    args = context.args

    # If called from a group, redirect user to DM
    if is_group_chat(update):
        # Auto-register this group for posting
        chat = update.effective_chat
        if chat:
            db.add_group(chat.id, chat.username or 'private_group', chat.title or 'Group')
            logger.info(f"📝 Group registered via /start: {chat.title} (ID: {chat.id})")
        
        bot_me = await context.bot.get_me()
        bot_username = bot_me.username
        group_msg = (
            f"👋 Hey {user.first_name}!\n\n"
            f"🚀 *Base Fair Launch Sniper Bot* is active in this group!\n\n"
            f"I'll post ALL new token launches here automatically.\n"
            f"📊 Group ID: `{chat.id}` ✅ Registered!\n\n"
            f"👉 *Tap below to open your personal bot menu:*"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Open Bot in DM", url=f"https://t.me/{bot_username}?start=group")]
        ])
        await update.message.reply_text(
            group_msg,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        return

    referrer_code = args[0] if args else None
    # Ignore the 'group' arg from DM redirect
    if referrer_code == 'group':
        referrer_code = None
    
    # Handle scan deep link: /start scan_0xABC...
    if referrer_code and referrer_code.startswith('scan_'):
        token_address = referrer_code.replace('scan_', '', 1)
        # Register user first
        db.add_user(user_id=user.id, username=user.username, first_name=user.first_name)
        # Trigger token check in DM
        update.message.text = token_address
        await handle_token_input(update, context)
        return
    
    # Handle buy deep link: /start buy_0xABC...
    if referrer_code and referrer_code.startswith('buy_'):
        token_address = referrer_code.replace('buy_', '', 1)
        # Register user first
        db.add_user(user_id=user.id, username=user.username, first_name=user.first_name)
        # Show buy options in DM
        buy_msg = (
            f"🎯 *Buy Token*\n\n"
            f"Contract: `{token_address}`\n\n"
            f"Select amount to buy:"
        )
        keyboard = [
            [
                InlineKeyboardButton("0.005 ETH", callback_data=f"buy_0.005_{token_address}"),
                InlineKeyboardButton("0.01 ETH", callback_data=f"buy_0.01_{token_address}"),
                InlineKeyboardButton("0.025 ETH", callback_data=f"buy_0.025_{token_address}"),
            ],
            [
                InlineKeyboardButton("0.05 ETH", callback_data=f"buy_0.05_{token_address}"),
                InlineKeyboardButton("0.1 ETH", callback_data=f"buy_0.1_{token_address}"),
                InlineKeyboardButton("0.25 ETH", callback_data=f"buy_0.25_{token_address}"),
            ],
            [
                InlineKeyboardButton("✏️ Custom Amount", callback_data=f"buy_custom_{token_address}"),
            ],
            [
                InlineKeyboardButton("🔍 Scan First", callback_data=f"check_{token_address}"),
                InlineKeyboardButton("📋 Menu", callback_data="menu"),
            ]
        ]
        await update.message.reply_text(
            buy_msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Handle advertise deep link: /start advertise
    if referrer_code and referrer_code == 'advertise':
        db.add_user(user_id=user.id, username=user.username, first_name=user.first_name)
        wallet_display = payment_wallet if payment_wallet else 'Contact @cccryp'
        ad_msg = (
            f"📣 *ADVERTISE YOUR PROJECT*\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"Get your token in front of *thousands* of active Base traders!\n\n"
            f"🎯 *What you get:*\n"
            f"• ⭐ SPONSORED badge on all group posts\n"
            f"• Posts stay permanently (no auto-delete)\n"
            f"• Priority listing on new launch alerts\n"
            f"• Direct exposure to verified traders\n\n"
            f"💎 *Advertising Tiers (ETH):*\n"
            f"🥉 Bronze — 0.05 ETH / 24h\n"
            f"🥈 Silver — 0.1 ETH / 3 days\n"
            f"🥇 Gold — 0.25 ETH / 7 days\n"
            f"💎 Diamond — 0.5 ETH / 14 days\n\n"
            f"💰 *HOW TO PAY (Automatic):*\n"
            f"1️⃣ Send the exact ETH amount to:\n"
            f"`{wallet_display}`\n\n"
            f"2️⃣ After sending, use:\n"
            f"/advertise <contract\_address> <tx\_hash>\n\n"
            f"3️⃣ Bot verifies payment automatically\n"
            f"4️⃣ Your project gets ⭐ SPONSORED badge!\n\n"
            f"🚀 *Reach 1000s of active Base traders today!*"
        )
        keyboard = [
            [InlineKeyboardButton("📩 Contact for Ads", url="https://t.me/cccryp")],
            [InlineKeyboardButton("📋 Menu", callback_data="menu")]
        ]
        await update.message.reply_text(
            ad_msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

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

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command for buying tokens
    Usage: /buy <token_address> <amount_eth>
    Example: /buy 0x1234567890abcdef1234567890abcdef12345678 0.1
    """
    user = update.effective_user
    
    # Check if command is from a group
    if is_group_chat(update):
        # Delete the user's command message for privacy
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete message in group: {e}")
        
        # Always process buy via DM for privacy
        try:
            # Send confirmation to DM instead of group
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    "🔒 *Processing your /buy command privately*\n\n"
                    "Your trade details are kept private.\n"
                    "Processing now..."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            # User hasn't started the bot in DM yet
            bot_me = await context.bot.get_me()
            try:
                await update.effective_chat.send_message(
                    f"@{user.username or user.first_name} Please start the bot first: @{bot_me.username}"
                )
            except:
                pass
            return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Invalid Format*\n\n"
            "Usage: `/buy <token_address> <amount_eth>`\n\n"
            "Example:\n"
            "`/buy 0x1234...5678 0.1`\n\n"
            "• Token address (required)\n"
            "• ETH amount (required)",
            parse_mode='Markdown'
        )
        return
    
    token_address = context.args[0]
    
    try:
        eth_amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid Amount*\n\n"
            f"'{context.args[1]}' is not a valid number.\n\n"
            "Example: `/buy 0x1234...5678 0.1`",
            parse_mode='Markdown'
        )
        return
    
    # Validate token address format
    if not token_address.startswith('0x') or len(token_address) != 42:
        await update.message.reply_text(
            "❌ *Invalid Token Address*\n\n"
            "Token address must be a valid Ethereum address.\n\n"
            "Example: `0x1234567890abcdef1234567890abcdef12345678`",
            parse_mode='Markdown'
        )
        return
    
    # Validate amount
    if eth_amount <= 0:
        await update.message.reply_text(
            "❌ *Invalid Amount*\n\n"
            "Amount must be greater than 0.",
            parse_mode='Markdown'
        )
        return
    
    # Check if user has a wallet
    wallets = db.get_user_wallets(user.id)
    if not wallets:
        await update.message.reply_text(
            "❌ *No Wallet Found*\n\n"
            "You need to create a wallet first.\n"
            "Use /start to create one.",
            parse_mode='Markdown'
        )
        return
    
    wallet_address = wallets[0]['wallet_address']
    private_key = db.get_wallet_private_key(user.id, wallet_address)
    
    if not private_key:
        await update.message.reply_text(
            "❌ *Wallet Error*\n\n"
            "Could not retrieve your wallet. Please contact support.",
            parse_mode='Markdown'
        )
        return
    
    # Check wallet balance
    try:
        balance = w3.eth.get_balance(wallet_address)
        balance_eth = balance / 10**18
        
        if balance_eth < eth_amount:
            await update.message.reply_text(
                f"❌ *Insufficient Balance*\n\n"
                f"You have: `{balance_eth:.4f} ETH`\n"
                f"You need: `{eth_amount} ETH`\n\n"
                f"Please deposit more ETH to your wallet:\n"
                f"`{wallet_address}`",
                parse_mode='Markdown'
            )
            return
    except Exception as e:
        logger.error(f"Error checking balance: {e}")
        await update.message.reply_text(
            "❌ *Error*\n\n"
            "Could not check your wallet balance. Please try again.",
            parse_mode='Markdown'
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"⏳ *EXECUTING BUY ORDER...*\n\n"
        f"Token: `{token_address}`\n"
        f"Amount: *{eth_amount} ETH*\n\n"
        f"Please wait...",
        parse_mode='Markdown'
    )
    
    # Execute buy with fee
    try:
        result = trading_bot.buy_token(
            token_address,
            private_key,
            eth_amount,
            fee_wallet=admin_manager.fee_wallet,
            fee_percentage=admin_manager.fee_percentage,
            user_id=user.id,
            db=db
        )
        
        if result['success']:
            # Mark user as having traded (for referral tracking)
            referrer_id = db.mark_user_traded(user.id)
            
            # Check if referrer should be upgraded to premium
            if referrer_id:
                if db.check_and_upgrade_premium(referrer_id):
                    # Start commission period
                    db.start_referral_commission(referrer_id)
                    
                    # Notify referrer they got premium + commission
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=(
                                "🎉 *CONGRATULATIONS!*\n\n"
                                "One of your referrals just made their first trade!\n"
                                "You've reached *10 active referrals*!\n\n"
                                "✅ *PREMIUM UNLOCKED* for 1 month! 💎\n"
                                "💰 *COMMISSION UNLOCKED* for 30 days!\n\n"
                                "━━━━━━━━━━━━━━━━\n"
                                "💸 *EARN 5% OF TRADING FEES*\n"
                                "━━━━━━━━━━━━━━━━\n\n"
                                "You'll earn 5% of the 0.5% trading fee from your referrals!\n\n"
                                "Example: If your referral trades 1 ETH:\n"
                                "• Trading fee: 0.005 ETH\n"
                                "• Your commission: 0.00025 ETH\n"
                                "• Sent directly to your wallet!\n\n"
                                "Commission expires in 30 days.\n"
                                "Use /earnings to track your earnings! 🚀"
                            ),
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            # Send success message
            await processing_msg.edit_text(
                f"✅ *BUY ORDER SUCCESSFUL!*\n\n"
                f"Token: `{token_address}`\n"
                f"Amount: *{eth_amount} ETH*\n"
                f"Tokens Received: *{result.get('tokens_received', 'N/A')}*\n\n"
                f"Transaction Hash:\n"
                f"`{result['tx_hash']}`\n\n"
                f"[View on Basescan](https://basescan.org/tx/{result['tx_hash']})",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            await processing_msg.edit_text(
                f"❌ *BUY ORDER FAILED*\n\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"Please try again or contact support.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Buy command error: {e}")
        await processing_msg.edit_text(
            f"❌ *BUY ORDER FAILED*\n\n"
            f"Error: {str(e)}\n\n"
            f"Please try again or contact support.",
            parse_mode='Markdown'
        )


async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral earnings and commission stats"""
    user = update.effective_user
    
    # Check if user has commission active
    if not db.is_commission_active(user.id):
        await update.message.reply_text(
            "💰 *REFERRAL EARNINGS*\n\n"
            "You don't have active commissions yet.\n\n"
            "To unlock commissions:\n"
            "1. Refer 10 users who make trades\n"
            "2. Get upgraded to Premium\n"
            "3. Earn 5% of trading fees for 30 days!\n\n"
            "Share your referral link to start earning! 🚀",
            parse_mode='Markdown'
        )
        return
    
    # Get commission stats
    stats = db.get_commission_stats(user.id)
    commissions = db.get_referrer_commissions(user.id)
    
    # Build message
    msg = (
        f"💰 *REFERRAL EARNINGS*\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📊 *STATISTICS*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Total Earned: `{stats['total_earned']:.6f} ETH`\n"
        f"Total Trades: `{stats['total_trades']}`\n"
        f"Days Remaining: `{stats['days_remaining']}`\n\n"
    )
    
    # Show recent commissions
    if commissions:
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += "📝 *RECENT COMMISSIONS*\n"
        msg += "━━━━━━━━━━━━━━━━\n\n"
        
        for i, comm in enumerate(commissions[:5]):  # Show last 5
            msg += f"• `{comm['commission_amount_eth']:.6f} ETH`\n"
            if i >= 4:
                break
    
    msg += "\n━━━━━━━━━━━━━━━━\n"
    msg += "Keep referring to earn more! 🚀"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def advertise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /advertise command - auto-verify payment and activate sponsorship"""
    user = update.effective_user
    args = context.args if context.args else []
    
    # If called with args: /advertise <contract_address> <tx_hash>
    if len(args) >= 2:
        token_address = args[0].strip()
        tx_hash = args[1].strip()
        
        await update.message.reply_text("🔍 Verifying payment on-chain... Please wait.")
        
        try:
            # Look up the transaction
            tx = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                await update.message.reply_text("❌ Transaction failed on-chain. Please try again.")
                return
            
            # Verify payment went to our wallet
            to_addr = tx['to'].lower() if tx.get('to') else ''
            expected_wallet = (payment_wallet or '').lower()
            
            if not expected_wallet or to_addr != expected_wallet:
                await update.message.reply_text(
                    f"❌ Payment not sent to our wallet.\n\n"
                    f"Expected: `{payment_wallet}`\n"
                    f"Got: `{tx.get('to', 'N/A')}`",
                    parse_mode='Markdown'
                )
                return
            
            # Get ETH amount
            eth_amount = tx['value'] / 10**18
            
            # Find matching tier
            matched_tier = None
            for price, tier in AD_TIERS.items():
                if abs(eth_amount - price) < 0.005:  # Small tolerance
                    matched_tier = (price, tier)
                    break
            
            if not matched_tier:
                tier_list = '\n'.join([f"• {p} ETH = {t['name']}" for p, t in AD_TIERS.items()])
                await update.message.reply_text(
                    f"❌ Amount {eth_amount:.4f} ETH doesn't match any tier.\n\n"
                    f"Available tiers:\n{tier_list}",
                    parse_mode='Markdown'
                )
                return
            
            # Activate sponsorship!
            price, tier = matched_tier
            import time as _time
            expires = _time.time() + (tier['duration_days'] * 86400)
            sponsored_projects[token_address.lower()] = {
                'name': tier['name'],
                'tier': tier['emoji'],
                'expires': expires,
                'tx_hash': tx_hash,
                'activated_by': user.id
            }
            
            await update.message.reply_text(
                f"✅ *SPONSORSHIP ACTIVATED!*\n\n"
                f"{tier['emoji']} *{tier['name']}* tier confirmed!\n"
                f"💰 Payment: {eth_amount:.4f} ETH verified ✅\n"
                f"📍 Token: `{token_address}`\n"
                f"⏱️ Duration: {tier['duration_days']} day(s)\n\n"
                f"Your project now gets:\n"
                f"⭐ SPONSORED badge on all group posts\n"
                f"📌 Posts stay permanently (no auto-delete)\n"
                f"🚀 Priority visibility to all traders!\n\n"
                f"Thank you for advertising with us! 🎉",
                parse_mode='Markdown'
            )
            logger.info(f"⭐ SPONSORSHIP ACTIVATED: {token_address} | {tier['name']} | tx={tx_hash} | by={user.id}")
            return
            
        except Exception as e:
            logger.error(f"Advertise verification error: {e}")
            await update.message.reply_text(
                f"❌ Could not verify transaction.\n\n"
                f"Error: {str(e)[:100]}\n\n"
                f"Make sure the tx hash is correct and on Base network."
            )
            return
    
    # No args: show pricing page
    wallet_display = payment_wallet if payment_wallet else 'Contact @cccryp'
    msg = (
        f"📣 *ADVERTISE YOUR PROJECT*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Get your token in front of *thousands* of active Base traders!\n\n"
        f"⭐ *What you get:*\n"
        f"• ⭐ SPONSORED badge on all group posts\n"
        f"• Posts stay permanently (no auto-delete)\n"
        f"• Priority listing on new launch alerts\n"
        f"• Direct exposure to verified traders\n\n"
        f"💎 *Advertising Tiers (ETH):*\n"
        f"🥉 Bronze — 0.05 ETH / 24h\n"
        f"🥈 Silver — 0.1 ETH / 3 days\n"
        f"🥇 Gold — 0.25 ETH / 7 days\n"
        f"💎 Diamond — 0.5 ETH / 14 days\n\n"
        f"💰 *HOW TO PAY (Automatic):*\n"
        f"1️⃣ Send exact ETH amount to:\n"
        f"`{wallet_display}`\n\n"
        f"2️⃣ Then run:\n"
        f"/advertise <contract> <tx\\_hash>\n\n"
        f"3️⃣ Bot verifies & activates instantly! ⚡\n\n"
        f"🚀 *Reach 1000s of active Base traders today!*"
    )
    
    keyboard = [
        [InlineKeyboardButton("📩 Contact for Ads", url="https://t.me/cccryp")],
        [InlineKeyboardButton("« Back", callback_data="menu")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            msg, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            msg, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


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
        f"▸ 💰 Earn 5% of trading fees for 30 days\n"
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
            safe_msg = html.escape(str(result.get('message', '')))
            await query.edit_message_text(
                f"❌ <b>Error creating wallet</b>\n\n<pre>{safe_msg}</pre>\n\nTry again later.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="wallets")]])
            )

    except Exception as e:
        logger.error(f"Wallet creation error: {e}")
        safe_err = html.escape(str(e))
        await query.edit_message_text(
            f"❌ <b>Error creating wallet</b>\n\n<pre>{safe_err}</pre>\n\nTry again later.",
            parse_mode='HTML',
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

    # Handle custom buy amount input
    if context.user_data.get('awaiting_custom_buy'):
        context.user_data['awaiting_custom_buy'] = False
        token_address = context.user_data.get('custom_buy_token', '')
        try:
            eth_amount = float(text)
            if eth_amount <= 0 or eth_amount > 10:
                await update.message.reply_text(
                    "❌ Invalid amount! Enter between 0.001 and 10 ETH.",
                    parse_mode='Markdown'
                )
                return
            await handle_buy(update, context, eth_amount, token_address)
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid number! Please enter a valid ETH amount (e.g. `0.05`).",
                parse_mode='Markdown'
            )
        return

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
    analyzing_msg = await update.message.reply_text("🔍 Scanning token... Please wait...")

    try:
        # Check if user is premium
        user_data = db.get_user(user.id)
        is_premium = user_data and user_data['tier'] == 'premium'
        premium_badge = " 💎" if is_premium else ""

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

        # ===== FETCH DEXSCREENER DATA INLINE =====
        price_usd = 0
        market_cap = 0
        liquidity_usd = 0
        volume_24h = 0
        volume_1h = 0
        price_change_24h = 0
        price_change_1h = 0
        ath_value = None
        pair_age = ""
        holders_count = 0
        dex_paid = False
        pair_url = ""

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pairs = data.get('pairs', [])
                        if pairs:
                            pair = pairs[0]  # Best pair
                            price_usd = float(pair.get('priceUsd', 0) or 0)
                            market_cap = float(pair.get('marketCap', 0) or pair.get('fdv', 0) or 0)
                            liquidity_usd = float(pair.get('liquidity', {}).get('usd', 0) or 0)
                            volume_24h = float(pair.get('volume', {}).get('h24', 0) or 0)
                            volume_1h = float(pair.get('volume', {}).get('h1', 0) or 0)
                            price_change_24h = float(pair.get('priceChange', {}).get('h24', 0) or 0)
                            price_change_1h = float(pair.get('priceChange', {}).get('h1', 0) or 0)
                            pair_url = pair.get('url', '')
                            
                            # Get ATH from price history
                            ath_value = float(pair.get('ath', 0)) if pair.get('ath') else None
                            
                            # Calculate pair age
                            pair_created = pair.get('pairCreatedAt', 0)
                            if pair_created:
                                from datetime import datetime, timezone
                                created_time = datetime.fromtimestamp(pair_created / 1000, tz=timezone.utc)
                                now = datetime.now(timezone.utc)
                                diff = now - created_time
                                days = diff.days
                                if days > 0:
                                    pair_age = f"{days}d"
                                elif diff.total_seconds() > 3600:
                                    pair_age = f"{int(diff.total_seconds() / 3600)}h"
                                else:
                                    pair_age = f"{int(diff.total_seconds() / 60)}m"
                            
                            # Check if dex paid
                            dex_paid = bool(pair.get('paidPromo'))
        except Exception as e:
            logger.debug(f"DexScreener fetch error: {e}")

        # ===== SECURITY SCAN =====
        is_honeypot = False
        buy_tax = 0.0
        sell_tax = 0.0
        liquidity_locked = False
        lock_days = 0
        locker_name = "Unknown"

        try:
            from security_scanner import SecurityScanner
            scanner = SecurityScanner(w3)

            honeypot_result = scanner.check_honeypot(token_address)
            is_honeypot = honeypot_result.get('is_honeypot', False)
            buy_tax = float(honeypot_result.get('buy_tax', 0))
            sell_tax = float(honeypot_result.get('sell_tax', 0))

            lock_result = scanner.check_liquidity_lock(token_address)
            liquidity_locked = lock_result.get('is_locked', False)
            lock_days = lock_result.get('lock_days', 0)
            locker_name = lock_result.get('locker_name', 'Unknown')
        except Exception as e:
            logger.debug(f"Security scan error: {e}")

        # ===== FORMAT DISPLAY VALUES =====
        def fmt(num):
            if num >= 1_000_000:
                return f"${num/1_000_000:.1f}M"
            elif num >= 1_000:
                return f"${num/1_000:.1f}K"
            elif num > 0:
                return f"${num:.2f}"
            return "N/A"

        mc_str = fmt(market_cap)
        liq_str = fmt(liquidity_usd)
        vol_24h_str = fmt(volume_24h)
        vol_1h_str = fmt(volume_1h)
        price_str = f"${price_usd:.10f}" if price_usd > 0 and price_usd < 0.001 else (f"${price_usd:.6f}" if price_usd > 0 and price_usd < 1 else (f"${price_usd:.2f}" if price_usd > 0 else "N/A"))
        
        # ATH display  
        if ath_value and ath_value > 0:
            ath_str = fmt(ath_value)
        elif market_cap > 0:
            ath_str = "🔝" + mc_str  # Current MC as proxy
        else:
            ath_str = "N/A"

        # Price change arrows
        change_24h_emoji = "📈" if price_change_24h > 0 else "📉" if price_change_24h < 0 else "➖"
        change_1h_emoji = "🟢" if price_change_1h > 0 else "🔴" if price_change_1h < 0 else "⚪"
        change_24h_str = f"{'+' if price_change_24h > 0 else ''}{price_change_24h:.1f}%"
        change_1h_str = f"{'+' if price_change_1h > 0 else ''}{price_change_1h:.1f}%"

        # Safety emojis
        own_emoji = "✅" if renounced else "⚠️"
        hp_emoji = "🤍" if not is_honeypot else "🔴"
        lp_emoji = "✅" if liquidity_locked else "❌"
        
        # Tax assessment
        total_tax = buy_tax + sell_tax
        if total_tax <= 5:
            tax_emoji = "🟢"
        elif total_tax <= 15:
            tax_emoji = "🟡"
        else:
            tax_emoji = "🔴"

        # Calculate security score
        sec_score = 0
        if renounced: sec_score += 30
        if not is_honeypot: sec_score += 30
        if liquidity_locked: sec_score += 25
        if total_tax < 5: sec_score += 15
        sec_score = min(sec_score, 100)
        
        # Score bar
        def score_bar(score):
            filled = int(score / 10)
            empty = 10 - filled
            if score >= 75:
                return f"{'🟩' * filled}{'⬜' * empty} {score}/100"
            elif score >= 50:
                return f"{'🟨' * filled}{'⬜' * empty} {score}/100"
            else:
                return f"{'🟥' * filled}{'⬜' * empty} {score}/100"

        # ===== BUILD SLEEK MESSAGE =====
        msg = f"🔬 *{name}* • ${symbol.upper()}{premium_badge}\n"
        msg += f"{'━' * 28}\n\n"

        # Ownership & Honeypot status line (Soul Scanner style)
        msg += f"{own_emoji} Owner: {'Renounced' if renounced else 'Active'} | "
        msg += f"{hp_emoji} Honeypot: {'Safe' if not is_honeypot else 'DANGER'}\n\n"

        # Age & Market Data
        if pair_age:
            msg += f"🕐 Age: *{pair_age}*"
            if price_change_24h != 0:
                msg += f" \\[{change_24h_str}]"
            msg += "\n"
        
        msg += f"💰 MC:   *{mc_str}* • 🔝 {ath_str}\n"
        msg += f"💧 Liq:    *{liq_str}*"
        if liquidity_usd > 0:
            try:
                eth_price = 2500  # Approximate
                liq_eth = liquidity_usd / eth_price
                msg += f" \\[{liq_eth:.1f} ETH]"
            except:
                pass
        msg += "\n"
        msg += f"📊 Vol:    *{vol_1h_str}* \\[1h] • {vol_24h_str} \\[24h]\n"
        msg += f"🏷 Price: *{price_str}*\n"
        if price_change_1h != 0 or price_change_24h != 0:
            msg += f"┗   {change_1h_emoji} 1h: {change_1h_str} | {change_24h_emoji} 24h: {change_24h_str}\n"
        msg += "\n"

        # Safety Checks Section
        msg += f"{'━' * 28}\n"
        msg += f"🛡 *SAFETY*\n"
        msg += f"{'━' * 28}\n"
        msg += f"{own_emoji} Ownership: *{'Renounced ✅' if renounced else 'NOT Renounced ⚠️'}*\n"
        msg += f"{'✅' if not is_honeypot else '🚨'} Honeypot: *{'SAFE' if not is_honeypot else 'DETECTED ⚠️'}*\n"
        msg += f"{lp_emoji} LP Lock: *{'YES' if liquidity_locked else 'NO'}*"
        if liquidity_locked and lock_days > 0:
            msg += f" ({lock_days}d via {locker_name})"
        msg += "\n"
        msg += f"{tax_emoji} Tax: B: {buy_tax:.1f}% | S: {sell_tax:.1f}% | Total: {total_tax:.1f}%\n"
        msg += f"🔒 Score: {score_bar(sec_score)}\n\n"

        # Token Info
        msg += f"{'━' * 28}\n"
        msg += f"📋 *TOKEN*\n"
        msg += f"{'━' * 28}\n"
        msg += f"Supply: *{supply_formatted:,.0f}*\n"
        msg += f"Decimals: *{decimals}*\n\n"

        # Premium section
        if is_premium:
            msg += f"{'━' * 28}\n"
            msg += f"💎 *PREMIUM INTEL*\n"
            msg += f"{'━' * 28}\n"
            if ath_value and ath_value > 0 and market_cap > 0:
                ath_mult = ath_value / market_cap if market_cap > 0 else 0
                msg += f"🔝 ATH MC: {fmt(ath_value)}"
                if ath_mult > 1:
                    msg += f" ({ath_mult:.1f}x from current)"
                msg += "\n"
            msg += f"🦅 DexScreener: {'Paid ✅' if dex_paid else 'Not paid'}\n"
            msg += "\n"
        else:
            msg += f"💡 _Upgrade to Premium for ATH tracking & advanced intel_\n\n"

        # Contract
        msg += f"`{token_address}`\n\n"
        msg += f"⚠️ _DYOR! Not financial advice._"

        # Create action buttons - Soul Scanner style quick links
        keyboard = [
            [
                InlineKeyboardButton("📊 Chart", url=f"https://dexscreener.com/base/{token_address}"),
                InlineKeyboardButton("🔍 Scan", url=f"https://basescan.org/token/{token_address}"),
                InlineKeyboardButton("🦄 Swap", url=f"https://app.uniswap.org/#/tokens/base/{token_address}")
            ],
            [
                InlineKeyboardButton("🎯 Snipe", callback_data=f"snipe_{token_address}"),
                InlineKeyboardButton("💰 Buy 0.01 ETH", callback_data=f"buy_0.01_{token_address}"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"check_{token_address}"),
                InlineKeyboardButton("« Menu", callback_data="menu")
            ]
        ]

        await analyzing_msg.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

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

async def register_commands_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to re-register bot commands for all chats at runtime"""
    user = update.effective_user
    if not admin_manager.is_admin(user.id, user.username):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return

    try:
        commands = [
            BotCommand("start", "Show main menu"),
            BotCommand("menu", "Open menu"),
            BotCommand("buy", "Buy token"),
            BotCommand("checktoken", "Check a token"),
            BotCommand("admin", "Admin panel")
        ]
        # Register for all scopes
        await context.bot.set_my_commands(commands)  # Default (everywhere)
        await context.bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())  # Groups
        await update.message.reply_text("✅ Bot commands re-registered for all chats.")
        logger.info("✅ Admin re-registered bot commands for all chats")
    except Exception as e:
        logger.warning(f"⚠️ Could not re-register bot commands: {e}")
        await update.message.reply_text(f"⚠️ Failed to register commands: {e}")

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
        # Block buy in groups - redirect to DM
        if is_group_chat(update):
            await query.answer("🔒 Open the bot in DM to buy! Your wallet is private.", show_alert=True)
            return
        parts = query.data.split('_')
        if parts[1] == 'custom':
            token_address = '_'.join(parts[2:])
            context.user_data['awaiting_custom_buy'] = True
            context.user_data['custom_buy_token'] = token_address
            await query.answer()
            await query.message.reply_text(
                f"✏️ *Enter custom ETH amount to buy:*\n\n"
                f"Token: `{token_address}`\n\n"
                f"Type the amount in ETH (e.g. `0.03` or `0.5`):",
                parse_mode='Markdown'
            )
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

    if query.data.startswith('snipe_'):
        # Snipe from group post or token check
        token_address = query.data.replace('snipe_', '', 1)
        if is_group_chat(update):
            # Redirect to DM for sniping (needs private wallet)
            bot_me = await context.bot.get_me()
            await query.answer("Open the bot in DM to snipe!", show_alert=True)
            return
        context.user_data['awaiting_snipe'] = True
        context.user_data['snipe_token'] = token_address
        await handle_snipe_input(update, context, token_address)
        return

    if query.data.startswith('check_'):
        # Refresh token check
        token_address = query.data.replace('check_', '', 1)
        # Simulate a token input by storing address and calling handler
        context.user_data['check_token'] = token_address
        await query.answer("🔄 Refreshing...")
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
        'export_key': export_key_callback,
        'advertise': advertise_command
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
    
    # Check how many users have alerts enabled
    users_with_alerts = db.get_users_with_alerts()
    logger.info(f"📊 Users with alerts enabled: {len(users_with_alerts)}")
    if len(users_with_alerts) == 0:
        logger.warning("⚠️  No users have alerts enabled! Alerts will not be sent.")
    else:
        # Count premium vs free
        premium_count = sum(1 for u in users_with_alerts if db.get_user(u['user_id'])['tier'] == 'premium')
        free_count = len(users_with_alerts) - premium_count
        logger.info(f"   👑 Premium users: {premium_count}")
        logger.info(f"   🆓 Free users: {free_count}")

    # Start from current block
    last_block = w3.eth.block_number
    scanned_pairs = set()
    scan_count = 0

    while True:
        try:
            scan_count += 1
            
            # Get new pairs (scans 10 blocks at a time due to Alchemy free tier limit)
            pairs = get_new_pairs(last_block)
            
            # Log scanning activity every 10 scans (~100 seconds)
            if scan_count % 10 == 0:
                current_block = w3.eth.block_number
                logger.info(f"🔍 Scan #{scan_count}: Blocks {last_block:,} to {current_block:,} | Pairs found: {len(pairs)} | Total scanned: {len(scanned_pairs)}")

            if len(pairs) > 0:
                logger.info(f"✨ Found {len(pairs)} new pair(s) in this scan!")

            for pair in pairs:
                pair_address = pair['address']

                # Skip if already scanned
                if pair_address in scanned_pairs:
                    continue

                scanned_pairs.add(pair_address)

                # Analyze the token with premium analytics enabled
                # (Premium analytics will be included in the data, sent only to premium users)
                analysis = analyze_token(
                    pair_address, 
                    pair['token0'], 
                    pair['token1'], 
                    premium_analytics=True,
                    dex_name=pair.get('dex_name', 'Unknown'),
                    dex_emoji=pair.get('dex_emoji', '🔷'),
                    dex_id=pair.get('dex_id', 'unknown')
                )

                if analysis:
                    logger.info(f"🚀 New launch detected: ${analysis['symbol']} ({analysis['name']}) on {analysis.get('dex_name', 'Unknown')}")

                    # Send alert to all users (premium users get priority + extra data)
                    await send_launch_alert(app, analysis)
                else:
                    logger.warning(f"⚠️  Failed to analyze pair {pair_address}")

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
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)  # Wait longer on error

# ===== AUTO GROUP DETECTION HANDLERS =====

async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a group - detect via new_chat_members"""
    try:
        # Check if the BOT was one of the new members
        new_members = update.message.new_chat_members if update.message else []
        bot_was_added = any(member.id == context.bot.id for member in new_members)
        
        if not bot_was_added:
            return  # Some other user was added, not us
        
        chat = update.effective_chat
        if chat.type in ['group', 'supergroup']:
            group_id = chat.id
            group_name = chat.username or "private_group"
            group_title = chat.title or "Group"
            
            # Add to database for auto-posting
            db.add_group(group_id, group_name, group_title)
            
            logger.info(f"🎉 Bot added to group: {group_title} (ID: {group_id})")
            
            # Send welcome message
            welcome_msg = (
                f"👋 Hello! I'm the *Base Fair Launch Sniper Bot*\n\n"
                f"✨ I will automatically post new token launches here!\n\n"
                f"🔍 *What I do:*\n"
                f"• Scan ALL new token launches on Base chain\n"
                f"• Post with safety score & market data\n"
                f"• Auto-delete posts after 5 minutes\n"
                f"• Cooldown: 3 posts, then 5 min pause\n\n"
                f"📊 Group ID: `{group_id}` ✅ Registered!\n"
                f"🔄 Waiting for new fair launches..."
            )
            
            await context.bot.send_message(
                chat_id=group_id,
                text=welcome_msg,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error handling bot added to group: {e}")

async def on_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat member status changes for the bot itself (more reliable detection)"""
    try:
        my_chat_member = update.my_chat_member
        if not my_chat_member:
            return
        
        chat = my_chat_member.chat
        new_status = my_chat_member.new_chat_member.status
        old_status = my_chat_member.old_chat_member.status if my_chat_member.old_chat_member else None
        
        if chat.type in ['group', 'supergroup']:
            # Bot was added or promoted to admin
            if new_status in ['member', 'administrator'] and old_status in [None, 'left', 'kicked']:
                group_id = chat.id
                group_name = chat.username or "private_group"
                group_title = chat.title or "Group"
                
                db.add_group(group_id, group_name, group_title)
                logger.info(f"🎉 Bot added to group (via my_chat_member): {group_title} (ID: {group_id})")
                
                welcome_msg = (
                    f"👋 Hello! I'm the *Base Fair Launch Sniper Bot*\n\n"
                    f"✨ I will automatically post new token launches here!\n\n"
                    f"📊 Group registered! ID: `{group_id}` ✅\n"
                    f"🔄 Waiting for new fair launches..."
                )
                
                try:
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=welcome_msg,
                        parse_mode='Markdown'
                    )
                except Exception:
                    pass  # May not have permission to send yet
            
            # Bot was removed or kicked
            elif new_status in ['left', 'kicked']:
                group_id = chat.id
                db.remove_group(group_id)
                logger.info(f"👋 Bot removed from group: {chat.title} (ID: {group_id})")
    except Exception as e:
        logger.error(f"Error handling my_chat_member update: {e}")

async def on_bot_removed_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is removed from a group via left_chat_member"""
    try:
        chat = update.effective_chat
        if chat and chat.type in ['group', 'supergroup']:
            left_member = update.message.left_chat_member if update.message else None
            if left_member and left_member.id == context.bot.id:
                db.remove_group(chat.id)
                logger.info(f"👋 Bot removed from group: {chat.title} (ID: {chat.id})")
    except Exception as e:
        logger.error(f"Error handling bot removed from group: {e}")

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

    # Ensure slash commands appear in groups: set bot commands for all group chats
    try:
        commands = [
            BotCommand("start", "Show main menu"),
            BotCommand("menu", "Open menu"),
            BotCommand("buy", "Buy token"),
            BotCommand("checktoken", "Check a token"),
            BotCommand("admin", "Admin panel")
        ]
        # Register for all scopes: default, private, and groups
        await app.bot.set_my_commands(commands)  # Default scope (everywhere)
        await app.bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())  # Groups
        logger.info("✅ Bot commands registered globally for all chats")
    except Exception as e:
        logger.warning(f"⚠️ Could not register bot commands: {e}")

    # Initialize sponsored projects tracking (if available)
    sponsored_projects = None
    if SPONSORSHIP_AVAILABLE:
        try:
            sponsored_projects = SponsoredProjects('users.db')
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize sponsorship system: {e}")
    
    # Initialize automated sponsorship processor if payment wallet is configured
    auto_sponsor = None
    if SPONSORSHIP_AVAILABLE and payment_wallet and sponsored_projects:
        try:
            auto_sponsor = AutomatedSponsorshipProcessor(
                db=db,
                sponsored_projects=sponsored_projects,
                payment_wallet=payment_wallet
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize automated sponsorship: {e}")

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("register_commands", register_commands_admin))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("earnings", earnings_command))
    app.add_handler(CommandHandler("advertise", advertise_command))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_callback))
    # Handle text messages (for token address input)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_input))
    
    # Register top performers handlers (if available)
    if SPONSORSHIP_AVAILABLE and register_top_performers_handlers:
        try:
            register_top_performers_handlers(app, sponsored_projects)
        except Exception as e:
            logger.warning(f"⚠️ Could not register top performers handlers: {e}")
    
    # Add group posting buy button handler (only if available)
    if GROUP_POSTER_AVAILABLE and group_poster:
        app.add_handler(CallbackQueryHandler(
            group_poster.handle_buy_button_click,
            pattern='^buy_'
        ))
    
    # Add handlers for automatic group detection (always enabled)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added_to_group))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_bot_removed_from_group))
    app.add_handler(ChatMemberHandler(on_my_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))

    logger.info(f"✅ Bot username: @{BOT_USERNAME}")
    logger.info("✅ Database initialized")
    logger.info("✅ Automatic group detection ENABLED")
    logger.info("✅ Group posting will auto-enable when bot is added to groups")

    # Check payment wallet configuration (use global payment_wallet)
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
            
            # Connect payment monitor to sponsorship processor
            if auto_sponsor:
                async def on_payment_detected(payment_data):
                    """Handle incoming USDC payments"""
                    await auto_sponsor.process_payment(payment_data)
                
                payment_monitor.on_payment_received = on_payment_detected
            
            payment_monitor_task = asyncio.create_task(payment_monitor.start_monitoring())
            logger.info("💰 Payment monitor started - auto-upgrades & sponsorships enabled!")
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



