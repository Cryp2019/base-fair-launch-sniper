# 🚂 Railway.app Deployment (Easiest Option)

## Why Railway Instead of Render?

- ✅ Automatically uses correct Python version
- ✅ Simpler setup (3 clicks)
- ✅ $5 free credit/month (enough for this bot)
- ✅ No Python version issues

---

## Step-by-Step Setup (2 minutes)

### 1. Sign Up
- Railway.app should be open in your browser
- Click **"Login"** (top right)
- Choose **"Login with GitHub"**
- Authorize Railway to access your repos

### 2. Create New Project
- Click **"New Project"**
- Select **"Deploy from GitHub repo"**
- Find and click: `Cryp2019/base-fair-launch-sniper`

### 3. Add Environment Variables
Railway will start deploying automatically. Now add your secrets:

- Click on your deployed service
- Go to **"Variables"** tab
- Click **"+ New Variable"** and add these 3:

| Variable Name | Value |
|---------------|-------|
| `TELEGRAM_BOT_TOKEN` | `8145491592:AAHVZ8xcr3q8i3ahsDuxJyt_F-aLXgRf4TE` |
| `ALCHEMY_BASE_KEY` | `RiA4S5DS3ZpgokvFCOenZ` |
| `TELEGRAM_CHAT_ID` | `@base_fair_launch_alerts` |

### 4. Redeploy
- After adding variables, click **"Deploy"** (top right)
- Wait 2-3 minutes

### 5. Check Logs
- Click **"Deployments"** tab
- Click the latest deployment
- You should see:
  ```
  ✅ Bot started successfully!
  📱 Bot username: @base_fair_launch_bot
  ```

---

## ✅ Test It

1. Open Telegram
2. Search for `@base_fair_launch_bot`
3. Send `/start`
4. You should get a response! 🎉

---

## 💰 Cost

- **Free tier:** $5 credit/month
- **Your bot usage:** ~$0.50/month
- **Runs 24/7 for free!**

---

## 🐛 If It Fails

Check the deployment logs in Railway. If you see any errors, copy and paste them to me.

---

## After It Works

Once the simple bot is working, I'll switch it back to `public_bot.py` with the full referral system!
