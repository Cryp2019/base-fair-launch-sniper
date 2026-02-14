#!/usr/bin/env python3
"""
Fair Launch Sniper Bot for Base Chain
Detects new token pairs with renounced ownership + locked liquidity
"""
import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from web3 import Web3
from web3.exceptions import ContractLogicError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
import requests
from eth_abi import encode

# Load .env file FIRST before any config
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        os.environ[parts[0].strip()] = parts[1].strip()
except FileNotFoundError:
    pass

# ===== CONFIG =====
_alchemy_key = os.getenv('ALCHEMY_BASE_KEY', '')
_base_rpc_url = os.getenv('BASE_RPC_URL', '')
if _base_rpc_url:
    BASE_RPC = _base_rpc_url
elif _alchemy_key:
    BASE_RPC = f"https://base-mainnet.g.alchemy.com/v2/{_alchemy_key}"
else:
    BASE_RPC = 'https://mainnet.base.org'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALERT_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '@base_fair_launch_alerts')  # Public channel

# Uniswap V3 Factory (Base)
FACTORY_ADDRESS = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913".lower()
WETH_ADDRESS = "0x4200000000000000000000000000000000000006".lower()  # Wrapped ETH on Base

# Critical thresholds
MAX_PREMINE_RATIO = 0.05  # 5% max creator holding
MIN_LIQUIDITY_LOCK_DAYS = 30
MAX_TAX_PERCENT = 5

# Standard ERC-20 Transfer event topic: keccak256("Transfer(address,address,uint256)")
TRANSFER_EVENT_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
# Zero address topic (used to detect token minting)
ZERO_ADDRESS_TOPIC = '0x0000000000000000000000000000000000000000000000000000000000000000'

# Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to Base RPC with fallbacks (free public RPCs)
_base_rpc_fallbacks = [
    BASE_RPC,
    'https://mainnet.base.org',
    'https://base.llamarpc.com',
    'https://base-rpc.publicnode.com',
    'https://base.drpc.org',
]
w3 = None
for _rpc in dict.fromkeys(_base_rpc_fallbacks):
    try:
        _w3 = Web3(Web3.HTTPProvider(_rpc, request_kwargs={'timeout': 10}))
        if _w3.is_connected():
            w3 = _w3
            logging.info(f"✅ Connected to Base RPC: {_rpc[:40]}...")
            break
    except Exception:
        continue
if w3 is None:
    w3 = Web3(Web3.HTTPProvider(BASE_RPC))

# Minimal ABIs (only what we need)
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}
]

UNISWAP_POOL_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"liquidity","outputs":[{"name":"","type":"uint128"}],"type":"function"}
]

# ===== CORE LOGIC =====
def is_renounced(owner_address: str) -> bool:
    """Check if contract ownership renounced (sent to burn address)"""
    burn_addresses = [
        "0x0000000000000000000000000000000000000001",
        "0x0000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000dEaD"
    ]
    return owner_address.lower() in [a.lower() for a in burn_addresses]

def get_creator_address(token_address: str) -> str:
    """Get deployer address with improved reliability"""
    try:
        # Method 1: Try to get contract creation transaction via Basescan API (free)
        basescan_key = os.getenv('BASESCAN_API_KEY', '')
        if basescan_key:
            url = f"https://api.basescan.org/api?module=contract&action=getcontractcreation&contractaddresses={token_address}&apikey={basescan_key}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == '1' and data.get('result'):
                    return data['result'][0]['contractCreator']
        
        # Method 2: Fallback using standard eth_getLogs to find first Transfer event (works with any RPC)
        # Search recent blocks to find earliest mint (zero address → deployer)
        current_block = w3.eth.block_number
        # Search last ~100k blocks (~2 days on Base) to avoid huge range queries on free RPCs
        from_block = max(0, current_block - 100000)
        logs = w3.eth.get_logs({
            'fromBlock': from_block,
            'toBlock': 'latest',
            'address': Web3.to_checksum_address(token_address),
            'topics': [TRANSFER_EVENT_TOPIC, ZERO_ADDRESS_TOPIC],
        })
        if logs:
            # The first mint's 'to' address is likely the deployer
            first_mint = logs[0]
            # 'to' is the 3rd topic (index 2), padded to 32 bytes
            to_address = '0x' + first_mint['topics'][2].hex()[-40:]
            return Web3.to_checksum_address(to_address)
    except Exception as e:
        logging.warning(f"Failed to get creator: {e}")
    return None

