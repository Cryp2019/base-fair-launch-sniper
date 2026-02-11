"""
On-Chain Token Analyzer for Base Chain
Soul Scanner-style analytics: holders, bundles, snipers, dev wallet, whale classification
Uses ERC20 Transfer event logs via Web3/Alchemy
"""
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from web3 import Web3

logger = logging.getLogger(__name__)

# ERC20 Transfer event topic
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
DEAD_ADDRESSES = [
    '0x0000000000000000000000000000000000000000',
    '0x0000000000000000000000000000000000000001',
    '0x000000000000000000000000000000000000dead',
]


class OnChainAnalyzer:
    def __init__(self, w3: Web3):
        self.w3 = w3
    
    def _get_transfer_logs(self, token_address: str, from_block: int = 0, to_block: str = 'latest', max_blocks: int = 50000) -> list:
        """Fetch Transfer event logs for a token (respecting Alchemy block range limits)"""
        token = Web3.to_checksum_address(token_address)
        current_block = self.w3.eth.block_number
        
        if to_block == 'latest':
            to_block = current_block
        
        # Limit range to avoid RPC errors (Alchemy allows ~2000 blocks per request)
        if from_block == 0:
            from_block = max(0, to_block - max_blocks)
        
        all_logs = []
        chunk_size = 2000  # Alchemy-safe chunk size
        
        block = from_block
        while block < to_block:
            end = min(block + chunk_size, to_block)
            try:
                logs = self.w3.eth.get_logs({
                    'fromBlock': hex(block),
                    'toBlock': hex(end),
                    'address': token,
                    'topics': [TRANSFER_TOPIC]
                })
                all_logs.extend(logs)
            except Exception as e:
                logger.warning(f"Error fetching logs {block}-{end}: {e}")
                # Try smaller chunk
                chunk_size = max(500, chunk_size // 2)
            block = end + 1
        
        return all_logs
    
    def _parse_transfer(self, log) -> dict:
        """Parse a Transfer event log"""
        from_addr = '0x' + log['topics'][1].hex()[-40:]
        to_addr = '0x' + log['topics'][2].hex()[-40:]
        amount = int(log['data'].hex(), 16) if log['data'] else 0
        return {
            'from': from_addr.lower(),
            'to': to_addr.lower(),
            'amount': amount,
            'block': log['blockNumber'],
            'tx_hash': log['transactionHash'].hex(),
            'log_index': log['logIndex']
        }
    
    def _get_deployer(self, token_address: str) -> Optional[str]:
        """Find the contract deployer address"""
        try:
            token = Web3.to_checksum_address(token_address)
            # The deployer is the 'from' of the first Transfer (mint) from 0x0
            logs = self.w3.eth.get_logs({
                'fromBlock': '0x0',
                'toBlock': 'latest',
                'address': token,
                'topics': [
                    TRANSFER_TOPIC,
                    '0x' + '0' * 64  # from = zero address (mint)
                ]
            })
            if logs:
                first_mint = self._parse_transfer(logs[0])
                return first_mint['to']
        except Exception as e:
            logger.warning(f"Could not find deployer: {e}")
        
        # Fallback: try to get contract creator from creation tx
        try:
            # Use eth_getCode to verify it's a contract, then check first tx
            code = self.w3.eth.get_code(Web3.to_checksum_address(token_address))
            if code:
                # Try basescan-style: first Transfer from zero address
                pass
        except:
            pass
        
        return None
    
    def get_holders_info(self, token_address: str, transfers: list = None, total_supply: int = 0, decimals: int = 18) -> dict:
        """Calculate holder count and top holder percentage from Transfer events"""
        if transfers is None:
            transfers = self._get_all_transfers(token_address)
        
        # Build balance map from transfers
        balances = defaultdict(int)
        for tx in transfers:
            balances[tx['from']] -= tx['amount']
            balances[tx['to']] += tx['amount']
        
        # Remove zero/dead addresses and zero balances
        holders = {}
        for addr, bal in balances.items():
            if bal > 0 and addr.lower() not in [a.lower() for a in DEAD_ADDRESSES]:
                holders[addr] = bal
        
        holder_count = len(holders)
        
        # Find top holder
        top_pct = 0
        if holders and total_supply > 0:
            top_balance = max(holders.values())
            top_pct = (top_balance / total_supply) * 100
        elif holders:
            total = sum(holders.values())
            top_balance = max(holders.values())
            top_pct = (top_balance / total) * 100 if total > 0 else 0
        
        return {
            'holder_count': holder_count,
            'top_holder_pct': round(top_pct, 1),
            'balances': holders
        }
    
    def detect_bundles(self, transfers: list, pair_address: str = None) -> dict:
        """Detect bundled wallets (multiple buys in same block/tx from related wallets)"""
        # Group buys by block number
        buys_by_block = defaultdict(list)
        total_bought = 0
        
        for tx in transfers:
            if tx['from'].lower() in [a.lower() for a in DEAD_ADDRESSES]:
                continue  # Skip mints
            if tx['to'].lower() in [a.lower() for a in DEAD_ADDRESSES]:
                continue  # Skip burns
            # A "buy" is a transfer TO a non-pair address FROM a pair address
            if pair_address and tx['from'].lower() == pair_address.lower():
                buys_by_block[tx['block']].append(tx)
                total_bought += tx['amount']
        
        # If no pair address, use heuristic: group by block for all transfers from zero
        if not pair_address:
            for tx in transfers:
                if tx['from'].lower() == ZERO_ADDRESS.lower():
                    buys_by_block[tx['block']].append(tx)
                    total_bought += tx['amount']
        
        # Blocks with 2+ unique buyers = potential bundles
        bundle_wallets = set()
        bundle_count = 0
        bundle_initial_pct = 0
        
        for block_num, block_buys in buys_by_block.items():
            unique_buyers = set(tx['to'] for tx in block_buys)
            if len(unique_buyers) >= 2:
                bundle_count += 1
                bundle_wallets.update(unique_buyers)
                if total_bought > 0:
                    block_amount = sum(tx['amount'] for tx in block_buys)
                    bundle_initial_pct += (block_amount / total_bought) * 100
        
        # Calculate current holdings of bundle wallets
        bundle_current_pct = 0
        # (calculated later when we have balances)
        
        return {
            'bundle_count': len(bundle_wallets),
            'bundle_initial_pct': round(bundle_initial_pct, 1),
            'bundle_current_pct': 0,  # Will be calculated with balances
            'bundle_wallets': list(bundle_wallets)
        }
    
    def detect_snipers(self, transfers: list, pair_address: str = None) -> dict:
        """Detect snipers (buyers in the first 2 blocks after pool creation)"""
        if not transfers:
            return {'sniper_count': 0, 'sniper_initial_pct': 0, 'sniper_current_pct': 0, 'sniper_wallets': []}
        
        # Find earliest block (pool creation / first buy)
        buy_blocks = sorted(set(tx['block'] for tx in transfers))
        if not buy_blocks:
            return {'sniper_count': 0, 'sniper_initial_pct': 0, 'sniper_current_pct': 0, 'sniper_wallets': []}
        
        first_block = buy_blocks[0]
        sniper_window = first_block + 2  # First 2 blocks
        
        sniper_wallets = set()
        sniper_amount = 0
        total_amount = sum(tx['amount'] for tx in transfers if tx['from'].lower() in [a.lower() for a in DEAD_ADDRESSES] or (pair_address and tx['from'].lower() == pair_address.lower()))
        
        for tx in transfers:
            if tx['block'] <= sniper_window:
                # Sniper = bought in first 2 blocks
                if tx['from'].lower() in [a.lower() for a in DEAD_ADDRESSES] or (pair_address and tx['from'].lower() == pair_address.lower()):
                    sniper_wallets.add(tx['to'])
                    sniper_amount += tx['amount']
        
        sniper_initial_pct = (sniper_amount / total_amount * 100) if total_amount > 0 else 0
        
        return {
            'sniper_count': len(sniper_wallets),
            'sniper_initial_pct': round(sniper_initial_pct, 1),
            'sniper_current_pct': 0,  # Calculated with balances
            'sniper_wallets': list(sniper_wallets)
        }
    
    def get_first_20_buyers(self, transfers: list, pair_address: str = None) -> dict:
        """Analyze the first 20 unique buyers"""
        seen = set()
        first_20 = []
        total_first_20_amount = 0
        bundle_in_first_20 = 0
        
        for tx in sorted(transfers, key=lambda x: (x['block'], x['log_index'])):
            buyer = tx['to']
            if buyer.lower() in [a.lower() for a in DEAD_ADDRESSES]:
                continue
            if buyer not in seen:
                seen.add(buyer)
                first_20.append({
                    'address': buyer,
                    'amount': tx['amount'],
                    'block': tx['block']
                })
                total_first_20_amount += tx['amount']
                if len(first_20) >= 20:
                    break
        
        # Check for bundles in first 20 (same block = bundle)
        blocks_seen = defaultdict(int)
        for buyer in first_20:
            blocks_seen[buyer['block']] += 1
        
        for buyer in first_20:
            if blocks_seen[buyer['block']] >= 2:
                bundle_in_first_20 += 1
        
        total_supply_approx = sum(tx['amount'] for tx in transfers if tx['from'].lower() == ZERO_ADDRESS.lower())
        first_20_pct = (total_first_20_amount / total_supply_approx * 100) if total_supply_approx > 0 else 0
        bundle_pct = (sum(b['amount'] for b in first_20 if blocks_seen[b['block']] >= 2) / total_supply_approx * 100) if total_supply_approx > 0 else 0
        
        return {
            'first_20_pct': round(first_20_pct, 1),
            'bundle_in_first_20': bundle_in_first_20,
            'bundle_pct': round(bundle_pct, 1),
            'buyers': first_20
        }
    
    def get_dev_info(self, token_address: str, transfers: list, total_supply: int = 0) -> dict:
        """Analyze the contract deployer/dev wallet"""
        deployer = self._get_deployer(token_address)
        
        if not deployer:
            return {
                'deployer': None,
                'deployer_short': 'Unknown',
                'balance_eth': 0,
                'holding_pct': 0,
                'bundled_pct': 0,
                'sold_pct': 0,
                'airdrop_pct': 0
            }
        
        # Get deployer ETH balance
        try:
            eth_balance = self.w3.eth.get_balance(Web3.to_checksum_address(deployer))
            eth_balance_formatted = eth_balance / 10**18
        except:
            eth_balance_formatted = 0
        
        # Calculate dev token stats from transfers
        dev_received = 0
        dev_sent = 0
        dev_sent_to_unique = set()
        
        for tx in transfers:
            if tx['to'].lower() == deployer.lower():
                dev_received += tx['amount']
            if tx['from'].lower() == deployer.lower():
                dev_sent += tx['amount']
                dev_sent_to_unique.add(tx['to'])
        
        # Current holding
        dev_holding = dev_received - dev_sent
        supply = total_supply if total_supply > 0 else sum(tx['amount'] for tx in transfers if tx['from'].lower() == ZERO_ADDRESS.lower())
        
        holding_pct = (dev_holding / supply * 100) if supply > 0 else 0
        sold_pct = (dev_sent / dev_received * 100) if dev_received > 0 else 0
        
        # Bundled = dev sent to multiple wallets in same block (airdrop/bundle pattern)
        dev_sends_by_block = defaultdict(list)
        for tx in transfers:
            if tx['from'].lower() == deployer.lower():
                dev_sends_by_block[tx['block']].append(tx)
        
        bundled_amount = 0
        airdrop_amount = 0
        for block_num, block_sends in dev_sends_by_block.items():
            if len(block_sends) >= 3:
                # 3+ sends in one block = airdrop
                airdrop_amount += sum(tx['amount'] for tx in block_sends)
            elif len(block_sends) >= 2:
                # 2 sends in one block = bundle
                bundled_amount += sum(tx['amount'] for tx in block_sends)
        
        bundled_pct = (bundled_amount / supply * 100) if supply > 0 else 0
        airdrop_pct = (airdrop_amount / supply * 100) if supply > 0 else 0
        
        return {
            'deployer': deployer,
            'deployer_short': f"{deployer[:6]}...{deployer[-4:]}" if deployer else 'Unknown',
            'balance_eth': round(eth_balance_formatted, 2),
            'holding_pct': round(holding_pct, 1),
            'bundled_pct': round(bundled_pct, 1),
            'sold_pct': round(sold_pct, 1),
            'airdrop_pct': round(airdrop_pct, 1)
        }
    
    def classify_holders(self, balances: dict, total_supply: int = 0) -> dict:
        """Classify holders as Whale/Fish/Shrimp based on holding %"""
        if not balances:
            return {'whales': 0, 'fish': 0, 'shrimp': 0, 'icons': ''}
        
        total = total_supply if total_supply > 0 else sum(balances.values())
        if total == 0:
            return {'whales': 0, 'fish': 0, 'shrimp': 0, 'icons': ''}
        
        whales = 0   # > 2% of supply
        fish = 0     # 0.5% - 2%
        shrimp = 0   # < 0.5%
        
        for addr, bal in balances.items():
            pct = (bal / total) * 100
            if pct >= 2:
                whales += 1
            elif pct >= 0.5:
                fish += 1
            else:
                shrimp += 1
        
        # Build icon string (max 20 icons)
        icons = '🐳' * min(whales, 5) + '🐟' * min(fish, 7) + '🍤' * min(shrimp, 8)
        
        return {
            'whales': whales,
            'fish': fish,
            'shrimp': shrimp,
            'icons': icons
        }
    
    def _update_current_pct(self, wallet_set: set, balances: dict, total_supply: int) -> float:
        """Calculate current holding % for a set of wallets"""
        if not wallet_set or total_supply == 0:
            return 0
        total = sum(balances.get(w, 0) for w in wallet_set)
        return round((total / total_supply) * 100, 1)
    
    def _get_all_transfers(self, token_address: str) -> list:
        """Get all Transfer events, with fallback for RPC limits"""
        logs = self._get_transfer_logs(token_address)
        return [self._parse_transfer(log) for log in logs]
    
    def analyze_token_onchain(self, token_address: str, pair_address: str = None, total_supply: int = 0, decimals: int = 18) -> dict:
        """
        Master analysis function - runs all on-chain analytics.
        Returns a complete Soul Scanner-style analysis dict.
        """
        logger.info(f"🔍 Starting on-chain analysis for {token_address[:10]}...")
        start_time = time.time()
        
        try:
            # Fetch all transfers
            transfers = self._get_all_transfers(token_address)
            
            if not transfers:
                logger.warning(f"No transfers found for {token_address}")
                return self._empty_result()
            
            logger.info(f"  Found {len(transfers)} transfers")
            
            # Holders info
            holders = self.get_holders_info(token_address, transfers, total_supply, decimals)
            
            # Bundle detection
            bundles = self.detect_bundles(transfers, pair_address)
            
            # Sniper detection  
            snipers = self.detect_snipers(transfers, pair_address)
            
            # First 20 buyers
            first_20 = self.get_first_20_buyers(transfers, pair_address)
            
            # Dev wallet info
            dev = self.get_dev_info(token_address, transfers, total_supply)
            
            # Holder classification
            classification = self.classify_holders(holders.get('balances', {}), total_supply)
            
            # Update current percentages
            balances = holders.get('balances', {})
            supply = total_supply if total_supply > 0 else sum(balances.values())
            
            bundles['bundle_current_pct'] = self._update_current_pct(
                set(bundles.get('bundle_wallets', [])), balances, supply
            )
            snipers['sniper_current_pct'] = self._update_current_pct(
                set(snipers.get('sniper_wallets', [])), balances, supply
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✅ On-chain analysis complete in {elapsed:.1f}s")
            
            return {
                'holders': holders,
                'bundles': bundles,
                'snipers': snipers,
                'first_20': first_20,
                'dev': dev,
                'classification': classification,
                'transfer_count': len(transfers),
                'analysis_time': round(elapsed, 1)
            }
        
        except Exception as e:
            logger.error(f"On-chain analysis error: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result()
    
    def _empty_result(self) -> dict:
        """Return empty analysis result"""
        return {
            'holders': {'holder_count': 0, 'top_holder_pct': 0, 'balances': {}},
            'bundles': {'bundle_count': 0, 'bundle_initial_pct': 0, 'bundle_current_pct': 0, 'bundle_wallets': []},
            'snipers': {'sniper_count': 0, 'sniper_initial_pct': 0, 'sniper_current_pct': 0, 'sniper_wallets': []},
            'first_20': {'first_20_pct': 0, 'bundle_in_first_20': 0, 'bundle_pct': 0, 'buyers': []},
            'dev': {'deployer': None, 'deployer_short': 'Unknown', 'balance_eth': 0, 'holding_pct': 0, 'bundled_pct': 0, 'sold_pct': 0, 'airdrop_pct': 0},
            'classification': {'whales': 0, 'fish': 0, 'shrimp': 0, 'icons': ''},
            'transfer_count': 0,
            'analysis_time': 0
        }


def format_onchain_section_html(data: dict) -> str:
    """Format on-chain analysis data as HTML for group posts"""
    h = data.get('holders', {})
    b = data.get('bundles', {})
    s = data.get('snipers', {})
    f20 = data.get('first_20', {})
    dev = data.get('dev', {})
    cls = data.get('classification', {})
    
    # Emoji for sold %
    def sold_emoji(pct):
        if pct == 0: return '🤍'
        elif pct < 30: return '🟢'
        elif pct < 70: return '🟡'
        else: return '🔴'
    
    section = (
        f"━━━━━━━━━━━━━━━━\n"
        f"🔬 <b>ON-CHAIN ANALYSIS</b>\n"
        f"👥 Holders: <b>{h.get('holder_count', 0):,}</b> • Top: {h.get('top_holder_pct', 0)}%\n"
        f"📦 Bundles: {b.get('bundle_count', 0)} • {b.get('bundle_initial_pct', 0)}% → {b.get('bundle_current_pct', 0)}%\n"
        f"🎯 Snipers: {s.get('sniper_count', 0)} • {s.get('sniper_initial_pct', 0)}% → {s.get('sniper_current_pct', 0)}% {sold_emoji(s.get('sniper_current_pct', 0))}\n"
        f"🎯 First 20: {f20.get('first_20_pct', 0)}% | {f20.get('bundle_in_first_20', 0)} 📦 • {f20.get('bundle_pct', 0)}%\n"
    )
    
    # Classification icons
    if cls.get('icons'):
        section += f"{cls['icons']}\n"
    else:
        section += f"🐳{cls.get('whales', 0)} 🐟{cls.get('fish', 0)} 🍤{cls.get('shrimp', 0)}\n"
    
    # Dev info
    if dev.get('deployer'):
        section += (
            f"\n🛠️ Dev: <code>{dev.get('deployer_short', 'Unknown')}</code> • {dev.get('balance_eth', 0)} ETH • {dev.get('holding_pct', 0)}%\n"
            f"┣ Bundled: {dev.get('bundled_pct', 0)}% {sold_emoji(dev.get('bundled_pct', 0))} | Sold: {dev.get('sold_pct', 0)}% {sold_emoji(dev.get('sold_pct', 0))}\n"
            f"┗ Airdrop: {dev.get('airdrop_pct', 0)}% {sold_emoji(dev.get('airdrop_pct', 0))}\n"
        )
    else:
        section += f"\n🛠️ Dev: Unknown\n"
    
    return section


def format_onchain_section_markdown(data: dict) -> str:
    """Format on-chain analysis data as Markdown for DM alerts"""
    h = data.get('holders', {})
    b = data.get('bundles', {})
    s = data.get('snipers', {})
    f20 = data.get('first_20', {})
    dev = data.get('dev', {})
    cls = data.get('classification', {})
    
    def sold_emoji(pct):
        if pct == 0: return '🤍'
        elif pct < 30: return '🟢'
        elif pct < 70: return '🟡'
        else: return '🔴'
    
    section = (
        f"━━━━━━━━━━━━━━━━\n"
        f"🔬 *ON-CHAIN ANALYSIS*\n"
        f"👥 Holders: *{h.get('holder_count', 0):,}* • Top: {h.get('top_holder_pct', 0)}%\n"
        f"📦 Bundles: {b.get('bundle_count', 0)} • {b.get('bundle_initial_pct', 0)}% → {b.get('bundle_current_pct', 0)}%\n"
        f"🎯 Snipers: {s.get('sniper_count', 0)} • {s.get('sniper_initial_pct', 0)}% → {s.get('sniper_current_pct', 0)}% {sold_emoji(s.get('sniper_current_pct', 0))}\n"
        f"🎯 First 20: {f20.get('first_20_pct', 0)}% | {f20.get('bundle_in_first_20', 0)} 📦 • {f20.get('bundle_pct', 0)}%\n"
    )
    
    if cls.get('icons'):
        section += f"{cls['icons']}\n"
    else:
        section += f"🐳{cls.get('whales', 0)} 🐟{cls.get('fish', 0)} 🍤{cls.get('shrimp', 0)}\n"
    
    if dev.get('deployer'):
        section += (
            f"\n🛠️ Dev: `{dev.get('deployer_short', 'Unknown')}` • {dev.get('balance_eth', 0)} ETH • {dev.get('holding_pct', 0)}%\n"
            f"┣ Bundled: {dev.get('bundled_pct', 0)}% {sold_emoji(dev.get('bundled_pct', 0))} | Sold: {dev.get('sold_pct', 0)}% {sold_emoji(dev.get('sold_pct', 0))}\n"
            f"┗ Airdrop: {dev.get('airdrop_pct', 0)}% {sold_emoji(dev.get('airdrop_pct', 0))}\n"
        )
    else:
        section += f"\n🛠️ Dev: Unknown\n"
    
    return section
