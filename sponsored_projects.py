"""
Sponsored Projects & Top Performers Module
Tracks promoted tokens and top-performing launches
Monetizes the bot through project promotion/sponsorships
"""
import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SponsoredProjects:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Initialize sponsored and performance tracking tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Sponsored projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sponsored_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT UNIQUE,
                    token_name TEXT,
                    token_symbol TEXT,
                    project_wallet TEXT,
                    sponsor_type TEXT,
                    payment_amount REAL,
                    currency TEXT DEFAULT 'USD',
                    paid_at TEXT,
                    expires_at TEXT,
                    active INTEGER DEFAULT 1,
                    featured_position INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    impressions INTEGER DEFAULT 0
                )
            ''')
            
            # Top performers table (auto-tracked)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS top_performers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT UNIQUE,
                    token_name TEXT,
                    token_symbol TEXT,
                    launched_at TEXT,
                    current_price REAL,
                    launch_price REAL,
                    price_increase_percent REAL,
                    market_cap REAL,
                    volume_24h REAL,
                    holder_count INTEGER,
                    security_score INTEGER,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Sponsored projects tables initialized")
        except Exception as e:
            logger.error(f"❌ Failed to init sponsored tables: {e}")
    
    def add_sponsored_project(self, token_address: str, token_name: str, token_symbol: str,
                             project_wallet: str, sponsor_type: str, payment_amount: float,
                             duration_days: int = 30) -> bool:
        """Add a new sponsored project"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expires_at = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO sponsored_projects 
                (token_address, token_name, token_symbol, project_wallet, sponsor_type, 
                 payment_amount, paid_at, expires_at, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (token_address.lower(), token_name, token_symbol, project_wallet, 
                  sponsor_type, payment_amount, paid_at, expires_at))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Added sponsored project: {token_name} ({token_symbol})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add sponsored project: {e}")
            return False
    
    def is_sponsored(self, token_address: str) -> Optional[Dict]:
        """Check if token is sponsored and get details"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sponsored_projects 
                WHERE token_address = ? AND active = 1 AND expires_at > datetime('now')
            ''', (token_address.lower(),))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'token_address': result[1],
                    'token_name': result[2],
                    'token_symbol': result[3],
                    'sponsor_type': result[5],
                    'payment_amount': result[6],
                    'paid_at': result[8],
                    'expires_at': result[9],
                    'featured_position': result[11]
                }
            return None
        except Exception as e:
            logger.error(f"❌ Failed to check sponsored status: {e}")
            return None
    
    def add_top_performer(self, token_address: str, token_name: str, token_symbol: str,
                         current_price: float, launch_price: float, market_cap: float,
                         volume_24h: float, holder_count: int, security_score: int):
        """Track a top performing token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            price_increase = ((current_price - launch_price) / launch_price * 100) if launch_price > 0 else 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO top_performers
                (token_address, token_name, token_symbol, launched_at, current_price, 
                 launch_price, price_increase_percent, market_cap, volume_24h, 
                 holder_count, security_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (token_address.lower(), token_name, token_symbol, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  current_price, launch_price, price_increase, market_cap, volume_24h,
                  holder_count, security_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to add top performer: {e}")
    
    def get_top_performers(self, limit: int = 10, hours: int = 24) -> List[Dict]:
        """Get top performing tokens from last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                SELECT * FROM top_performers 
                WHERE launched_at > ?
                ORDER BY price_increase_percent DESC
                LIMIT ?
            ''', (since, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            performers = []
            for row in results:
                performers.append({
                    'token_name': row[2],
                    'token_symbol': row[3],
                    'token_address': row[1],
                    'price_increase_percent': row[7],
                    'market_cap': row[8],
                    'volume_24h': row[9],
                    'holder_count': row[10],
                    'security_score': row[11],
                    'launched_at': row[5]
                })
            
            return performers
        except Exception as e:
            logger.error(f"❌ Failed to get top performers: {e}")
            return []

# ===== SPONSORSHIP PRICING =====

AD_RATES = {
    'featured_48h': {
        'name': '⭐ Featured 48-Hour Boost',
        'price': 199,
        'duration': 2,
        'highlights': [
            '📌 Pinned to top of alerts',
            '⭐ Featured badge',
            '🔔 Broadcast alert to all users',
            '📊 Analytics dashboard'
        ]
    },
    'featured_7d': {
        'name': '👑 Featured 1-Week Premium',
        'price': 499,
        'duration': 7,
        'highlights': [
            '📌 Pinned for 7 days',
            '👑 Premium badge',
            '🔔 Multiple broadcast alerts',
            '📈 Performance tracking',
            '💬 Community boost post'
        ]
    },
    'featured_30d': {
        'name': '🏆 Featured 30-Day Top Tier',
        'price': 1299,
        'duration': 30,
        'highlights': [
            '📌 Premium position (30 days)',
            '🏆 Top tier badge',
            '🔔 Daily promotional alerts',
            '📊 Full analytics dashboard',
            '💬 Daily community mentions',
            '📱 Mobile notification boost'
        ]
    },
    'broadcast_alert': {
        'name': '📢 Broadcast Alert Single',
        'price': 99,
        'duration': 1,
        'highlights': [
            '📢 One-time broadcast to all users',
            '⭐ Highlighted format',
            '📊 Click analytics'
        ]
    },
    'top_performers': {
        'name': '🚀 Top Performers List',
        'price': 299,
        'duration': 24,
        'highlights': [
            '🚀 Featured in top performers',
            '📊 Real-time performance tracking',
            '🎯 Performance-based ranking'
        ]
    }
}

def get_ad_rates() -> Dict:
    """Get all available ad rates and packages"""
    return AD_RATES

def format_ad_rates_message() -> str:
    """Format ad rates for display to projects"""
    msg = """
🎯 <b>PROJECT SPONSORSHIP PACKAGES</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 <b>⭐ Featured 48-Hour Boost</b>
<b>$199 USD</b>
• Pinned to top of launch alerts
• Featured badge (⭐) on all posts
• Broadcast alert to all users
• Analytics dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏅 <b>👑 Featured 1-Week Premium</b>
<b>$499 USD</b>
• Premium position for 7 days
• Purple badge on all posts  
• 3-5 promotional broadcasts
• Full performance analytics
• Community boost post
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 <b>🏆 Featured 30-Day Top Tier</b>
<b>$1,299 USD</b>
• Premium position for full month
• Gold badge (🏆) on all posts
• Daily promotional alerts
• Complete analytics dashboard
• Daily community mentions
• Mobile notification priority
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📢 <b>📢 Broadcast Alert Single</b>
<b>$99 USD</b>
• One-time broadcast to all users
• Highlighted message format
• Click and conversion tracking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>🚀 Top Performers List (24h)</b>
<b>$299 USD</b>
• Featured in real-time top performers
• Performance tracking & ranking
• Automatic updates every hour
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>All prices in USD. Payment via USDC on Base Network.
Contact @support for bulk discounts and custom packages.</i>
"""
    return msg