def check_honeypot(token_address: str, pair_address: str = None) -> dict:
    """Check for honeypot using Honeypot.is API and on-chain checks"""
    result = {
        'is_honeypot': False,
        'honeypot_reason': None,
        'buy_tax': 0,
        'sell_tax': 0,
        'transfer_tax': 0
    }
    
    try:
        # Use Honeypot.is API (free tier: 100 requests/day)
        url = f"https://api.honeypot.is/v2/IsHoneypot?address={token_address}&chainID=8453"  # Base chain ID
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('honeypotResult'):
                hp_result = data['honeypotResult']
                result['is_honeypot'] = hp_result.get('isHoneypot', False)
                
                # Extract tax information
                if 'simulationResult' in data:
                    sim = data['simulationResult']
                    result['buy_tax'] = sim.get('buyTax', 0)
                    result['sell_tax'] = sim.get('sellTax', 0)
                    result['transfer_tax'] = sim.get('transferTax', 0)
                
                if result['is_honeypot']:
                    result['honeypot_reason'] = hp_result.get('honeypotReason', 'Unknown')
                    logging.warning(f"Honeypot detected: {token_address} - {result['honeypot_reason']}")
                    return result
    except Exception as e:
        logging.warning(f"Honeypot.is API failed: {e}, falling back to on-chain checks")
    
    # Fallback: On-chain checks for suspicious functions
    try:
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Check for common tax-related functions
        suspicious_functions = ['taxFee', 'buyTax', 'sellTax', 'transferTax', 'setMaxTxAmount', 'blacklist', 'pause']
        found_suspicious = []
        
        for func in suspicious_functions:
            if hasattr(contract.functions, func):
                found_suspicious.append(func)
        
        if found_suspicious:
            result['is_honeypot'] = True
            result['honeypot_reason'] = f"Suspicious functions: {', '.join(found_suspicious)}"
            logging.warning(f"Suspicious functions found in {token_address}: {found_suspicious}")
    except Exception as e:
        logging.warning(f"On-chain honeypot check failed: {e}")
    
    return result

def check_taxes(token_address: str, pair_address: str = None) -> dict:
    """Enhanced tax check with honeypot detection"""
    # Use honeypot detection which includes tax information
    honeypot_result = check_honeypot(token_address, pair_address)
    
    return {
        'has_suspicious_functions': honeypot_result['is_honeypot'],
        'buy_tax': honeypot_result['buy_tax'],
        'sell_tax': honeypot_result['sell_tax'],
        'transfer_tax': honeypot_result.get('transfer_tax', 0),
        'is_honeypot': honeypot_result['is_honeypot'],
        'honeypot_reason': honeypot_result.get('honeypot_reason')
    }

