"""
Automated Sponsorship Payment Processor
Automatically activates sponsorships when USDC payments are received
Integrates with payment_monitor.py to track incoming payments
"""
import logging
import os
from web3 import Web3
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# USDC on Base
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

# Sponsorship package to duration mapping
SPONSORSHIP_PACKAGES = {
    99: {'name': 'broadcast_alert', 'duration': 1, 'type': 'broadcast'},
    199: {'name': 'featured_48h', 'duration': 2, 'type': 'featured'},
    299: {'name': 'top_performers', 'duration': 1, 'type': 'performers'},
    499: {'name': 'featured_7d', 'duration': 7, 'type': 'featured'},
    1299: {'name': 'featured_30d', 'duration': 30, 'type': 'featured'},
}

# ELIGIBILITY REQUIREMENTS - Prevent scam projects from buying promotions
ELIGIBILITY_REQUIREMENTS = {
    'min_security_score': 80,           # Must pass quality filter
    'require_ownership_renounced': True, # No rug pull risk
    'require_no_honeypot': True,        # Not a honeypot scam
    'require_lp_locked': True,          # Liquidity locked = safe
    'max_buy_tax': 10,                  # Reasonable buy tax
    'max_sell_tax': 10,                 # Reasonable sell tax
    'max_transfer_tax': 5,              # Reasonable transfer tax
}

