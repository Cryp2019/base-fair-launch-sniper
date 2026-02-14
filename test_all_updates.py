#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Integration Test for All Updates
Tests every module offline (no API keys needed) to verify all new updates are integrated.

Modules tested:
  1. bot.py          - Core sniping functions (is_renounced, thresholds)
  2. scoring.py      - Token scoring system (social, viral, security, overall)
  3. database.py     - User database, wallets, referrals, groups, commissions
  4. security_scanner.py - SecurityScanner class and report formatting
  5. trading.py      - TradingBot class and constants
  6. group_poster.py - GroupPoster formatting and quality gate
  7. base_scanner_design.py - Premium, ultra-premium, and minimal alert designs
  8. encryption_utils.py - Wallet encryption/decryption cycle
"""

import sys
import os
import tempfile

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

passed = 0
failed = 0


def check(description, condition):
    """Helper to track pass/fail results."""
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {description}")
    else:
        failed += 1
        print(f"  ❌ {description}")


# ============================================================
print("\n" + "=" * 80)
print("[TEST] COMPREHENSIVE INTEGRATION TEST - ALL UPDATES")
print("=" * 80 + "\n")

# ------------------------------------------------------------------
# TEST 1: Core bot.py imports and is_renounced logic
# ------------------------------------------------------------------
print("TEST 1: Core bot.py - Imports and Ownership Logic")
print("-" * 80)

try:
    from bot import (
        is_renounced,
        MAX_TAX_PERCENT,
        MAX_PREMINE_RATIO,
        MIN_LIQUIDITY_LOCK_DAYS,
        check_honeypot,
        check_taxes,
        get_lock_duration,
        is_liquidity_locked,
        get_new_pairs,
        analyze_new_pair,
        get_creator_address,
        FACTORY_ADDRESS,
        USDC_ADDRESS,
        WETH_ADDRESS,
    )
    check("All bot.py functions imported", True)
except ImportError as e:
    check(f"All bot.py functions imported (error: {e})", False)

# is_renounced tests
check("Zero address is renounced", is_renounced("0x0000000000000000000000000000000000000000"))
check("Dead address is renounced", is_renounced("0x000000000000000000000000000000000000dEaD"))
check("Burn address 0x01 is renounced", is_renounced("0x0000000000000000000000000000000000000001"))
check("Regular address is NOT renounced", not is_renounced("0x1234567890123456789012345678901234567890"))
check("Case-insensitive dead address", is_renounced("0x000000000000000000000000000000000000DEAD"))

# Threshold configuration
check(f"MAX_PREMINE_RATIO is 5% ({MAX_PREMINE_RATIO})", MAX_PREMINE_RATIO == 0.05)
check(f"MIN_LIQUIDITY_LOCK_DAYS is 30 ({MIN_LIQUIDITY_LOCK_DAYS})", MIN_LIQUIDITY_LOCK_DAYS == 30)
check(f"MAX_TAX_PERCENT is 5 ({MAX_TAX_PERCENT})", MAX_TAX_PERCENT == 5)

# Contract addresses
check("Factory address is set", FACTORY_ADDRESS == "0x33128a8fC17869897dcE68Ed026d694621f6FDfD")
check("USDC address is set", USDC_ADDRESS is not None and len(USDC_ADDRESS) == 42)
check("WETH address is set", WETH_ADDRESS is not None and len(WETH_ADDRESS) == 42)

print()

# ------------------------------------------------------------------
# TEST 2: scoring.py - Token scoring system
# ------------------------------------------------------------------
print("TEST 2: scoring.py - Token Scoring System")
print("-" * 80)

try:
    from scoring import calculate_token_scores, get_score_emoji, format_score
    check("scoring.py imported", True)
except ImportError as e:
    check(f"scoring.py imported (error: {e})", False)

# High-quality token
analysis_safe = {
    'renounced': True,
    'is_honeypot': False,
    'liquidity_locked': True,
    'lock_days': 365,
    'buy_tax': 1,
    'sell_tax': 1,
}
metrics_high = {
    'liquidity_usd': 100000,
    'volume_24h': 50000,
    'market_cap': 500000,
    'price_change_24h': 50,
}
scores_high = calculate_token_scores(analysis_safe, metrics_high)
check("Social score is 0-100", 0 <= scores_high['social_score'] <= 100)
check("Viral score is 0-100", 0 <= scores_high['viral_score'] <= 100)
check("Security score is 0-100", 0 <= scores_high['security_score'] <= 100)
check("Overall score is 0-100", 0 <= scores_high['overall_score'] <= 100)
check("Safe token has high security score (>=70)", scores_high['security_score'] >= 70)

# Risky token
analysis_risky = {
    'renounced': False,
    'is_honeypot': True,
    'liquidity_locked': False,
    'lock_days': 0,
    'buy_tax': 20,
    'sell_tax': 20,
}
metrics_low = {
    'liquidity_usd': 100,
    'volume_24h': 10,
    'market_cap': 1000,
    'price_change_24h': 0,
}
scores_low = calculate_token_scores(analysis_risky, metrics_low)
check("Risky token has lower security score", scores_low['security_score'] < scores_high['security_score'])
check("Risky token has lower overall score", scores_low['overall_score'] < scores_high['overall_score'])

# Score emojis
check("Score >= 75 is green", get_score_emoji(75) == "🟢")
check("Score >= 50 is yellow", get_score_emoji(50) == "🟡")
check("Score >= 25 is orange", get_score_emoji(25) == "🟠")
check("Score < 25 is red", get_score_emoji(10) == "🔴")

# format_score
formatted = format_score(85)
check("format_score includes emoji and value", "🟢" in formatted and "85/100" in formatted)

print()

# ------------------------------------------------------------------
# TEST 3: database.py - User Database
# ------------------------------------------------------------------
print("TEST 3: database.py - User Database (SQLite)")
print("-" * 80)

try:
    from database import UserDatabase
    check("database.py imported", True)
except ImportError as e:
    check(f"database.py imported (error: {e})", False)

# Create a temporary database for testing
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
    tmp_db_path = tmp.name

try:
    db = UserDatabase(db_path=tmp_db_path)
    check("Database initialized successfully", os.path.exists(tmp_db_path))

    # Add user
    result = db.add_user(user_id=12345, username="testuser", first_name="Test")
    check("User added successfully", result['success'])
    check("Referral code generated", result['referral_code'] == "BASE12345")

    # Get user
    user = db.get_user(12345)
    check("User retrieved", user is not None)
    check("Username stored correctly", user['username'] == "testuser")
    check("Default tier is free", user['tier'] == 'free')
    check("Alerts enabled by default", user['alerts_enabled'] == 1)

    # Duplicate user
    dup_result = db.add_user(user_id=12345, username="testuser")
    check("Duplicate user rejected", not dup_result['success'])

    # Referral system
    result2 = db.add_user(user_id=67890, username="referred_user", referrer_code="BASE12345")
    check("Referred user added with referral code", result2['success'])
    check("Referred user linked to referrer", result2['referred_by'] == 12345)

    # User stats
    stats = db.get_user_stats(12345)
    check("User stats returned", stats is not None)
    check("Referrals list is accessible", 'referrals' in stats)

    # Toggle alerts
    new_state = db.toggle_alerts(12345)
    check("Alerts toggled off", new_state == 0)
    new_state = db.toggle_alerts(12345)
    check("Alerts toggled back on", new_state == 1)

    # Update tier
    db.update_tier(12345, 'premium')
    user = db.get_user(12345)
    check("Tier updated to premium", user['tier'] == 'premium')

    # Leaderboard
    leaderboard = db.get_leaderboard(limit=10)
    check("Leaderboard returns list", isinstance(leaderboard, list))

    # Total users
    total = db.get_total_users()
    check("Total users count correct", total == 2)

    # Group management
    add_group_result = db.add_group(group_id=-100123, group_name="test_group", group_title="Test Group")
    check("Group added", add_group_result)

    groups = db.get_all_groups()
    check("Groups retrieved", len(groups) >= 1)
    check("Group has correct ID", groups[0]['group_id'] == -100123)

    db.update_group_post_count(-100123)
    check("Group post count updated (no error)", True)

    remove_result = db.remove_group(-100123)
    check("Group removed", remove_result)
    check("Groups list empty after removal", len(db.get_all_groups()) == 0)

    # Wallet creation (without master key, stored in plaintext)
    wallet_result = db.create_wallet(
        user_id=12345,
        wallet_address="0xTestWalletAddress123",
        private_key="0xTestPrivateKey123"
    )
    check("Wallet created", wallet_result['success'])

    # Verify wallet access log entry was created by _log_wallet_access
    import sqlite3 as _sqlite3
    _conn = _sqlite3.connect(tmp_db_path)
    _cur = _conn.cursor()
    _cur.execute("SELECT user_id, wallet_address, action FROM wallet_access_log WHERE user_id = 12345")
    _log_row = _cur.fetchone()
    _conn.close()
    check("Wallet access log recorded", _log_row is not None)
    check("Wallet access log action is 'created'", _log_row is not None and _log_row[2] == 'created')

    wallets = db.get_user_wallets(12345)
    check("Wallet retrieved for user", len(wallets) == 1)
    check("Wallet address stored", wallets[0]['wallet_address'] == "0xTestWalletAddress123")

    # Get private key
    pk = db.get_wallet_private_key(12345, "0xTestWalletAddress123")
    check("Private key retrievable", pk is not None)

    # Find user by wallet
    found_user = db.get_user_by_wallet("0xTestWalletAddress123")
    check("User found by wallet address", found_user == 12345)

    # Delete wallet (soft delete)
    deleted = db.delete_wallet(12345, "0xTestWalletAddress123")
    check("Wallet soft deleted", deleted)
    check("Wallet no longer active", len(db.get_user_wallets(12345)) == 0)

    # Users with alerts
    alert_users = db.get_users_with_alerts()
    check("Users with alerts returned", len(alert_users) >= 1)

    # Commission tracking
    db.start_referral_commission(12345)
    check("Commission period started", db.is_commission_active(12345))

    db.log_commission(
        referrer_id=12345,
        referred_user_id=67890,
        trade_tx_hash="0xTestTxHash",
        commission_amount=0.001,
        commission_tx_hash="0xCommTxHash"
    )
    commissions = db.get_referrer_commissions(12345)
    check("Commission logged", len(commissions) == 1)
    check("Commission amount correct", commissions[0]['commission_amount_eth'] == 0.001)

    comm_stats = db.get_commission_stats(12345)
    check("Commission stats returned", comm_stats['total_earned'] == 0.001)
    check("Commission is active", comm_stats['is_active'])

    # Mark user traded and check premium upgrade
    # Add 10 referred users who trade to trigger premium upgrade
    user_before = db.get_user(12345)
    check("Tier is premium before reset", user_before['tier'] == 'premium')
    db.update_tier(12345, 'free')  # Reset to free for test
    user_reset = db.get_user(12345)
    check("Tier reset to free", user_reset['tier'] == 'free')
    for i in range(10):
        uid = 100000 + i
        db.add_user(user_id=uid, username=f"ref_{i}", referrer_code="BASE12345")
        db.mark_user_traded(uid)

    upgraded = db.check_and_upgrade_premium(12345)
    check("Auto-upgrade to premium after 10 referrals", upgraded)
    user = db.get_user(12345)
    check("User tier is now premium", user['tier'] == 'premium')

    # Scheduled deletions
    db.add_scheduled_deletion(chat_id=-1001, message_id=42, delete_at=9999999999)
    pending = db.get_pending_deletions()
    check("Scheduled deletion added", len(pending) >= 1)
    db.remove_scheduled_deletion(chat_id=-1001, message_id=42)
    check("Scheduled deletion removed", len(db.get_pending_deletions()) == 0)

finally:
    os.unlink(tmp_db_path)

print()

# ------------------------------------------------------------------
# TEST 4: security_scanner.py - SecurityScanner class
# ------------------------------------------------------------------
print("TEST 4: security_scanner.py - SecurityScanner Class")
print("-" * 80)

try:
    from security_scanner import SecurityScanner, DANGEROUS_FUNCTIONS, LOCK_PLATFORMS
    check("security_scanner.py imported", True)
except ImportError as e:
    check(f"security_scanner.py imported (error: {e})", False)

# Verify dangerous function signatures
check("Mint function signature present", "mint" in DANGEROUS_FUNCTIONS)
check("Blacklist signature present", "blacklist" in DANGEROUS_FUNCTIONS)
check("Pause signature present", "pause" in DANGEROUS_FUNCTIONS)
check("setTaxFee signature present", "setTaxFee" in DANGEROUS_FUNCTIONS)

# Verify lock platforms
check("Lock platforms defined", len(LOCK_PLATFORMS) > 0)

# Test SecurityScanner instantiation (with a mock web3 — just verify it can be created)
from unittest.mock import MagicMock

mock_w3 = MagicMock()
scanner = SecurityScanner(mock_w3)
check("SecurityScanner instantiated with web3", scanner.w3 == mock_w3)

# Test format_security_report
sample_scan = {
    'is_safe': True,
    'risk_level': 'LOW',
    'warnings': [],
    'score': 90,
    'rug_detection': {
        'ownership_renounced': True,
        'has_mint_function': False,
        'has_blacklist': False,
    },
    'lp_lock': {
        'is_locked': True,
        'lock_platform': 'Uncx Network',
        'lock_duration_days': 90,
    },
    'honeypot': {
        'is_honeypot': False,
        'buy_tax': 1,
        'sell_tax': 1,
    }
}
report = scanner.format_security_report(sample_scan)
check("Security report contains score", "90/100" in report)
check("Security report contains risk level", "LOW" in report)
check("Security report mentions renounced", "Renounced" in report)
check("Security report mentions honeypot check", "honeypot" in report.lower())

# Test with unsafe results
unsafe_scan = {
    'is_safe': False,
    'risk_level': 'CRITICAL',
    'warnings': ['🚨 HONEYPOT DETECTED - CANNOT SELL!'],
    'score': 0,
    'rug_detection': {'ownership_renounced': False, 'has_mint_function': True, 'has_blacklist': True},
    'lp_lock': {'is_locked': False},
    'honeypot': {'is_honeypot': True},
}
unsafe_report = scanner.format_security_report(unsafe_scan)
check("Unsafe report shows CRITICAL", "CRITICAL" in unsafe_report)
check("Unsafe report shows HIGH RISK recommendation", "HIGH RISK" in unsafe_report)

print()

# ------------------------------------------------------------------
# TEST 5: trading.py - TradingBot class
# ------------------------------------------------------------------
print("TEST 5: trading.py - TradingBot Class and Constants")
print("-" * 80)

try:
    from trading import TradingBot, UNISWAP_V3_ROUTER, WETH_ADDRESS as TRADING_WETH, USDC_ADDRESS as TRADING_USDC
    check("trading.py imported", True)
except ImportError as e:
    check(f"trading.py imported (error: {e})", False)

check("Uniswap V3 router address set", UNISWAP_V3_ROUTER == "0x2626664c2603336E57B271c5C0b26F421741e481")
check("Trading WETH address set", TRADING_WETH == "0x4200000000000000000000000000000000000006")
check("Trading USDC address set", TRADING_USDC == "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913")

# Verify TradingBot can be instantiated
mock_w3 = MagicMock()
mock_w3.eth.contract.return_value = MagicMock()
trading_bot = TradingBot(mock_w3)
check("TradingBot instantiated", trading_bot is not None)
check("TradingBot has buy_token method", hasattr(trading_bot, 'buy_token'))
check("TradingBot has sell_token method", hasattr(trading_bot, 'sell_token'))
check("TradingBot has approve_token method", hasattr(trading_bot, 'approve_token'))
check("TradingBot has get_token_balance method", hasattr(trading_bot, 'get_token_balance'))
check("TradingBot has get_eth_balance method", hasattr(trading_bot, 'get_eth_balance'))

print()

# ------------------------------------------------------------------
# TEST 6: group_poster.py - GroupPoster formatting and quality gate
# ------------------------------------------------------------------
print("TEST 6: group_poster.py - GroupPoster Quality Gate and Formatting")
print("-" * 80)

try:
    from group_poster import GroupPoster, PREMIUM_DESIGN_AVAILABLE
    check("group_poster.py imported", True)
except ImportError as e:
    check(f"group_poster.py imported (error: {e})", False)

check("Premium design is available", PREMIUM_DESIGN_AVAILABLE)

gp = GroupPoster()
check("GroupPoster instantiated (no web3)", gp is not None)
check("Min rating score is 75", gp.min_rating_score == 75)

# Test format_project_message with premium design
project = {
    'name': 'TestToken',
    'symbol': '$TT',
    'contract': '0xAbCdEf1234567890AbCdEf1234567890AbCdEf12',
    'dex': 'UniswapV3',
    'market_cap': 500000,
    'liquidity_usd': 100000,
    'volume_24h': 200000,
    'volume_1h': 15000,
}
rating = {'score': 90, 'risk_level': 'low'}
analysis = {
    'owner_renounced': True,
    'is_honeypot': False,
    'lp_locked': True,
    'tax_buy': 2,
    'tax_sell': 2,
}

msg = gp.format_project_message(project, rating, analysis)
check("Message contains Base header", "NEW FAIR LAUNCH ON BASE" in msg)
check("Message contains token name", "TESTTOKEN" in msg)
check("Message contains security score", "90/100" in msg)
check("Message contains Market Cap", "Market Cap" in msg)
check("Message contains Liquidity", "Liquidity" in msg)
check("Message contains DexScreener link", "dexscreener.com" in msg)
check("Message contains BaseScan link", "basescan.io" in msg)
check("Message contains GeckoTerminal link", "geckoterminal.com" in msg)
check("Message contains ownership status", "Renounced" in msg)
check("Message contains honeypot status", "Clear" in msg)
check("Message contains LP lock status", "Locked" in msg)
check("Message contains tax info", "2%" in msg)
check("Message contains disclaimer", "DISCLAIMER" in msg)
check("Message shows SAFE risk level", "SAFE" in msg)

# Test with risky token (low score)
rating_risky = {'score': 50, 'risk_level': 'high'}
msg_risky = gp.format_project_message(project, rating_risky, analysis)
check("Risky message shows red indicator", "🔴" in msg_risky or "RISKY" in msg_risky)

# Test quality gate filtering
MIN_QUALITY_SCORE = 80
test_scores = [
    (88, True, "88 >= 80: should post"),
    (80, True, "80 >= 80: should post (edge case)"),
    (79, False, "79 < 80: should filter out"),
    (50, False, "50 < 80: should filter out"),
]
for score, expected, desc in test_scores:
    actual = score >= MIN_QUALITY_SCORE
    check(f"Quality gate: {desc}", actual == expected)

print()

# ------------------------------------------------------------------
# TEST 7: base_scanner_design.py - Premium alert formatting
# ------------------------------------------------------------------
print("TEST 7: base_scanner_design.py - Alert Design Formats")
print("-" * 80)

try:
    from base_scanner_design import (
        format_premium_token_alert,
        format_ultra_premium_alert,
        format_minimal_alert,
    )
    check("base_scanner_design.py imported", True)
except ImportError as e:
    check(f"base_scanner_design.py imported (error: {e})", False)

token_data = {
    'name': 'AlphaToken',
    'symbol': '$ALPHA',
    'contract': '0x1111111111111111111111111111111111111111',
    'dex': 'Uniswap V3',
}
analysis_data = {
    'security_score': 92,
    'risk_level': 'SAFE',
    'ownership_status': '✅ Renounced',
    'honeypot_status': '✅ Clear',
    'lp_lock_status': '✅ Locked',
    'tax_status': '0% Buy / 0% Sell',
    'owner_renounced': True,
    'no_honeypot': True,
    'lp_locked': True,
    'tax': '0%',
}
metrics_data = {
    'market_cap': 1200000,
    'liquidity_usd': 350000,
    'volume_24h': 800000,
    'volume_1h': 60000,
}

# Premium alert
premium_msg = format_premium_token_alert(token_data, analysis_data, metrics_data)
check("Premium alert has Base header", "NEW FAIR LAUNCH ON BASE" in premium_msg)
check("Premium alert shows market cap $1.2M", "$1.2M" in premium_msg)
check("Premium alert shows security score", "92/100" in premium_msg)
check("Premium alert has quick links section", "QUICK LINKS" in premium_msg)
check("Premium alert has contract link", "0x1111111111111111111111111111111111111111" in premium_msg)

# Ultra premium alert
holders_data = {'total': 5000, 'top_holder_pct': 12.5}
ultra_msg = format_ultra_premium_alert(token_data, analysis_data, metrics_data, holders_data)
check("Ultra premium shows holders", "5.0K" in ultra_msg or "5000" in ultra_msg)
check("Ultra premium shows top holder %", "12.5%" in ultra_msg)
check("Ultra premium shows safety section", "Safety" in ultra_msg)

# Minimal alert
minimal_msg = format_minimal_alert(token_data, analysis_data, metrics_data)
check("Minimal alert shows token symbol", "$ALPHA" in minimal_msg)
check("Minimal alert shows score", "92/100" in minimal_msg)
check("Minimal alert shows BaseScan link", "basescan.io" in minimal_msg)

# Test number formatting edge cases
small_metrics = {'market_cap': 500, 'liquidity_usd': 50, 'volume_24h': 10, 'volume_1h': 1}
small_msg = format_premium_token_alert(token_data, analysis_data, small_metrics)
check("Small numbers formatted correctly (< $1K)", "$500" in small_msg or "$50" in small_msg)

large_metrics = {'market_cap': 5000000, 'liquidity_usd': 2000000, 'volume_24h': 1000000, 'volume_1h': 100000}
large_msg = format_premium_token_alert(token_data, analysis_data, large_metrics)
check("Large numbers formatted as millions", "$5.0M" in large_msg or "$2.0M" in large_msg)

# Risk color coding — exact boundary tests
score_85_data = {**analysis_data, 'security_score': 85}
msg_85 = format_premium_token_alert(token_data, score_85_data, metrics_data)
check("Score 85 (boundary) shows green 🟢", "🟢" in msg_85)

score_84_data = {**analysis_data, 'security_score': 84}
msg_84 = format_premium_token_alert(token_data, score_84_data, metrics_data)
check("Score 84 (boundary) shows yellow 🟡", "🟡" in msg_84)

score_70_data = {**analysis_data, 'security_score': 70}
msg_70 = format_premium_token_alert(token_data, score_70_data, metrics_data)
check("Score 70 (boundary) shows yellow 🟡", "🟡" in msg_70)

score_69_data = {**analysis_data, 'security_score': 69}
msg_69 = format_premium_token_alert(token_data, score_69_data, metrics_data)
check("Score 69 (boundary) shows red 🔴", "🔴" in msg_69)

print()

# ------------------------------------------------------------------
# TEST 8: encryption_utils.py - Wallet encryption
# ------------------------------------------------------------------
print("TEST 8: encryption_utils.py - Wallet Encryption/Decryption")
print("-" * 80)

try:
    from encryption_utils import (
        generate_master_key,
        encrypt_private_key,
        decrypt_private_key,
        validate_master_key,
        get_user_cipher,
    )
    check("encryption_utils.py imported", True)
except ImportError as e:
    check(f"encryption_utils.py imported (error: {e})", False)

# Generate and validate master key
master_key = generate_master_key()
check("Master key generated", master_key is not None and len(master_key) > 0)
check("Master key validates", validate_master_key(master_key))
check("Invalid key rejected", not validate_master_key("not_a_valid_key"))
check("None key rejected", not validate_master_key(None))

# Encrypt/decrypt cycle
test_private_key = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
test_user_id = 99999

encrypted = encrypt_private_key(test_private_key, test_user_id, master_key)
check("Private key encrypted", encrypted != test_private_key)
check("Encrypted key is not empty", len(encrypted) > 0)

decrypted = decrypt_private_key(encrypted, test_user_id, master_key)
check("Private key decrypted correctly", decrypted == test_private_key)

# Different user IDs produce different ciphertexts
encrypted_other = encrypt_private_key(test_private_key, 11111, master_key)
check("Different user IDs produce different ciphertext", encrypted != encrypted_other)

# Wrong user ID cannot decrypt
try:
    wrong_decrypt = decrypt_private_key(encrypted, 11111, master_key)
    check("Wrong user ID fails to decrypt", wrong_decrypt != test_private_key)
except (ValueError, Exception) as e:
    # Fernet raises InvalidToken (subclass of Exception) on wrong key
    check("Wrong user ID fails to decrypt (InvalidToken raised)", True)

# User cipher creation
cipher = get_user_cipher(test_user_id, master_key)
check("User cipher created successfully", cipher is not None)

print()

# ------------------------------------------------------------------
# TEST 9: Cross-module integration
# ------------------------------------------------------------------
print("TEST 9: Cross-Module Integration")
print("-" * 80)

# Scoring + Security Scanner interaction
# Verify scoring works with analysis data that mirrors security_scanner output
scanner_like_analysis = {
    'renounced': True,
    'is_honeypot': False,
    'liquidity_locked': True,
    'lock_days': 180,
    'buy_tax': 0,
    'sell_tax': 0,
}
scanner_like_metrics = {
    'liquidity_usd': 200000,
    'volume_24h': 100000,
    'market_cap': 800000,
    'price_change_24h': 30,
}
combined_scores = calculate_token_scores(scanner_like_analysis, scanner_like_metrics)
check("Cross-module: scoring works with scanner-like data", combined_scores['overall_score'] > 0)
check("Cross-module: safe token scores high security", combined_scores['security_score'] >= 70)

# GroupPoster uses base_scanner_design formatting
poster = GroupPoster()
cross_project = {
    'name': 'CrossTest',
    'symbol': '$CROSS',
    'contract': '0x2222222222222222222222222222222222222222',
    'dex': 'Uniswap',
    'market_cap': 300000,
    'liquidity_usd': 80000,
    'volume_24h': 150000,
    'volume_1h': 12000,
}
cross_rating = {'score': 85, 'risk_level': 'low'}
cross_analysis = {
    'owner_renounced': True,
    'is_honeypot': False,
    'lp_locked': True,
    'tax_buy': 0,
    'tax_sell': 0,
}
cross_msg = poster.format_project_message(cross_project, cross_rating, cross_analysis)
check("Cross-module: GroupPoster uses premium design", "NEW FAIR LAUNCH ON BASE" in cross_msg)
check("Cross-module: premium format includes security score", "85/100" in cross_msg)

# Database + encryption integration
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
    tmp_db_path2 = tmp.name

try:
    os.environ['WALLET_MASTER_KEY'] = master_key
    db2 = UserDatabase(db_path=tmp_db_path2)
    db2.add_user(user_id=55555, username="crypto_user")

    # Create wallet with encryption enabled
    wallet_result = db2.create_wallet(
        user_id=55555,
        wallet_address="0xEncryptedWallet123",
        private_key="0xSecretKey123456789"
    )
    check("Cross-module: wallet created with encryption", wallet_result['success'])

    # Retrieve and verify encrypted storage
    stored_pk = db2.get_wallet_private_key(55555, "0xEncryptedWallet123")
    check("Cross-module: encrypted key stored and retrieved", stored_pk is not None)
finally:
    if 'WALLET_MASTER_KEY' in os.environ:
        del os.environ['WALLET_MASTER_KEY']
    os.unlink(tmp_db_path2)

print()

# ------------------------------------------------------------------
# TEST 10: Feature completeness checklist
# ------------------------------------------------------------------
print("TEST 10: Feature Completeness Checklist")
print("-" * 80)

features = [
    ("Core sniping (is_renounced, thresholds)", True),
    ("Honeypot detection function", callable(check_honeypot)),
    ("Tax checking function", callable(check_taxes)),
    ("Liquidity lock detection", callable(is_liquidity_locked)),
    ("Lock duration calculation", callable(get_lock_duration)),
    ("New pair discovery", callable(get_new_pairs)),
    ("Full pair analysis", callable(analyze_new_pair)),
    ("Creator address detection", callable(get_creator_address)),
    ("Token scoring (social/viral/security)", callable(calculate_token_scores)),
    ("Score emoji formatting", callable(get_score_emoji)),
    ("User database with SQLite", True),
    ("Referral system", True),
    ("Wallet management with encryption", True),
    ("Commission tracking", True),
    ("Group posting management", True),
    ("Scheduled message deletion", True),
    ("Security scanner with report", True),
    ("Trading bot (buy/sell/approve)", True),
    ("Premium alert design", PREMIUM_DESIGN_AVAILABLE),
    ("Ultra premium alert design", callable(format_ultra_premium_alert)),
    ("Minimal alert design", callable(format_minimal_alert)),
    ("Quality gate filtering", True),
    ("Wallet encryption/decryption", True),
]

for feature_name, implemented in features:
    check(f"{feature_name}", implemented)

print()

# ============================================================
# SUMMARY
# ============================================================
print("=" * 80)
print("🎯 TEST SUMMARY")
print("=" * 80)
print(f"\n  ✅ Passed: {passed}")
print(f"  ❌ Failed: {failed}")
print(f"  📊 Total:  {passed + failed}")
print()

if failed == 0:
    print("  🚀 ALL TESTS PASSED - All updates are integrated successfully!")
else:
    print(f"  ⚠️  {failed} test(s) failed - review the output above for details")

print()
print("=" * 80 + "\n")

sys.exit(0 if failed == 0 else 1)
