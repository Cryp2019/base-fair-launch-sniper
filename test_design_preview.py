#!/usr/bin/env python3
"""Test script to preview the new premium design format"""

from group_poster import GroupPoster, PREMIUM_DESIGN_AVAILABLE

print("=" * 70)
print("✨ PREMIUM DESIGN TEST - Full Message Preview")
print("=" * 70)
print(f"\n✅ PREMIUM_DESIGN_AVAILABLE: {PREMIUM_DESIGN_AVAILABLE}\n")

gp = GroupPoster()

# High quality project (88/100 score - will be posted)
test_project = {
    'name': 'BaseGold Token',
    'symbol': '$BGT',
    'contract': '0xAbCd1234EF5678901234567890aBcDEF12345678',
    'dex': 'UniswapV3',
    'market_cap': 450000,
    'liquidity_usd': 125000,
    'volume_24h': 320000,
    'volume_1h': 25000
}

test_rating = {
    'score': 88,
    'risk_level': 'low'
}

test_analysis = {
    'owner_renounced': True,
    'is_honeypot': False,
    'lp_locked': True,
    'tax_buy': 1,
    'tax_sell': 1
}

msg = gp.format_project_message(test_project, test_rating, test_analysis)
print("THIS IS WHAT WILL BE POSTED TO GROUPS:\n")
print(msg)
print("\n" + "=" * 70)
print("\nBased on the design, here's what you'll see when bot runs:")
print("  ✅ Base chain header with 🟢 safety indicator")
print("  ✅ Token name and symbol with color coding")
print("  ✅ Market metrics (liquidity, market cap, volume)")
print("  ✅ Security analysis (ownership, honeypot, LP lock status)")
print("  ✅ Base chain links (BaseScan, DexScreener, GeckoTerminal)")
print("  ✅ Buy button below the message")
print("\nNote: The bot will ONLY post projects with 80+ security score")
print("=" * 70)
