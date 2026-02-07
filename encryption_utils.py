"""
Wallet Encryption Utilities
Provides secure encryption/decryption for private keys
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def generate_master_key() -> str:
    """
    Generate a new Fernet encryption key
    
    Returns:
        Base64-encoded encryption key
        
    Usage:
        key = generate_master_key()
        # Save this key securely in Railway environment variables
    """
    return Fernet.generate_key().decode()


def get_user_cipher(user_id: int, master_key: str) -> Fernet:
    """
    Create user-specific cipher from master key and user ID
    
    Args:
        user_id: User's unique ID
        master_key: Master encryption key from environment
        
    Returns:
        Fernet cipher object for this user
        
    Note:
        Each user gets a unique cipher derived from master key + user ID
        This prevents cross-user key access even if database is compromised
    """
    # Derive user-specific key using PBKDF2
    user_key = hashlib.pbkdf2_hmac(
        'sha256',
        f"{master_key}{user_id}".encode(),
        b'wallet_salt_v1',  # Static salt for consistency
        100000  # 100k iterations for security
    )
    
    # Fernet requires 32-byte key, base64-encoded
    fernet_key = base64.urlsafe_b64encode(user_key[:32])
    return Fernet(fernet_key)


def encrypt_private_key(private_key: str, user_id: int, master_key: str) -> str:
    """
    Encrypt a private key for storage
    
    Args:
        private_key: Plaintext private key (hex format)
        user_id: User's unique ID
        master_key: Master encryption key
        
    Returns:
        Encrypted private key (base64 string)
        
    Example:
        encrypted = encrypt_private_key("0x123...", 12345, master_key)
        # Store encrypted in database
    """
    try:
        cipher = get_user_cipher(user_id, master_key)
        encrypted_bytes = cipher.encrypt(private_key.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Encryption error for user {user_id}: {e}")
        raise


def decrypt_private_key(encrypted_key: str, user_id: int, master_key: str) -> str:
    """
    Decrypt a private key from storage
    
    Args:
        encrypted_key: Encrypted private key from database
        user_id: User's unique ID
        master_key: Master encryption key
        
    Returns:
        Decrypted private key (hex format)
        
    Example:
        private_key = decrypt_private_key(encrypted, 12345, master_key)
        # Use for transaction signing
    """
    try:
        cipher = get_user_cipher(user_id, master_key)
        decrypted_bytes = cipher.decrypt(encrypted_key.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Decryption error for user {user_id}: {e}")
        raise


def validate_master_key(master_key: Optional[str]) -> bool:
    """
    Validate that master key is properly formatted
    
    Args:
        master_key: Master key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not master_key:
        return False
    
    try:
        # Try to create a Fernet instance
        Fernet(master_key.encode())
        return True
    except Exception:
        return False


# Test function for verification
def test_encryption():
    """Test encryption/decryption cycle"""
    print("🧪 Testing wallet encryption...")
    
    # Generate test key
    master_key = generate_master_key()
    print(f"✅ Generated master key: {master_key[:20]}...")
    
    # Test data
    test_private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    test_user_id = 12345
    
    # Encrypt
    encrypted = encrypt_private_key(test_private_key, test_user_id, master_key)
    print(f"✅ Encrypted: {encrypted[:50]}...")
    
    # Decrypt
    decrypted = decrypt_private_key(encrypted, test_user_id, master_key)
    print(f"✅ Decrypted: {decrypted[:20]}...")
    
    # Verify
    if decrypted == test_private_key:
        print("✅ Encryption/decryption successful!")
        return True
    else:
        print("❌ Encryption/decryption failed!")
        return False


if __name__ == "__main__":
    # Run test
    test_encryption()
    
    # Generate key for production
    print("\n" + "="*50)
    print("🔑 PRODUCTION KEY GENERATION")
    print("="*50)
    print("\nGenerate a new master key for production:")
    print(f"\nWALLET_MASTER_KEY={generate_master_key()}")
    print("\n⚠️  SAVE THIS KEY SECURELY!")
    print("   Add to Railway environment variables")
    print("   Losing this key means losing all wallets!")
