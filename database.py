"""
User Database for Base Fair Launch Sniper
Tracks users, referrals, and tier status
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List

class UserDatabase:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
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

        conn.commit()
        conn.close()
    
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
                # Update referrer's total referrals
                cursor.execute('UPDATE users SET total_referrals = total_referrals + 1 WHERE user_id = ?', 
                             (referrer_id,))
                # Add to referrals table
                cursor.execute('INSERT INTO referrals (referrer_id, referred_id, referral_date) VALUES (?, ?, ?)',
                             (referrer_id, user_id, datetime.utcnow().isoformat()))
        
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
        
        # Get referral details
        cursor.execute('''
            SELECT u.user_id, u.username, u.first_name, r.referral_date
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.referral_date DESC
        ''', (user_id,))
        
        referrals = []
        for row in cursor.fetchall():
            referrals.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'date': row[3]
            })
        
        conn.close()
        
        return {
            'user': user,
            'referrals': referrals,
            'total_referrals': len(referrals)
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
        """Get top referrers"""
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
                'total_referrals': row[3]
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

    def check_and_upgrade_premium(self, user_id: int) -> bool:
        """Check if user has 10+ referrals and auto-upgrade to premium for 1 month"""
        user = self.get_user(user_id)
        if not user:
            return False

        # If user already has premium, don't downgrade
        if user['tier'] == 'premium':
            return False

        # Check if user has 10+ referrals
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
        return bool(new_state)

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
