"""
Delete Telegram webhook to enable polling mode
Run this if bot is not responding to commands
"""
import os
import requests

# Get bot token from environment or paste it here
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN') or 'YOUR_BOT_TOKEN_HERE'

if 'YOUR_BOT_TOKEN' in BOT_TOKEN:
    print("❌ Please set TELEGRAM_TOKEN environment variable or edit this file")
    print("   Get your token from Railway environment variables")
    exit(1)

# Check current webhook
print("🔍 Checking current webhook...")
response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo')
webhook_info = response.json()

if webhook_info.get('result', {}).get('url'):
    print(f"⚠️  Webhook is set to: {webhook_info['result']['url']}")
    print("   This prevents polling from working!")
    
    # Delete webhook
    print("\n🗑️  Deleting webhook...")
    delete_response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook')
    
    if delete_response.json().get('ok'):
        print("✅ Webhook deleted successfully!")
        print("\n📝 Next steps:")
        print("   1. Restart your Railway bot")
        print("   2. Try /start command again")
        print("   3. Bot should respond now!")
    else:
        print(f"❌ Failed to delete webhook: {delete_response.text}")
else:
    print("✅ No webhook set - polling should work")
    print("\n🤔 If bot still not responding, check:")
    print("   1. Bot is running on Railway (check logs)")
    print("   2. No other bot instances running with same token")
    print("   3. Bot token is correct in Railway environment")