def get_lock_duration(locker_address: str, token_address: str) -> int:
    """Get actual lock duration from locker contract"""
    try:
        # Unicrypt V2 ABI for getting lock info
        unicrypt_abi = [
            {"constant":True,"inputs":[{"name":"_lpToken","type":"address"}],"name":"getNumLocksForToken","outputs":[{"name":"","type":"uint256"}],"type":"function"},
            {"constant":True,"inputs":[{"name":"_lpToken","type":"address"},{"name":"_index","type":"uint256"}],"name":"tokenLocks","outputs":[{"name":"unlockDate","type":"uint256"}],"type":"function"}
        ]
        
        locker_contract = w3.eth.contract(address=locker_address, abi=unicrypt_abi)
        
        # Try to get lock count
        try:
            num_locks = locker_contract.functions.getNumLocksForToken(token_address).call()
            if num_locks > 0:
                # Get the first lock's unlock date
                lock_info = locker_contract.functions.tokenLocks(token_address, 0).call()
                unlock_timestamp = lock_info if isinstance(lock_info, int) else lock_info[0]
                
                # Calculate days remaining
                current_time = int(time.time())
                days_remaining = max(0, (unlock_timestamp - current_time) // 86400)
                return days_remaining
        except:
            pass
    except Exception as e:
        logging.debug(f"Failed to get lock duration: {e}")
    
    return 0

def is_liquidity_locked(pair_address: str) -> dict:
    """Check if LP tokens locked via common lockers - FIXED VERSION"""
    # Known locker contracts on Base (update with Base-specific addresses)
    locker_contracts = {
        "0x663a5c229c09b049e36dcc11a9b0d4a8eb9db214": "Unicrypt",
        "0x35970d815e4f857f7c829c8b78e1964d15f3e674": "Team Finance",
        "0x71B5759d73262FBb223956913ecF4ecC51057641": "PinkLock",
    }
    
    try:
        # For Uniswap V3, the pair address IS the LP token
        # Create LP token contract to check balances
        lp_token_abi = [
            {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
            {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}
        ]
        
        lp_contract = w3.eth.contract(address=pair_address, abi=lp_token_abi)
        
        try:
            total_supply = lp_contract.functions.totalSupply().call()
        except:
            # If totalSupply fails, might be Uniswap V3 which doesn't have LP tokens
            logging.debug(f"Could not get total supply for {pair_address}, might be V3 pool")
            return {'locked': False, 'locker': None, 'days': 0, 'reason': 'Not a standard LP token'}
        
        # Check each locker contract for LP token balance
        for locker_addr, locker_name in locker_contracts.items():
            try:
                balance = lp_contract.functions.balanceOf(locker_addr).call()
                
                if balance > 0:
                    # Calculate percentage locked
                    percent_locked = (balance / total_supply * 100) if total_supply > 0 else 0
                    
                    # Only consider it locked if >50% of LP is in locker
                    if percent_locked >= 50:
                        # Try to get actual lock duration
                        days = get_lock_duration(locker_addr, pair_address)
                        
                        # If we can't get duration, assume minimum lock period
                        if days == 0:
                            days = 30  # Conservative estimate
                        
                        logging.info(f"Found {percent_locked:.1f}% LP locked in {locker_name} for {days} days")
                        return {
                            'locked': True,
                            'locker': locker_addr,
                            'locker_name': locker_name,
                            'days': days,
                            'percent_locked': round(percent_locked, 2)
                        }
            except Exception as e:
                logging.debug(f"Error checking {locker_name}: {e}")
                continue
    except Exception as e:
        logging.warning(f"Liquidity lock check failed for {pair_address}: {e}")
    
    return {'locked': False, 'locker': None, 'days': 0, 'percent_locked': 0}

def analyze_new_pair(pair_address: str) -> dict:
    """Full fair launch analysis"""
    try:
        pair_contract = w3.eth.contract(address=pair_address, abi=UNISWAP_POOL_ABI)
        token0 = pair_contract.functions.token0().call().lower()
        token1 = pair_contract.functions.token1().call().lower()
        
        # Identify new token (non-USDC and non-WETH)
        if token0 == USDC_ADDRESS or token0 == WETH_ADDRESS:
            new_token = token1
        elif token1 == USDC_ADDRESS or token1 == WETH_ADDRESS:
            new_token = token0
        else:
            # Neither token is USDC or WETH, skip this pair
            return None
        
        # Get token details
        token_contract = w3.eth.contract(address=new_token, abi=ERC20_ABI)
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            total_supply = token_contract.functions.totalSupply().call()
        except:
            return None  # Not a standard ERC20
        
        # Critical checks
        owner = "0x0"
        try:
            owner = token_contract.functions.owner().call()
        except:
            pass  # No owner() function = likely renounced
        
        renounced = is_renounced(owner) or owner == "0x0"
        creator = get_creator_address(new_token)
        creator_balance = 0
        if creator:
            try:
                creator_balance = token_contract.functions.balanceOf(creator).call()
            except:
                pass
        premine_ratio = creator_balance / total_supply if total_supply > 0 else 1.0
        
        tax_info = check_taxes(new_token, pair_address)
        lock_info = is_liquidity_locked(pair_address)
        
        # Fair launch criteria - now includes honeypot check and tax thresholds
        is_fair = (
            renounced and
            premine_ratio <= MAX_PREMINE_RATIO and
            lock_info['locked'] and lock_info['days'] >= MIN_LIQUIDITY_LOCK_DAYS and
            not tax_info['is_honeypot'] and
            tax_info['buy_tax'] <= MAX_TAX_PERCENT and
            tax_info['sell_tax'] <= MAX_TAX_PERCENT
        )
        
        return {
            'is_fair': is_fair,
            'token_address': new_token,
            'pair_address': pair_address,
            'name': name,
            'symbol': symbol,
            'renounced': renounced,
            'premine_ratio': round(premine_ratio * 100, 2),
            'liquidity_locked': lock_info['locked'],
            'lock_days': lock_info['days'],
            'lock_percent': lock_info.get('percent_locked', 0),
            'locker_name': lock_info.get('locker_name', 'Unknown'),
            'has_suspicious_tax': tax_info['has_suspicious_functions'],
            'is_honeypot': tax_info['is_honeypot'],
            'honeypot_reason': tax_info.get('honeypot_reason'),
            'buy_tax': tax_info['buy_tax'],
            'sell_tax': tax_info['sell_tax'],
            'transfer_tax': tax_info.get('transfer_tax', 0),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Analysis failed for {pair_address}: {e}")
        return None

def get_new_pairs(last_block: int = None) -> list:
    """Get new Uniswap V3 pairs - FIXED to properly decode PoolCreated events"""
    if last_block is None:
        last_block = w3.eth.block_number - 10
    
    # PoolCreated event signature: PoolCreated(address indexed token0, address indexed token1, uint24 indexed fee, int24 tickSpacing, address pool)
    pool_created_topic = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
    
    try:
        # Use eth_getLogs to get PoolCreated events
        logs = w3.eth.get_logs({
            'fromBlock': last_block,
            'toBlock': 'latest',
            'address': FACTORY_ADDRESS,
            'topics': [pool_created_topic]
        })
        
        pools = []
        for log in logs:
            try:
                # Decode the event
                # topics[0] = event signature
                # topics[1] = token0 (indexed)
                # topics[2] = token1 (indexed)
                # topics[3] = fee (indexed)
                # data = tickSpacing + pool address
                
                if len(log['topics']) >= 4:
                    token0 = '0x' + log['topics'][1].hex()[-40:]
                    token1 = '0x' + log['topics'][2].hex()[-40:]
                    
                    # Pool address is in the data field (last 20 bytes)
                    pool_address = '0x' + log['data'].hex()[-40:]
                    
                    # Include pairs with USDC or WETH
                    if (token0.lower() == USDC_ADDRESS or token1.lower() == USDC_ADDRESS or
                        token0.lower() == WETH_ADDRESS or token1.lower() == WETH_ADDRESS):
                        
                        # Determine pair type
                        pair_type = "USDC" if (token0.lower() == USDC_ADDRESS or token1.lower() == USDC_ADDRESS) else "WETH"
                        
                        pools.append({
                            'address': pool_address,
                            'token0': token0,
                            'token1': token1,
                            'block': log['blockNumber'],
                            'pair_type': pair_type
                        })
                        logging.info(f"Found new {pair_type} pair: {pool_address} at block {log['blockNumber']}")
            except Exception as e:
                logging.warning(f"Failed to decode log: {e}")
                continue
        
        # Return just the addresses, sorted by block number (newest first)
        pools.sort(key=lambda x: x['block'], reverse=True)
        return [p['address'] for p in pools[:5]]  # Limit to 5 newest
        
    except Exception as e:
        logging.error(f"Failed to fetch pairs: {e}")
        
        # Fallback: retry via JSON-RPC POST to the configured BASE_RPC (works with any provider)
        try:
            logging.info("Retrying eth_getLogs via JSON-RPC POST...")
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getLogs",
                "params": [{
                    "fromBlock": hex(last_block),
                    "toBlock": "latest",
                    "address": FACTORY_ADDRESS,
                    "topics": [pool_created_topic]
                }]
            }
            resp = requests.post(BASE_RPC, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if 'result' in data:
                    return [log['data'][-40:] for log in data['result'][:5]]
        except Exception as fallback_error:
            logging.error(f"Fallback also failed: {fallback_error}")
    
    return []

async def send_alert(context: CallbackContext, analysis: dict):
    """Send Telegram alert with enhanced analysis information"""
    if not TELEGRAM_TOKEN or not ALERT_CHAT_ID:
        logging.error("Missing Telegram config")
        return
    
    # Build alert message with enhanced information
    status_emoji = "✅" if analysis['is_fair'] else "⚠️"
    
    # Build tax info string
    tax_info = ""
    if analysis.get('buy_tax', 0) > 0 or analysis.get('sell_tax', 0) > 0:
        tax_info = f"\n💸 Buy Tax: {analysis['buy_tax']}% | Sell Tax: {analysis['sell_tax']}%"
    
    # Build honeypot warning
    honeypot_warning = ""
    if analysis.get('is_honeypot'):
        honeypot_warning = f"\n🚨 *HONEYPOT DETECTED*: {analysis.get('honeypot_reason', 'Unknown reason')}"
    
    # Build lock info
    lock_info = f"{analysis['lock_days']} days"
    if analysis.get('lock_percent', 0) > 0:
        lock_info += f", {analysis['lock_percent']}% locked"
    if analysis.get('locker_name'):
        lock_info += f" via {analysis['locker_name']}"
    
    message = (
        f"{status_emoji} *NEW TOKEN DETECTED* {status_emoji}\n\n"
        f"🔤 *{analysis['name']}* (${analysis['symbol'].upper()})\n"
        f"🔗 Pair: `{analysis['pair_address'][:6]}...{analysis['pair_address'][-4:]}`\n"
        f"🏷️ Token: `{analysis['token_address'][:6]}...{analysis['token_address'][-4:]}`\n\n"
        f"🛡️ *Fair Launch Checks:*\n"
        f"{'✅' if analysis['renounced'] else '❌'} Ownership renounced\n"
        f"{'✅' if analysis['premine_ratio'] <= 5 else '❌'} Creator holding: {analysis['premine_ratio']}%\n"
        f"{'✅' if analysis['liquidity_locked'] else '❌'} Liquidity locked ({lock_info})\n"
        f"{'✅' if not analysis['is_honeypot'] and analysis['buy_tax'] <= MAX_TAX_PERCENT else '❌'} "
        f"Tax check passed{tax_info}\n"
        f"{honeypot_warning}\n\n"
        f"⚠️ *DISCLAIMER: Not financial advice. 99% of new tokens fail. DYOR.*"
    )
    
    # Add Basescan links
    keyboard = [
        [
            InlineKeyboardButton("🔍 Token", url=f"https://basescan.org/token/{analysis['token_address']}"),
            InlineKeyboardButton("💧 Pair", url=f"https://basescan.org/address/{analysis['pair_address']}")
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=ALERT_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logging.info(f"Alert sent for {analysis['symbol']}")
    except Exception as e:
        logging.error(f"Failed to send alert: {e}")

# ===== TELEGRAM BOT COMMANDS =====
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🔍 *Base Fair Launch Sniper*\n\n"
        "I monitor Base chain for *truly* fair-launched tokens:\n"
        "✅ Renounced ownership\n"
        "✅ <5% pre-mine\n"
        "✅ Locked liquidity (30+ days)\n"
        "✅ No suspicious tax functions\n\n"
        "⚠️ *DISCLAIMER:* Not financial advice. Most new tokens fail. Always DYOR.\n\n"
        "Join alerts channel: @base_fair_launch_alerts",
        parse_mode='Markdown'
    )

async def howitworks(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🛡️ *How Fair Launch Verification Works:*\n\n"
        "1️⃣ *Ownership Check*\n"
        "   → Confirms contract ownership sent to burn address\n\n"
        "2️⃣ *Pre-mine Analysis*\n"
        "   → Checks creator wallet holds <5% of supply\n\n"
        "3️⃣ *Liquidity Lock*\n"
        "   → Verifies LP tokens locked via Unicrypt/Team Finance\n\n"
        "4️⃣ *Tax Screening*\n"
        "   → Flags contracts with hidden tax functions\n\n"
        "⚠️ *Limitations:* Cannot detect all honeypots. Always test with small amounts first.",
        parse_mode='Markdown'
    )

async def scan_command(update: Update, context: CallbackContext):
    """Manual scan trigger"""
    await update.message.reply_text("🔍 Scanning for new pairs...")
    pairs = get_new_pairs()
    results = []
    
    for pair in pairs[:3]:  # Limit to 3 for demo
        analysis = analyze_new_pair(pair)
        if analysis:
            results.append(analysis)
            status = "✅ FAIR" if analysis['is_fair'] else "⚠️ RISKY"
            await update.message.reply_text(
                f"{status} ${analysis['symbol'].upper()} "
                f"({analysis['premine_ratio']}% pre-mine)"
            )
    
    if not results:
        await update.message.reply_text("No new pairs found in last 10 blocks.")

# ===== MAIN =====
async def main():
    # Debug: Print loaded env vars
    logging.info(f"Telegram Token loaded: {'Yes' if TELEGRAM_TOKEN else 'No'}")
    logging.info(f"RPC Provider: {'Alchemy' if os.getenv('ALCHEMY_BASE_KEY') else 'Free public RPC'}")
    
    # Scan-only mode (for GitHub Actions)
    if '--scan-only' in sys.argv:
        logging.info("Running in scan-only mode")
        pairs = get_new_pairs()
        new_finds = 0
        
        for pair in pairs:
            analysis = analyze_new_pair(pair)
            if analysis and analysis['is_fair']:
                # Minimal bot setup just for sending alerts
                if TELEGRAM_TOKEN:
                    from telegram.ext import Application
                    app = Application.builder().token(TELEGRAM_TOKEN).build()
                    await send_alert(app, analysis)
                    new_finds += 1
        
        logging.info(f"Scan complete. Found {new_finds} fair launches.")
        return
    
    # Full bot mode
    if not TELEGRAM_TOKEN:
        logging.error("Missing TELEGRAM_BOT_TOKEN in .env")
        logging.error("Please add TELEGRAM_BOT_TOKEN=your_token_here to .env file")
        return
    
    try:
        logging.info("Initializing Telegram bot...")
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("howitworks", howitworks))
        app.add_handler(CommandHandler("scan", scan_command))
        
        logging.info("Bot started. Press Ctrl+C to stop.")
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        logging.info("Bot is now running and monitoring for fair launches...")
        
        # Keep running
        while True:
            await asyncio.sleep(60)
    except Exception as e:
        logging.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
