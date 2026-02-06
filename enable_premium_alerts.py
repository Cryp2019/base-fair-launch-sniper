#!/usr/bin/env python3
"""
Enable alerts for all premium users
"""
import os
from database import UserDatabase

# Load environment variables
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

print("🔧 Enabling alerts for premium users...")
print()

db = UserDatabase()

# Get all users
import sqlite3
conn = sqlite3.connect(db.db_path)
cursor = conn.cursor()

# Get all users
cursor.execute('SELECT user_id, username, tier, alerts_enabled FROM users')
users = cursor.fetchall()

print(f"📊 Total users: {len(users)}")
print()

premium_count = 0
enabled_count = 0

for user in users:
    user_id, username, tier, alerts_enabled = user
    
    if tier == 'premium':
        premium_count += 1
        print(f"👑 Premium user: {username or user_id} (Alerts: {'ON' if alerts_enabled else 'OFF'})")
        
        if not alerts_enabled:
            # Enable alerts
            cursor.execute('UPDATE users SET alerts_enabled = 1 WHERE user_id = ?', (user_id,))
            print(f"   ✅ Enabled alerts for {username or user_id}")
            enabled_count += 1
        else:
            print(f"   ✅ Already enabled")

conn.commit()
conn.close()

print()
print("=" * 60)
print(f"✅ Premium users: {premium_count}")
print(f"✅ Alerts enabled: {enabled_count}")
print()

if premium_count == 0:
    print("⚠️  No premium users found!")
    print("💡 Users need to be upgraded to premium tier first")
else:
    print("✅ All premium users now have alerts enabled!")
    print("🚀 They will receive alerts for new token launches")

print("=" * 60)
