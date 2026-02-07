"""
Migrate Existing Wallets to Encrypted Format
One-time migration script to encrypt all plaintext private keys
"""
import os
import sqlite3
import sys
from datetime import datetime
from encryption_utils import encrypt_private_key, generate_master_key

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def backup_database(db_path):
    """Create backup of database before migration"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path


def migrate_wallets(db_path='users.db', master_key=None):
    """
    Migrate all plaintext private keys to encrypted format
    
    Args:
        db_path: Path to database file
        master_key: Master encryption key (from WALLET_MASTER_KEY env var)
    """
    # Get master key
    if not master_key:
        master_key = os.getenv('WALLET_MASTER_KEY')
    
    if not master_key:
        print("❌ WALLET_MASTER_KEY not set!")
        print("\nGenerate a new key:")
        print(f"WALLET_MASTER_KEY={generate_master_key()}")
        print("\nThen set it:")
        print("export WALLET_MASTER_KEY=<key>  # Linux/Mac")
        print("set WALLET_MASTER_KEY=<key>     # Windows")
        return False
    
    # Determine database path
    if not os.path.isabs(db_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, db_path)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"📁 Database: {db_path}")
    
    # Backup database
    backup_path = backup_database(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all wallets
    cursor.execute('SELECT id, user_id, wallet_address, private_key FROM wallets')
    wallets = cursor.fetchall()
    
    if not wallets:
        print("ℹ️  No wallets found in database")
        conn.close()
        return True
    
    print(f"\n🔍 Found {len(wallets)} wallets to migrate")
    
    # Migrate each wallet
    migrated = 0
    errors = 0
    
    for wallet_id, user_id, wallet_address, private_key in wallets:
        try:
            # Check if already encrypted (Fernet encrypted keys start with 'gAAAAA')
            if private_key.startswith('gAAAAA'):
                print(f"⏭️  Wallet {wallet_address[:10]}... already encrypted")
                continue
            
            # Encrypt private key
            encrypted_key = encrypt_private_key(private_key, user_id, master_key)
            
            # Update database
            cursor.execute('''
                UPDATE wallets 
                SET private_key = ? 
                WHERE id = ?
            ''', (encrypted_key, wallet_id))
            
            migrated += 1
            print(f"✅ Encrypted wallet {wallet_address[:10]}... for user {user_id}")
            
        except Exception as e:
            errors += 1
            print(f"❌ Error encrypting wallet {wallet_address[:10]}...: {e}")
    
    # Commit changes
    if errors == 0:
        conn.commit()
        print(f"\n✅ Migration complete!")
        print(f"   Migrated: {migrated} wallets")
        print(f"   Errors: {errors}")
        print(f"   Backup: {backup_path}")
    else:
        print(f"\n⚠️  Migration completed with errors")
        print(f"   Migrated: {migrated} wallets")
        print(f"   Errors: {errors}")
        print(f"   Backup: {backup_path}")
        print("\n   Review errors before using encrypted wallets")
    
    conn.close()
    return errors == 0


def verify_migration(db_path='users.db', master_key=None):
    """
    Verify that all wallets are encrypted and can be decrypted
    
    Args:
        db_path: Path to database file
        master_key: Master encryption key
    """
    from encryption_utils import decrypt_private_key
    
    # Get master key
    if not master_key:
        master_key = os.getenv('WALLET_MASTER_KEY')
    
    if not master_key:
        print("❌ WALLET_MASTER_KEY not set!")
        return False
    
    # Determine database path
    if not os.path.isabs(db_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all wallets
    cursor.execute('SELECT user_id, wallet_address, private_key FROM wallets')
    wallets = cursor.fetchall()
    
    print(f"\n🔍 Verifying {len(wallets)} wallets...")
    
    verified = 0
    errors = 0
    
    for user_id, wallet_address, encrypted_key in wallets:
        try:
            # Try to decrypt
            decrypted = decrypt_private_key(encrypted_key, user_id, master_key)
            
            # Verify it's a valid private key format
            if decrypted.startswith('0x') and len(decrypted) == 66:
                verified += 1
                print(f"✅ Wallet {wallet_address[:10]}... verified")
            else:
                errors += 1
                print(f"❌ Wallet {wallet_address[:10]}... invalid format after decryption")
                
        except Exception as e:
            errors += 1
            print(f"❌ Wallet {wallet_address[:10]}... decryption failed: {e}")
    
    conn.close()
    
    print(f"\n📊 Verification Results:")
    print(f"   Verified: {verified}/{len(wallets)}")
    print(f"   Errors: {errors}")
    
    if errors == 0:
        print("\n✅ All wallets verified successfully!")
        return True
    else:
        print("\n⚠️  Some wallets failed verification")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate wallet private keys to encrypted format')
    parser.add_argument('--verify', action='store_true', help='Verify migration instead of migrating')
    parser.add_argument('--db', default='users.db', help='Database path')
    parser.add_argument('--key', help='Master encryption key (or use WALLET_MASTER_KEY env var)')
    
    args = parser.parse_args()
    
    if args.verify:
        print("🔍 VERIFICATION MODE")
        print("=" * 50)
        success = verify_migration(args.db, args.key)
    else:
        print("🔐 MIGRATION MODE")
        print("=" * 50)
        print("\n⚠️  WARNING: This will encrypt all private keys in the database")
        print("   Make sure you have WALLET_MASTER_KEY set correctly")
        print("   A backup will be created automatically\n")
        
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled")
            sys.exit(0)
        
        success = migrate_wallets(args.db, args.key)
    
    sys.exit(0 if success else 1)
