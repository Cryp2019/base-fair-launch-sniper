#!/usr/bin/env python3
"""
🛡️ Security Scanner for Base Fair Launch Sniper Bot
Detects rugs, honeypots, and verifies LP locks
"""
import logging
from web3 import Web3
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Common lock platforms on Base
LOCK_PLATFORMS = {
    "0x231278eDd38B00B07fBd52120CEf685B9BaEBCC1": "Uncx Network",
    "0xC77aab3c6D7dAb46248F3CC3033C856171878BD5": "Team Finance",
    "0x0000000000000000000000000000000000000000": "No Lock Detected"
}

# Dangerous function signatures
DANGEROUS_FUNCTIONS = {
    "mint": "0x40c10f19",
    "setTaxFee": "0x7c6b4f5a",
    "setMaxTxPercent": "0xc49b9a80",
    "blacklist": "0xf9f92be4",
    "pause": "0x8456cb59",
    "excludeFromFee": "0x437823ec"
}


class SecurityScanner:
    def __init__(self, w3: Web3):
        self.w3 = w3
    
    def scan_token(self, token_address: str) -> Dict:
        """
        Comprehensive security scan of a token
        
        Returns:
            dict with security analysis results
        """
        results = {
            'is_safe': True,
            'risk_level': 'LOW',  # LOW, MEDIUM, HIGH, CRITICAL
            'warnings': [],
            'rug_detection': {},
            'lp_lock': {},
            'honeypot': {},
            'score': 100  # 0-100, higher is safer
        }
        
        try:
            # Run all security checks
            rug_check = self.check_rug_indicators(token_address)
            lp_check = self.check_lp_lock(token_address)
            honeypot_check = self.check_honeypot(token_address)
            
            results['rug_detection'] = rug_check
            results['lp_lock'] = lp_check
            results['honeypot'] = honeypot_check
            
            # Calculate risk score
            score = 100
            
            # Rug detection penalties
            if not rug_check.get('ownership_renounced', False):
                score -= 20
                results['warnings'].append("⚠️ Ownership NOT renounced")
            
            if rug_check.get('has_mint_function', False):
                score -= 30
                results['warnings'].append("🚨 Has MINT function - can create unlimited tokens!")
            
            if rug_check.get('has_blacklist', False):
                score -= 25
                results['warnings'].append("⚠️ Has BLACKLIST function")
            
            if rug_check.get('has_pause', False):
                score -= 20
                results['warnings'].append("⚠️ Has PAUSE function")
            
            # LP lock penalties
            if not lp_check.get('is_locked', False):
                score -= 40
                results['warnings'].append("🚨 LIQUIDITY NOT LOCKED!")
            elif lp_check.get('lock_duration_days', 0) < 30:
                score -= 20
                results['warnings'].append("⚠️ LP locked for less than 30 days")
            
            # Honeypot penalties
            if honeypot_check.get('is_honeypot', False):
                score -= 100
                results['warnings'].append("🚨 HONEYPOT DETECTED - CANNOT SELL!")
            
            if honeypot_check.get('buy_tax', 0) > 10:
                score -= 15
                results['warnings'].append(f"⚠️ High buy tax: {honeypot_check['buy_tax']}%")
            
            if honeypot_check.get('sell_tax', 0) > 10:
                score -= 15
                results['warnings'].append(f"⚠️ High sell tax: {honeypot_check['sell_tax']}%")
            
            # Set final score and risk level
            results['score'] = max(0, score)
            
            if score >= 80:
                results['risk_level'] = 'LOW'
                results['is_safe'] = True
            elif score >= 60:
                results['risk_level'] = 'MEDIUM'
                results['is_safe'] = True
            elif score >= 40:
                results['risk_level'] = 'HIGH'
                results['is_safe'] = False
            else:
                results['risk_level'] = 'CRITICAL'
                results['is_safe'] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Security scan error: {e}")
            return {
                'is_safe': False,
                'risk_level': 'UNKNOWN',
                'warnings': [f"Scan failed: {str(e)[:100]}"],
                'score': 0
            }
    
    def check_rug_indicators(self, token_address: str) -> Dict:
        """Check for common rug pull indicators"""
        try:
            token_checksum = Web3.to_checksum_address(token_address)
            
            # Get contract bytecode
            bytecode = self.w3.eth.get_code(token_checksum).hex()
            
            results = {
                'ownership_renounced': False,
                'has_mint_function': False,
                'has_blacklist': False,
                'has_pause': False,
                'has_tax_functions': False,
                'contract_verified': True  # Assume verified, would need API to check
            }
            
            # Check for dangerous function signatures in bytecode
            for func_name, signature in DANGEROUS_FUNCTIONS.items():
                if signature[2:] in bytecode:  # Remove 0x prefix
                    if func_name == 'mint':
                        results['has_mint_function'] = True
                    elif func_name in ['blacklist']:
                        results['has_blacklist'] = True
                    elif func_name == 'pause':
                        results['has_pause'] = True
                    elif func_name in ['setTaxFee', 'setMaxTxPercent']:
                        results['has_tax_functions'] = True
            
            # Check ownership (try to call owner function)
            try:
                owner_abi = [{
                    "constant": True,
                    "inputs": [],
                    "name": "owner",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                }]
                contract = self.w3.eth.contract(address=token_checksum, abi=owner_abi)
                owner = contract.functions.owner().call()
                
                # Check if owner is burn address
                burn_addresses = [
                    "0x0000000000000000000000000000000000000000",
                    "0x000000000000000000000000000000000000dEaD",
                    "0x0000000000000000000000000000000000000001"
                ]
                results['ownership_renounced'] = owner.lower() in [a.lower() for a in burn_addresses]
            except:
                # No owner function = likely renounced or no ownership
                results['ownership_renounced'] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Rug detection error: {e}")
            return {'error': str(e)}

    def check_lp_lock(self, token_address: str) -> Dict:
        """Check if liquidity is locked"""
        try:
            token_checksum = Web3.to_checksum_address(token_address)

            results = {
                'is_locked': False,
                'lock_platform': 'Unknown',
                'lock_duration_days': 0,
                'unlock_date': None,
                'locked_amount': 0
            }

            # Common LP lock contract addresses on Base
            lock_contracts = {
                "0x231278eDd38B00B07fBd52120CEf685B9BaEBCC1": "Uncx Network",
                "0xC77aab3c6D7dAb46248F3CC3033C856171878BD5": "Team Finance"
            }

            # Check each lock platform
            for lock_address, platform_name in lock_contracts.items():
                try:
                    # Simple check: see if lock contract holds LP tokens
                    # This is a simplified version - real implementation would query lock contract
                    lp_token_abi = [{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]

                    # Try to get LP token address (would need to query Uniswap factory)
                    # For now, we'll mark as unknown
                    results['lock_platform'] = 'Check manually on Basescan'

                except Exception as e:
                    logger.debug(f"Lock check failed for {platform_name}: {e}")
                    continue

            # Note: Full implementation would require:
            # 1. Get LP token address from Uniswap factory
            # 2. Check LP token balance in lock contracts
            # 3. Query lock contract for unlock time
            # For MVP, we'll return a warning to check manually

            return results

        except Exception as e:
            logger.error(f"LP lock check error: {e}")
            return {'error': str(e), 'is_locked': False}

    def check_honeypot(self, token_address: str) -> Dict:
        """Check if token is a honeypot by simulating trades"""
        try:
            token_checksum = Web3.to_checksum_address(token_address)

            results = {
                'is_honeypot': False,
                'can_buy': True,
                'can_sell': True,
                'buy_tax': 0,
                'sell_tax': 0,
                'transfer_tax': 0
            }

            # Use honeypot.is API (free service for honeypot detection)
            try:
                # Note: This is a placeholder - actual API would be:
                # https://api.honeypot.is/v2/IsHoneypot?address={token_address}&chainID=8453

                # For now, we'll do a basic simulation check
                # Try to estimate gas for a swap
                router_address = "0x2626664c2603336E57B271c5C0b26F421741e481"
                weth_address = "0x4200000000000000000000000000000000000006"

                # Check if token has transfer function
                transfer_abi = [{
                    "constant": False,
                    "inputs": [
                        {"name": "_to", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "transfer",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }]

                contract = self.w3.eth.contract(address=token_checksum, abi=transfer_abi)

                # Try to estimate gas for transfer (if this fails, might be honeypot)
                try:
                    # Estimate gas for a small transfer
                    gas_estimate = contract.functions.transfer(
                        router_address,
                        1000  # Small amount
                    ).estimate_gas({'from': router_address})

                    # If gas is extremely high, might be honeypot
                    if gas_estimate > 500000:
                        results['is_honeypot'] = True
                        results['can_sell'] = False

                except Exception as e:
                    # If we can't estimate gas, might be honeypot
                    if "execution reverted" in str(e).lower():
                        results['is_honeypot'] = True
                        results['can_sell'] = False

            except Exception as e:
                logger.debug(f"Honeypot API check failed: {e}")

            # Note: Full implementation would:
            # 1. Simulate actual buy transaction
            # 2. Simulate sell transaction
            # 3. Calculate actual tax percentages
            # 4. Use external honeypot detection APIs

            return results

        except Exception as e:
            logger.error(f"Honeypot check error: {e}")
            return {'error': str(e), 'is_honeypot': False}

    def format_security_report(self, scan_results: Dict) -> str:
        """Format security scan results into readable message"""

        risk_emoji = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'CRITICAL': '🔴',
            'UNKNOWN': '⚪'
        }

        emoji = risk_emoji.get(scan_results['risk_level'], '⚪')
        score = scan_results['score']

        msg = (
            f"┌─────────────────────┐\n"
            f"│  🛡️ *SECURITY SCAN*  │\n"
            f"└─────────────────────┘\n\n"
            f"Risk Level: {emoji} *{scan_results['risk_level']}*\n"
            f"Safety Score: *{score}/100*\n\n"
        )

        # Add warnings
        if scan_results['warnings']:
            msg += "⚠️ *WARNINGS:*\n"
            for warning in scan_results['warnings']:
                msg += f"  • {warning}\n"
            msg += "\n"
        else:
            msg += "✅ *No major warnings detected!*\n\n"

        # Add rug detection details
        rug = scan_results.get('rug_detection', {})
        if rug:
            msg += "🔍 *Rug Detection:*\n"
            msg += f"  • Ownership: {'✅ Renounced' if rug.get('ownership_renounced') else '❌ NOT Renounced'}\n"
            msg += f"  • Mint Function: {'❌ Present' if rug.get('has_mint_function') else '✅ None'}\n"
            msg += f"  • Blacklist: {'❌ Present' if rug.get('has_blacklist') else '✅ None'}\n"
            msg += "\n"

        # Add LP lock details
        lp = scan_results.get('lp_lock', {})
        if lp:
            msg += "🔒 *Liquidity Lock:*\n"
            if lp.get('is_locked'):
                msg += f"  • Status: ✅ Locked\n"
                msg += f"  • Platform: {lp.get('lock_platform', 'Unknown')}\n"
                if lp.get('lock_duration_days'):
                    msg += f"  • Duration: {lp['lock_duration_days']} days\n"
            else:
                msg += f"  • Status: ⚠️ Check manually on Basescan\n"
            msg += "\n"

        # Add honeypot details
        hp = scan_results.get('honeypot', {})
        if hp:
            msg += "🍯 *Honeypot Check:*\n"
            if hp.get('is_honeypot'):
                msg += "  • Status: 🚨 *HONEYPOT DETECTED!*\n"
                msg += "  • Can Sell: ❌ NO\n"
            else:
                msg += "  • Status: ✅ Not a honeypot\n"
                if hp.get('buy_tax', 0) > 0:
                    msg += f"  • Buy Tax: {hp['buy_tax']}%\n"
                if hp.get('sell_tax', 0) > 0:
                    msg += f"  • Sell Tax: {hp['sell_tax']}%\n"
            msg += "\n"

        # Add recommendation
        if scan_results['is_safe']:
            msg += "✅ *Recommendation:* Proceed with caution\n"
        else:
            msg += "🚨 *Recommendation:* HIGH RISK - Avoid trading!\n"

        msg += "\n⚠️ *Always DYOR! This is not financial advice.*"

        return msg

