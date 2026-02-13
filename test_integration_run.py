import asyncio
import os
import logging

# Ensure we can import the bot
from sniper_bot import post_to_group_with_buy_button, db, security_scanner, group_poster

# Monkeypatch security scanner to always return high score
def fake_scan(token_address):
    return {
        'score': 95,
        'ownership_renounced': True,
        'is_honeypot': False,
        'lp_locked': True,
        'buy_tax': 0,
        'sell_tax': 0,
        'transfer_tax': 0
    }

security_scanner.scan_token = fake_scan

# Ensure a test group exists in DB
TEST_GROUP_ID = -1001234567890
try:
    db.add_group(TEST_GROUP_ID, 'test_group', 'Test Group')
except Exception as e:
    print(f"DB add_group error (continuing): {e}")

# Dummy app with bot.send_message
class DummyBot:
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        print(f"[DummyBot] send_message to {chat_id}, parse_mode={parse_mode}\n{text[:200]}...\n")

class DummyApp:
    def __init__(self):
        self.bot = DummyBot()

# Build fake analysis and metrics
analysis = {
    'token_address': '0x0000000000000000000000000000000000000000',
    'name': 'TestToken',
    'symbol': 'TST',
    'pair_address': '0x1111111111111111111111111111111111111111',
    'dex_name': 'TestDEX',
    'base_token': 'USDC',
}
metrics = {
    'liquidity_usd': 10000,
    'market_cap': 50000,
    'volume_24h': 1000,
    'volume_1h': 50
}

async def main():
    app = DummyApp()
    await post_to_group_with_buy_button(app, analysis, metrics)

if __name__ == '__main__':
    asyncio.run(main())
