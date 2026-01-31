#!/usr/bin/env python3
"""
Quick script to upgrade a user to premium tier
Usage: python upgrade_user.py <user_id>
"""

import sys
from database import Database

def main():
    if len(sys.argv) != 2:
        print("❌ Usage: python upgrade_user.py <user_id>")
        print("\nExample:")
        print("  python upgrade_user.py 123456789")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print("❌ Error: user_id must be a number")
        sys.exit(1)
    
    # Initialize database
    db = Database()
    
    # Check if user exists
    user = db.get_user(user_id)
    if not user:
        print(f"❌ Error: User {user_id} not found in database")
        print("\nMake sure the user has started the bot first!")
        sys.exit(1)
    
    # Check current tier
    current_tier = user['tier']
    if current_tier == 'premium':
        print(f"⚠️  User is already premium!")
        print(f"\n📊 User Info:")
        print(f"   User ID: {user_id}")
        print(f"   Username: @{user['username']}")
        print(f"   Tier: {user['tier']} 💎")
        print(f"   Referrals: {user['total_referrals']}")
        sys.exit(0)
    
    # Upgrade user
    db.update_tier(user_id, 'premium')
    
    # Get updated user info
    user = db.get_user(user_id)
    
    print("✅ User successfully upgraded to PREMIUM! 💎")
    print(f"\n📊 User Info:")
    print(f"   User ID: {user_id}")
    print(f"   Username: @{user['username']}")
    print(f"   First Name: {user['first_name']}")
    print(f"   Tier: {user['tier']} 💎")
    print(f"   Referrals: {user['total_referrals']}")
    print(f"   Joined: {user['joined_date']}")
    print(f"\n💡 Don't forget to notify the user in Telegram!")

if __name__ == '__main__':
    main()

