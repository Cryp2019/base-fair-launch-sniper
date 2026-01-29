# GitHub Actions Secrets Setup

## Required Secrets

Add these three secrets to your GitHub repository:

### 1. TELEGRAM_BOT_TOKEN
**Name:** `TELEGRAM_BOT_TOKEN`
**Value:**
```
8145491592:AAHVZ8xcr3q8i3ahsDuxJyt_F-aLXgRf4TE
```

---

### 2. ALCHEMY_BASE_KEY
**Name:** `ALCHEMY_BASE_KEY`
**Value:**
```
RiA4S5DS3ZpgokvFCOenZ
```

---

### 3. TELEGRAM_CHAT_ID
**Name:** `TELEGRAM_CHAT_ID`
**Value:**
```
@base_fair_launch_alerts
```

---

## How to Add Secrets

1. Go to: https://github.com/Cryp2019/base-fair-launch-sniper/settings/secrets/actions
2. Click **"New repository secret"** button
3. Enter the **Name** (exactly as shown above)
4. Paste the **Secret** value
5. Click **"Add secret"**
6. Repeat for all three secrets

---

## After Adding Secrets

Once all three secrets are added:

1. Go to **Actions** tab: https://github.com/Cryp2019/base-fair-launch-sniper/actions
2. Click on **"Fair Launch Sniper"** workflow
3. Click **"Run workflow"** → **"Run workflow"** to test
4. The workflow will automatically run every 5 minutes after that

---

## Verify It's Working

- Check the Actions tab for green checkmarks ✅
- You should receive Telegram alerts when fair launches are detected
- Logs will show scanning activity every 5 minutes