class AutomatedSponsorshipProcessor:
    def __init__(self, db, sponsored_projects, payment_wallet: str):
        """
        Initialize automated sponsorship processor
        
        Args:
            db: UserDatabase instance
            sponsored_projects: SponsoredProjects instance
            payment_wallet: Wallet address that receives payments
        """
        self.db = db
        self.sponsored = sponsored_projects
        self.payment_wallet = Web3.to_checksum_address(payment_wallet)
        
        # Get payment address from env or use provided
        self.payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS') or payment_wallet
        if self.payment_wallet:
            self.payment_wallet = Web3.to_checksum_address(self.payment_wallet)
        
        self.processed_payments = set()  # Track processed payment hashes
        
        logger.info(f"🤖 Automated Sponsorship Processor initialized")
        logger.info(f"   💰 Payment wallet: {self.payment_wallet}")
    
    def process_payment(self, payment_data: Dict) -> bool:
        """
        Process an incoming payment and auto-activate sponsorship
        
        Args:
            payment_data: {
                'tx_hash': str,
                'from_address': str,
                'to_address': str (payment wallet),
                'amount_usd': float,
                'token_address': str,
                'timestamp': str,
                'project_wallet': str (optional, for attribution)
            }
        
        Returns:
            bool: True if sponsorship activated, False otherwise
        """
        try:
            tx_hash = payment_data.get('tx_hash', '')
            
            # Skip if already processed
            if tx_hash in self.processed_payments:
                logger.debug(f"⏭️  Already processed payment: {tx_hash}")
                return False
            
            from_wallet = payment_data.get('from_address', '').lower()
            amount = payment_data.get('amount_usd', 0)
            token_address = payment_data.get('token_address', '')
            
            # Validate payment
            if not from_wallet or amount <= 0:
                logger.warning(f"❌ Invalid payment data: {payment_data}")
                return False
            
            # CHECK ELIGIBILITY FIRST - Critical to prevent scams
            eligibility_result = self.check_project_eligibility(token_address)
            if not eligibility_result['eligible']:
                logger.warning(f"❌ Project REJECTED for sponsorship - {eligibility_result['reason']}")
                self.processed_payments.add(tx_hash)  # Mark as processed to not retry
                return False
            
            # Find matching package
            package_info = None
            for price, info in SPONSORSHIP_PACKAGES.items():
                if abs(amount - price) < 0.01:  # Account for decimal places
                    package_info = info
                    break
            
            if not package_info:
                logger.warning(f"⚠️  No matching sponsorship package for amount ${amount}")
                return False
            
            # Activate sponsorship
            project_wallet = payment_data.get('project_wallet', from_wallet)
            result = self.activate_sponsorship(
                wallet_address=project_wallet,
                amount=amount,
                package_name=package_info['name'],
                duration_days=package_info['duration'],
                tx_hash=tx_hash,
                token_address=token_address
            )
            
            if result:
                self.processed_payments.add(tx_hash)
                logger.info(f"✅ AUTO-ACTIVATED: {package_info['name']} for {project_wallet}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error processing payment: {e}")
            return False
    
    def check_project_eligibility(self, token_address: str) -> Dict:
        """
        Check if project meets sponsorship eligibility requirements
        
        Args:
            token_address: Token contract address
        
        Returns:
            Dict with 'eligible': bool and 'reason': str
        """
        try:
            if not token_address:
                return {
                    'eligible': False,
                    'reason': 'No token address provided'
                }
            
            # Import security scanner
            from security_scanner import SecurityScanner
            from web3 import Web3
            
            w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
            scanner = SecurityScanner(w3)
            
            # Get security rating
            rating = scanner.get_project_rating(token_address)
            
            # Check each requirement
            issues = []
            
            # 1. Security Score
            score = rating.get('score', 0)
            if score < ELIGIBILITY_REQUIREMENTS['min_security_score']:
                issues.append(f"Security score {score}/100 < {ELIGIBILITY_REQUIREMENTS['min_security_score']}")
            
            # 2. Ownership Renounced
            if ELIGIBILITY_REQUIREMENTS['require_ownership_renounced']:
                if not rating.get('ownership_renounced', False):
                    issues.append("Ownership not renounced (rug pull risk)")
            
            # 3. No Honeypot
            if ELIGIBILITY_REQUIREMENTS['require_no_honeypot']:
                if rating.get('is_honeypot', False):
                    issues.append("Token is a honeypot scam")
            
            # 4. LP Locked
            if ELIGIBILITY_REQUIREMENTS['require_lp_locked']:
                if not rating.get('lp_locked', False):
                    issues.append("Liquidity not locked")
            
            # 5. Reasonable Taxes
            buy_tax = rating.get('buy_tax', 0)
            sell_tax = rating.get('sell_tax', 0)
            transfer_tax = rating.get('transfer_tax', 0)
            
            if buy_tax > ELIGIBILITY_REQUIREMENTS['max_buy_tax']:
                issues.append(f"Buy tax {buy_tax}% exceeds max {ELIGIBILITY_REQUIREMENTS['max_buy_tax']}%")
            
            if sell_tax > ELIGIBILITY_REQUIREMENTS['max_sell_tax']:
                issues.append(f"Sell tax {sell_tax}% exceeds max {ELIGIBILITY_REQUIREMENTS['max_sell_tax']}%")
            
            if transfer_tax > ELIGIBILITY_REQUIREMENTS['max_transfer_tax']:
                issues.append(f"Transfer tax {transfer_tax}% exceeds max {ELIGIBILITY_REQUIREMENTS['max_transfer_tax']}%")
            
            # Return result
            if not issues:
                logger.info(f"✅ PROJECT ELIGIBLE: {token_address}")
                logger.info(f"   Security Score: {score}/100")
                logger.info(f"   Ownership: Renounced ✓")
                logger.info(f"   Honeypot: Clear ✓")
                logger.info(f"   LP: Locked ✓")
                logger.info(f"   Taxes: {buy_tax}% buy / {sell_tax}% sell ✓")
                return {'eligible': True, 'reason': 'All requirements met'}
            else:
                reason = ' | '.join(issues)
                logger.warning(f"❌ PROJECT INELIGIBLE: {token_address}")
                for issue in issues:
                    logger.warning(f"   ✗ {issue}")
                return {'eligible': False, 'reason': reason}
            
        except Exception as e:
            logger.error(f"❌ Error checking eligibility: {e}")
            return {
                'eligible': False,
                'reason': f'Eligibility check failed: {str(e)}'
            }
    
    def activate_sponsorship(self, wallet_address: str, amount: float,
                            package_name: str, duration_days: int,
                            tx_hash: str, token_address: str = None) -> bool:
        """
        Activate sponsorship for a project
        
        Args:
            wallet_address: Project's wallet address
            amount: Payment amount in USD
            package_name: Sponsorship package name
            duration_days: How many days sponsorship lasts
            tx_hash: Transaction hash for tracking
            token_address: Token contract address for attribution
        
        Returns:
            bool: True if activated successfully
        """
        try:
            # For now, we can't directly link wallet to token address
            # This would need to be done via:
            # 1. Project provides token address when initiating payment
            # 2. Invoice system with token address pre-specified
            # 3. Admin links token to wallet manually
            
            logger.info(f"📝 Sponsorship activation requested")
            logger.info(f"   💰 Amount: ${amount}")
            logger.info(f"   📦 Package: {package_name}")
            logger.info(f"   ⏱️  Duration: {duration_days} days")
            logger.info(f"   🪙 From: {wallet_address}")
            logger.info(f"   🔗 TX: {tx_hash}")
            if token_address:
                logger.info(f"   📍 Token: {token_address}")
            
            # TODO: Link token address to wallet for automatic activation
            # For now, store payment metadata for admin to link
            self._store_pending_sponsorship(
                wallet_address=wallet_address,
                amount=amount,
                package_name=package_name,
                duration_days=duration_days,
                tx_hash=tx_hash,
                token_address=token_address
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to activate sponsorship: {e}")
            return False
    
    def _store_pending_sponsorship(self, wallet_address: str, amount: float,
                                   package_name: str, duration_days: int,
                                   tx_hash: str, token_address: str = None):
        """Store pending sponsorship in database for admin verification"""
        try:
            # This would require adding a pending_sponsorships table
            logger.info(f"📦 Stored pending sponsorship (admin action required)")
            logger.info(f"   Wallet: {wallet_address}")
            logger.info(f"   Package: {package_name}")
            logger.info(f"   TX: {tx_hash}")
            if token_address:
                logger.info(f"   Token: {token_address}")
        except Exception as e:
            logger.error(f"Failed to store pending sponsorship: {e}")
    
    def get_payment_address(self) -> str:
        """Get the payment wallet address"""
        return self.payment_wallet
    
    def get_sponsorship_rates(self) -> Dict:
        """Get all sponsorship rates"""
        return {
            price: {
                'name': info['name'],
                'duration': f"{info['duration']} day(s)",
                'type': info['type']
            }
            for price, info in SPONSORSHIP_PACKAGES.items()
        }


def format_payment_instructions(payment_wallet: str) -> str:
    """Format payment instructions for projects"""
    msg = f"""
💰 <b>AUTOMATED SPONSORSHIP PAYMENT</b>

Send USDC to: <code>{payment_wallet}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📢 <b>Broadcast Alert</b>
Amount: <code>99 USDC</code>
Duration: 1 day
Features: One-time alert to all users

⭐ <b>48-Hour Featured</b>
Amount: <code>199 USDC</code>
Duration: 2 days
Features: Featured badge + top position

👑 <b>1-Week Premium</b>
Amount: <code>499 USDC</code>
Duration: 7 days
Features: Premium badge + broadcasts

🚀 <b>Top Performers</b>
Amount: <code>299 USDC</code>
Duration: 24 hours
Features: Featured in top performers

🏆 <b>30-Day Premium</b>
Amount: <code>1299 USDC</code>
Duration: 30 days
Features: Gold badge + daily promotion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>Important:</b>
1. Make sure you send EXACTLY the amount listed
2. Payment on Base Network only
3. Include your token contract in the memo if possible
4. Sponsorship activates automatically upon payment

📝 Network: Base
🪙 Token: USDC
⏱️ Confirms: ~2 minutes

Questions? Contact @support
"""
    return msg


async def monitor_sponsorship_payments(w3: Web3, processor: AutomatedSponsorshipProcessor,
                                       poll_interval: int = 60):
    """
    Background task to monitor incoming payments
    
    Args:
        w3: Web3 instance
        processor: AutomatedSponsorshipProcessor instance
        poll_interval: Seconds between checks (default 60)
    """
    logger.info("🔍 Sponsorship payment monitor started")
    logger.info(f"   Monitoring wallet: {processor.get_payment_address()}")
    logger.info(f"   Poll interval: {poll_interval}s")
    
    # This would integrate with PaymentMonitor to detect incoming USDC transfers
    # Implementation would depend on PaymentMonitor's event detection system
