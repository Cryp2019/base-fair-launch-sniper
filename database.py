"""
User Database for Base Fair Launch Sniper
Tracks users, referrals, and tier status
"""
import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, db_path='users.db'):
        # Determine database path based on environment
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID'):
            # Running on Railway - use persistent volume path
            # User needs to create a volume mounted at /data in Railway
            self.db_path = '/data/users.db'
            logger.info("🚂 Detected Railway environment - using persistent volume")
        elif os.getenv('DATABASE_PATH'):
            # Custom database path from environment variable
            self.db_path = os.getenv('DATABASE_PATH')
            logger.info(f"📌 Using custom DATABASE_PATH from environment")
        elif not os.path.isabs(db_path):
            # Local development - use script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(script_dir, db_path)
            logger.info("💻 Local development mode")
        else:
            self.db_path = db_path
        
        logger.info(f"📁 Database path: {self.db_path}")
        
        # Ensure directory exists (for Railway volume)
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"📂 Created database directory: {db_dir}")
            except Exception as e:
                logger.warning(f"⚠️  Could not create directory {db_dir}: {e}")
        
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_date TEXT,
                    referrer_id INTEGER,
                    referral_code TEXT UNIQUE,
                    tier TEXT DEFAULT 'free',
                    alerts_enabled INTEGER DEFAULT 1,
                    total_referrals INTEGER DEFAULT 0,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id)
                )
            ''')
            
            # Referrals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    referral_date TEXT,
                    has_traded INTEGER DEFAULT 0,
                    first_trade_date TEXT,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id)
                )
            ''')
            
            # Stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    total_users INTEGER,
                    new_users INTEGER,
                    total_referrals INTEGER
                )
            ''')

            # Wallets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    wallet_address TEXT UNIQUE,
                    private_key TEXT,
                    created_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Referral commissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_commissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_user_id INTEGER NOT NULL,
                    trade_tx_hash TEXT NOT NULL,
                    commission_amount_eth REAL NOT NULL,
                    commission_sent_tx_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Add commission_start_date column to users table if it doesn't exist
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN commission_start_date TIMESTAMP')
                logger.info("✅ Added commission_start_date column to users table")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            conn.commit()
            conn.close()
            
            logger.info(f"✅ Database initialized successfully")
            
            # Verify database is accessible
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path)
                logger.info(f"📊 Database size: {size} bytes")
            else:
                logger.error(f"❌ Database file not found after initialization!")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 referrer_code: str = None) -> Dict:
        """Add a new user to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'User already exists'}
        
        # Generate unique referral code
        referral_code = f"BASE{user_id}"
        
        # Find referrer if code provided
        referrer_id = None
        if referrer_code:
            cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
            result = cursor.fetchone()
            if result:
                referrer_id = result[0]
                # Add to referrals table (but don't count yet - only counts when they trade)
                cursor.execute('INSERT INTO referrals (referrer_id, referred_id, referral_date, has_traded) VALUES (?, ?, ?, ?)',
                             (referrer_id, user_id, datetime.utcnow().isoformat(), 0))
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, joined_date, referrer_id, referral_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.utcnow().isoformat(), referrer_id, referral_code))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'referral_code': referral_code,
            'referred_by': referrer_id
        }
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'user_id': result[0],
            'username': result[1],
            'first_name': result[2],
            'joined_date': result[3],
            'referrer_id': result[4],
            'referral_code': result[5],
            'tier': result[6],
            'alerts_enabled': result[7],
            'total_referrals': result[8]
        }
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        user = self.get_user(user_id)
        if not user:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get active referral details (users who have traded)
        cursor.execute('''
            SELECT u.user_id, u.username, u.first_name, r.referral_date, r.has_traded, r.first_trade_date
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.referral_date DESC
        ''', (user_id,))

        referrals = []
        active_referrals = []
        for row in cursor.fetchall():
            ref_data = {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'date': row[3],
                'has_traded': bool(row[4]),
                'first_trade_date': row[5]
            }
            referrals.append(ref_data)
            if row[4]:  # has_traded
                active_referrals.append(ref_data)

        conn.close()

        return {
            'user': user,
            'referrals': referrals,
            'active_referrals': active_referrals,
            'total_referrals': len(active_referrals),  # Only count active ones
            'pending_referrals': len(referrals) - len(active_referrals)
        }
    
    def get_total_users(self) -> int:
        """Get total number of users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top referrers (only counting active referrals who have traded)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, username, first_name, total_referrals
            FROM users
            WHERE total_referrals > 0
            ORDER BY total_referrals DESC
            LIMIT ?
        ''', (limit,))

        leaderboard = []
        for row in cursor.fetchall():
            leaderboard.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'total_referrals': row[3]  # This now only counts active referrals
            })

        conn.close()
        return leaderboard
    
    def update_tier(self, user_id: int, tier: str):
        """Update user tier (free/premium)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET tier = ? WHERE user_id = ?', (tier, user_id))
        conn.commit()
        conn.close()

    def create_wallet(self, user_id: int, wallet_address: str, private_key: str) -> Dict:
        """Create a new wallet for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO wallets (user_id, wallet_address, private_key, created_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, wallet_address, private_key, datetime.utcnow().isoformat()))

            conn.commit()
            conn.close()
            return {'success': True, 'wallet_address': wallet_address}
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'message': 'Wallet already exists'}
        except Exception as e:
            conn.close()
            return {'success': False, 'message': str(e)}

    def get_user_wallets(self, user_id: int) -> List[Dict]:
        """Get all wallets for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT wallet_address, created_date, is_active
            FROM wallets
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_date DESC
        ''', (user_id,))

        wallets = []
        for row in cursor.fetchall():
            wallets.append({
                'wallet_address': row[0],
                'created_date': row[1],
                'is_active': row[2]
            })

        conn.close()
        return wallets

    def get_wallet_private_key(self, user_id: int, wallet_address: str) -> Optional[str]:
        """Get private key for a specific wallet (use with caution!)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT private_key
            FROM wallets
            WHERE user_id = ? AND wallet_address = ? AND is_active = 1
        ''', (user_id, wallet_address))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_user_by_wallet(self, wallet_address: str) -> Optional[int]:
        """Find user ID by wallet address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id
            FROM wallets
            WHERE wallet_address = ? AND is_active = 1
            LIMIT 1
        ''', (wallet_address,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def delete_wallet(self, user_id: int, wallet_address: str) -> bool:
        """Soft delete a wallet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE wallets
            SET is_active = 0
            WHERE user_id = ? AND wallet_address = ?
        ''', (user_id, wallet_address))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def mark_user_traded(self, user_id: int) -> Optional[int]:
        """
        Mark that a user has made their first trade.
        If they were referred, increment referrer's count and check for premium upgrade.
        Returns referrer_id if they should be upgraded to premium, None otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if this user was referred and hasn't traded yet
        cursor.execute('''
            SELECT referrer_id, has_traded
            FROM referrals
            WHERE referred_id = ?
        ''', (user_id,))

        result = cursor.fetchone()

        if result and result[1] == 0:  # User was referred and hasn't traded yet
            referrer_id = result[0]

            # Mark as traded
            cursor.execute('''
                UPDATE referrals
                SET has_traded = 1, first_trade_date = ?
                WHERE referred_id = ?
            ''', (datetime.utcnow().isoformat(), user_id))

            # Increment referrer's total_referrals count
            cursor.execute('''
                UPDATE users
                SET total_referrals = total_referrals + 1
                WHERE user_id = ?
            ''', (referrer_id,))

            conn.commit()

            # Check if referrer now has 10+ active referrals
            cursor.execute('SELECT total_referrals FROM users WHERE user_id = ?', (referrer_id,))
            total_refs = cursor.fetchone()[0]

            conn.close()

            # Return referrer_id if they hit 10 referrals
            if total_refs >= 10:
                return referrer_id

        conn.close()
        return None

    def check_and_upgrade_premium(self, user_id: int) -> bool:
        """Check if user has 10+ active referrals (who have traded) and auto-upgrade to premium"""
        user = self.get_user(user_id)
        if not user:
            return False

        # If user already has premium, don't downgrade
        if user['tier'] == 'premium':
            return False

        # Check if user has 10+ active referrals (who have made trades)
        if user['total_referrals'] >= 10:
            self.update_tier(user_id, 'premium')
            return True

        return False
    
    def toggle_alerts(self, user_id: int) -> bool:
        """Toggle alerts on/off for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT alerts_enabled FROM users WHERE user_id = ?', (user_id,))
        current = cursor.fetchone()[0]
        new_state = 0 if current else 1
        cursor.execute('UPDATE users SET alerts_enabled = ? WHERE user_id = ?', (new_state, user_id))
        conn.commit()
        conn.close()
        return new_state
    
    # ===== COMMISSION TRACKING FUNCTIONS =====
    
    def start_referral_commission(self, user_id: int):
        """Start 30-day commission period for referrer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET commission_start_date = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"💰 Started commission period for user {user_id}")
    
    def is_commission_active(self, user_id: int) -> bool:
        """Check if referrer's 30-day commission period is active"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT commission_start_date FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return False
        
        start_date = datetime.fromisoformat(result[0])
        days_elapsed = (datetime.now() - start_date).days
        
        return days_elapsed < 30
    
    def log_commission(self, referrer_id: int, referred_user_id: int, 
                      trade_tx_hash: str, commission_amount: float, 
                      commission_tx_hash: str = None):
        """Log commission payment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO referral_commissions 
            (referrer_id, referred_user_id, trade_tx_hash, commission_amount_eth, commission_sent_tx_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (referrer_id, referred_user_id, trade_tx_hash, commission_amount, commission_tx_hash))
        conn.commit()
        conn.close()
        logger.info(f"💰 Logged commission: {commission_amount} ETH for referrer {referrer_id}")
    
    def get_referrer_commissions(self, user_id: int) -> List[Dict]:
        """Get all commissions earned by referrer"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM referral_commissions 
            WHERE referrer_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        commissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return commissions
    
    def get_commission_stats(self, user_id: int) -> Dict:
        """Get commission statistics for referrer"""
        commissions = self.get_referrer_commissions(user_id)
        total_earned = sum(c['commission_amount_eth'] for c in commissions)
        
        # Calculate days remaining
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT commission_start_date FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        days_remaining = 0
        if result and result[0]:
            start_date = datetime.fromisoformat(result[0])
            days_elapsed = (datetime.now() - start_date).days
            days_remaining = max(0, 30 - days_elapsed)
        
        return {
            'total_earned': total_earned,
            'total_trades': len(commissions),
            'days_remaining': days_remaining,
            'is_active': days_remaining > 0
        }
    
    def get_referrer(self, user_id: int) -> Optional[int]:
        """Get the referrer ID for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

    def get_users_with_alerts(self) -> List[Dict]:
        """Get all users with alerts enabled"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, first_name FROM users WHERE alerts_enabled = 1')

        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2]
            })

        conn.close()
        return users
