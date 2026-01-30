# ✅ Testing Your Bot - Quick Guide

## You just opened the GitHub Actions page. Here's what to do:

### **Step 1: Trigger a Test Run**
1. On the Actions page, click **"Fair Launch Sniper"** workflow (on the left sidebar)
2. Click the blue **"Run workflow"** button (top right)
3. Click **"Run workflow"** again in the popup
4. Wait 5-10 seconds and refresh the page

### **Step 2: Check the Results**
1. You should see a new workflow run appear (yellow dot = running, green checkmark = success)
2. Click on the workflow run to see details
3. Click on **"scan"** job to see the logs

### **What to Look For:**

✅ **SUCCESS - You should see:**
```
Using Alchemy key: RiA4S5DS...enZ
Running in scan-only mode
Scan complete. Found 0 fair launches.
```

❌ **FAILURE - If you still see:**
```
401 Client Error: Unauthorized
```
Then the secret wasn't updated correctly.

---

## After It Works

Once you see the green checkmark ✅:
- The bot will automatically scan every 5 minutes
- You'll get Telegram alerts when fair launches are detected
- No further action needed!

---

## Need Help?

If it's still failing, let me know what error you see in the logs and I'll help troubleshoot.
