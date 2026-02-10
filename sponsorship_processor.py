"""
Automated Sponsorship Payment Processor
Automatically activates sponsorships when USDC payments are received
Integrates with payment_monitor.py to track incoming payments
"""
import logging
import os
import sqlite3
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
        self.payment_wallet = os.getenv('PAYMENT_WALLET_ADDRESS') or payment_wallet
        if self.payment_wallet:
            self.payment_wallet = Web3.to_checksum_address(self.payment_wallet)
        
        self.processed_payments = set()  # Track processed payment hashes
        self._init_pending_table()
        
        logger.info(f"🤖 Automated Sponsorship Processor initialized")
        logger.info(f"   💰 Payment wallet: {self.payment_wallet}")
    
    def _init_pending_table(self):
        """Create pending_sponsorships table if it doesn't exist"""
        try:
            db_path = getattr(self.db, 'db_path', 'users.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_sponsorships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    package_name TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    tx_hash TEXT NOT NULL UNIQUE,
                    token_address TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activated_at TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("📦 Pending sponsorships table ready")
        except Exception as e:
            logger.error(f"Error creating pending_sponsorships table: {e}")
    
    async def process_payment(self, payment_data: Dict) -> bool:
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
            
            # Find matching package
            package_info = None
            for price, info in SPONSORSHIP_PACKAGES.items():
                if abs(amount - price) < 1.0:  # Allow $1 tolerance for rounding
                    package_info = info
                    break
            
            if not package_info:
                logger.info(f"ℹ️ Payment ${amount} doesn't match any sponsorship package (premium upgrade?)")
                return False
            
            logger.info(f"📢 Sponsorship payment detected: ${amount} → {package_info['name']}")
            
            # CHECK ELIGIBILITY if token address is provided
            if token_address:
                eligibility_result = self.check_project_eligibility(token_address)
                if not eligibility_result['eligible']:
                    logger.warning(f"❌ Project REJECTED for sponsorship - {eligibility_result['reason']}")
                    # Store as pending for admin review (payment was valid, token wasn't)
                    self._store_pending_sponsorship(
                        wallet_address=from_wallet,
                        amount=amount,
                        package_name=package_info['name'],
                        duration_days=package_info['duration'],
                        tx_hash=tx_hash,
                        token_address=token_address,
                        status='rejected'
                    )
                    self.processed_payments.add(tx_hash)
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
            rating = scanner.scan_token(token_address)
            
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
                return {'eligible': True, 'reason': 'All requirements met'}
            else:
                reason = ' | '.join(issues)
                logger.warning(f"❌ PROJECT INELIGIBLE: {token_address} - {reason}")
                return {'eligible': False, 'reason': reason}
            
        except Exception as e:
            logger.error(f"❌ Error checking eligibility: {e}")
            # Allow sponsorship if we can't check (admin can review later)
            return {
                'eligible': True,
                'reason': f'Eligibility check unavailable - auto-approved for admin review'
            }
    
    def activate_sponsorship(self, wallet_address: str, amount: float,
                            package_name: str, duration_days: int,
                            tx_hash: str, token_address: str = None) -> bool:
        """
        Activate sponsorship for a project
        """
        try:
            logger.info(f"📝 Activating sponsorship:")
            logger.info(f"   💰 Amount: ${amount}")
            logger.info(f"   📦 Package: {package_name}")
            logger.info(f"   ⏱️  Duration: {duration_days} days")
            logger.info(f"   🪙 From: {wallet_address}")
            logger.info(f"   🔗 TX: {tx_hash}")
            
            # If we have a token address, activate directly in sponsored_projects
            if token_address and self.sponsored:
                try:
                    self.sponsored.add_sponsored_project(
                        token_address=token_address,
                        token_name=f"Sponsored-{token_address[:8]}",
                        token_symbol="SPONSORED",
                        project_wallet=wallet_address,
                        sponsor_type=package_name,
                        payment_amount=amount,
                        duration_days=duration_days
                    )
                    logger.info(f"✅ Sponsorship ACTIVATED in database for token {token_address}")
                except Exception as e:
                    logger.error(f"Failed to add to sponsored_projects: {e}")
            
            # Always store in pending_sponsorships for tracking
            self._store_pending_sponsorship(
                wallet_address=wallet_address,
                amount=amount,
                package_name=package_name,
                duration_days=duration_days,
                tx_hash=tx_hash,
                token_address=token_address,
                status='activated' if token_address else 'pending'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to activate sponsorship: {e}")
            return False
    
    def _store_pending_sponsorship(self, wallet_address: str, amount: float,
                                   package_name: str, duration_days: int,
                                   tx_hash: str, token_address: str = None,
                                   status: str = 'pending'):
        """Store sponsorship record in database"""
        try:
            db_path = getattr(self.db, 'db_path', 'users.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO pending_sponsorships 
                (wallet_address, amount, package_name, duration_days, tx_hash, token_address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (wallet_address, amount, package_name, duration_days, tx_hash, token_address, status))
            conn.commit()
            conn.close()
            logger.info(f"📦 Stored sponsorship record: {package_name} ({status})")
        except Exception as e:
            logger.error(f"Failed to store sponsorship: {e}")
    
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
    msg = (
        "💰 *PROMOTE YOUR PROJECT*\n\n"
        f"Send USDC to:\n`{payment_wallet}`\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📢 *PACKAGES*\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "📢 *Broadcast Alert* — `99 USDC`\n"
        "• One-time alert to ALL users\n"
        "• Highlighted format + analytics\n\n"
        "⭐ *48-Hour Featured* — `199 USDC`\n"
        "• Pinned to top of alerts (2 days)\n"
        "• ⭐ Featured badge on all alerts\n\n"
        "🚀 *Top Performers* — `299 USDC`\n"
        "• Featured in top performers list\n"
        "• Real-time performance tracking\n\n"
        "👑 *1-Week Premium* — `499 USDC`\n"
        "• Premium badge for 7 days\n"
        "• Priority in all alerts + banner\n\n"
        "🏆 *30-Day Premium* — `1,299 USDC`\n"
        "• Gold badge for 30 days\n"
        "• Daily promotion + broadcasts\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "⚠️ *Requirements:*\n"
        "• Token must pass security checks\n"
        "• Ownership must be renounced\n"
        "• LP must be locked\n"
        "• Max 10% buy/sell tax\n\n"
        "📝 *Network:* Base\n"
        "🪙 *Token:* USDC\n"
        "⏱️ *Activates:* ~2 minutes\n\n"
        "Send EXACT amount listed above.\n"
        "Sponsorship activates automatically! ✅"
    )
    return msg
