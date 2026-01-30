# 🚀 Deploy to Render.com (FREE)

## Quick Setup (5 minutes)

### Step 1: Push Code to GitHub

```bash
cd e:\base-fair-launch-sniper
git add .
git commit -m "Add Render deployment files"
git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Click **"Get Started for Free"**
3. Sign up with GitHub (easiest)

### Step 3: Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `Cryp2019/base-fair-launch-sniper`
3. Configure:
   - **Name:** `base-fair-launch-sniper`
   - **Region:** Oregon (US West) - cheapest
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python public_bot.py`
   - **Instance Type:** **Free** (select this!)

### Step 4: Add Environment Variables

In Render dashboard, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | `8145491592:AAHVZ8xcr3q8i3ahsDuxJyt_F-aLXgRf4TE` |
| `ALCHEMY_BASE_KEY` | `RiA4S5DS3ZpgokvFCOenZ` |
| `TELEGRAM_CHAT_ID` | `@base_fair_launch_alerts` |

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait 2-3 minutes for deployment
3. Bot will start automatically!

---

## ✅ Verify It's Working

1. Open Telegram
2. Search for `@base_fair_launch_bot`
3. Send `/start`
4. You should get a response!

---

## 📊 Free Tier Limits

- **Cost:** $0/month (FREE forever)
- **Uptime:** 750 hours/month (enough for 24/7)
- **RAM:** 512 MB (plenty for this bot)
- **Bandwidth:** 100 GB/month
- **Sleeps after 15 min inactivity** (wakes up instantly when user messages)

---

## 🔄 Alternative: Railway.app (Also Free)

If Render doesn't work, try Railway:

1. Go to https://railway.app
2. Sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select `base-fair-launch-sniper`
5. Add environment variables (same as above)
6. Deploy!

**Free tier:** $5 credit/month (enough for this bot)

---

## 🎯 After Deployment

Your bot will run 24/7 for FREE and respond to all commands:
- `/start` - Welcome message
- `/refer` - Get referral link
- `/stats` - View statistics
- `/leaderboard` - Top referrers
- `/alerts` - Toggle notifications
- `/howitworks` - Verification info

---

## 🐛 Troubleshooting

**Bot not responding?**
- Check Render logs (click "Logs" tab)
- Verify environment variables are set
- Make sure bot is not sleeping (send a message to wake it)

**Deployment failed?**
- Check build logs for errors
- Verify `requirements.txt` is correct
- Try Railway.app as alternative

---

## 💰 Cost Comparison

| Service | Free Tier | Best For |
|---------|-----------|----------|
| **Render.com** | ✅ Free forever | Best choice! |
| **Railway.app** | $5 credit/month | Good alternative |
| **Heroku** | ❌ No free tier | Not recommended |
| **Fly.io** | $5 credit/month | More complex |

**Recommendation: Use Render.com** - it's the easiest and truly free!
