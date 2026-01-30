# 🔍 Base Fair Launch Sniper

**A free Telegram bot that alerts you to truly fair-launched tokens on Base chain** – filtering out 95% of rugs.

> **Note**: This is a Telegram bot, not a web service. All alerts are delivered via Telegram messages.

✅ Renounced ownership  
✅ <5% pre-mine  
✅ Locked liquidity (30+ days)  
✅ No hidden tax functions  

⚠️ **DISCLAIMER**: Not financial advice. 99% of new tokens fail. Always DYOR.

---

## 📲 Join Alerts Channel
[@base_fair_launch_alerts](https://t.me/base_fair_launch_alerts)

---

## 🤔 Why This Exists
I got rugged 3 times on Base in 2 weeks. Built this to save others from losing money.

- **No token** – pure utility tool
- **No fees** – completely free
- **Open source** – verify the code yourself

---

## 🛡️ How Verification Works
1. **Ownership Check** → Confirms contract sent to burn address
2. **Pre-mine Analysis** → Creator holds <5% of supply
3. **Liquidity Lock** → LP tokens locked via Unicrypt/Team Finance
4. **Tax Screening** → Flags hidden tax functions

⚠️ **Limitations**: Cannot detect all honeypots. Always test with <$10 first.

---

## 🚀 Quick Start

### 1. Get API Keys
- **Telegram Bot Token**: Visit [@BotFather](https://t.me/BotFather) → `/newbot`
- **Alchemy Base Key**: [dashboard.alchemy.com](https://dashboard.alchemy.com) → Create App → Base Mainnet (free tier)

### 2. Local Setup
```bash
# Clone repository
git clone https://github.com/your-username/base-fair-launch-sniper.git
cd base-fair-launch-sniper

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here
ALCHEMY_BASE_KEY=your_alchemy_key_here
TELEGRAM_CHAT_ID=@your_channel_or_chat_id" > .env

# Run locally
python bot.py
```

### 3. Deploy to GitHub Actions (Free 24/7 Scanning)
```bash
# Push to GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/base-fair-launch-sniper.git
git push -u origin main

# Add secrets in GitHub repo settings
# Settings → Secrets and variables → Actions → New repository secret
# Add: TELEGRAM_BOT_TOKEN, ALCHEMY_BASE_KEY, TELEGRAM_CHAT_ID
```

The bot will automatically scan every 5 minutes via GitHub Actions (completely free).

---

## 🔧 Configuration

### Environment Variables
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from BotFather
- `ALCHEMY_BASE_KEY` - Your Alchemy API key for Base mainnet
- `TELEGRAM_CHAT_ID` - Channel/chat ID for alerts (e.g., `@your_channel`)

### Thresholds (edit in `bot.py`)
```python
MAX_PREMINE_RATIO = 0.05  # 5% max creator holding
MIN_LIQUIDITY_LOCK_DAYS = 30  # Minimum lock duration
MAX_TAX_PERCENT = 5  # Maximum acceptable tax
```

---

## 🤖 Bot Commands
- `/start` - Welcome message and overview
- `/howitworks` - Detailed verification explanation
- `/scan` - Manually trigger a scan for new pairs

---

## 📊 How It Works

### 1. Pool Detection
Monitors Uniswap V3 Factory on Base for new USDC pairs:
```python
FACTORY_ADDRESS = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
```

### 2. Fair Launch Checks
For each new token:
- ✅ **Ownership**: Checks if `owner()` returns burn address
- ✅ **Pre-mine**: Calculates creator balance / total supply
- ✅ **Liquidity Lock**: Verifies LP tokens in Unicrypt/Team Finance
- ✅ **Taxes**: Scans for suspicious tax-related functions

### 3. Alert System
Sends Telegram messages with:
- Token name, symbol, addresses
- Pass/fail status for each check
- Direct links to Basescan
- Risk disclaimer

---

## ⚠️ Limitations

This bot **CANNOT** detect:
- **Honeypots** (requires paid simulation services)
- **Backdoors** in contract code
- **Social engineering** scams
- **Rug pulls** after initial checks pass

**Always**:
- Test with small amounts (<$10)
- Read the contract code on Basescan
- Check team social media presence
- Never invest more than you can afford to lose

---

## 💡 Found a Bug?
[Open an issue](https://github.com/your-username/base-fair-launch-sniper/issues) – I review all PRs.

---

## 🙏 Support Development
This is free because I believe in protecting retail traders. If it saves you from a rug:
- ⭐ Star this repo
- 🔗 Share with one friend who trades Base tokens
- 💰 [Apply for Base Ecosystem Grants](https://base.org/ecosystem) to fund further development

---

## 📜 License
MIT License - Use at your own risk. Not financial advice.
