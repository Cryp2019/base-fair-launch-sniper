# 🎯 TOP PERFORMERS & SPONSORSHIP SYSTEM

## Overview
New monetization system for the sniper bot that:
1. **Tracks top performing tokens** - Real-time dashboard of best launchers
2. **Offers sponsorship packages** - Projects can pay to get featured/promoted
3. **Generates revenue** - Multiple ad tier options from $99 to $1,299

---

## 🚀 TOP PERFORMERS DASHBOARD

### Command: `/top`
Displays the best performing tokens from the last 24 hours

**Shows:**
- 🏆 Top 15 tokens ranked by price increase
- 📈 Price increase % (with rocket emojis for explosive gains)
- 💰 Market cap and 24h volume
- 👥 Holder count & security score
- ⭐ "Get Featured" button

**Example Output:**
```
📊 TOP PERFORMERS (Last 24 Hours)

🥇 GoldenToken ($GOLD)
   🚀🚀🚀 +850.5%
   💰 MC: $2.5M | Vol: $450K
   👥 1,250 holders | 🛡️ 87/100

🥈 MoonLaunch ($MOON)
   🚀🚀 +320.2%
   💰 MC: $1.8M | Vol: $280K
   👥 980 holders | 🛡️ 82/100
```

---

## 💰 SPONSORSHIP PACKAGES & AD RATES

### 1. Featured 48-Hour Boost
**Price: $199 USD**
- 📌 Pinned to top of launch alerts
- ⭐ Featured badge on all posts
- 🔔 Broadcast alert to all users
- 📊 Analytics dashboard

**Best for:** Quick publicity, fast launch

### 2. Featured 1-Week Premium ⭐ POPULAR
**Price: $499 USD**  
- 📌 Premium position for 7 days
- 👑 Purple badge on all posts
- 🔔 3-5 promotional broadcasts
- 📈 Full performance analytics
- 💬 Community boost post

**Best for:** Established projects, sustained growth

### 3. Featured 30-Day Top Tier 👑 PREMIUM
**Price: $1,299 USD**
- 📌 Premium position for full month
- 🏆 Gold badge on all posts
- 🔔 Daily promotional alerts
- 📊 Complete analytics dashboard
- 💬 Daily community mentions
- 📱 Mobile notification priority

**Best for:** Enterprise launches, long-term visibility

### 4. Broadcast Alert Single
**Price: $99 USD**
- 📢 One-time broadcast to all users
- ⭐ Highlighted format
- 📊 Click analytics

**Best for:** Budget option, single promotion

### 5. Top Performers List (24h)
**Price: $299 USD**
- 🚀 Featured in top performers dashboard
- 📊 Performance tracking & ranking
- 🔄 Automatic updates every hour

**Best for:** Confident about project performance

---

## 📱 User Commands

### `/top` - View Top Performers
Shows live dashboard of best performing tokens

### `/featured` - Sponsorship Packages
Displays all ad packages and pricing
- Can contact support to book package
- Bulk discounts available
- Custom packages negotiable

---

## 🎯 IMPLEMENTATION STATUS

### ✅ Created Files
1. **sponsored_projects.py** - Core sponsorship system
   - `SponsoredProjects` class with database integration
   - Functions to add/track sponsored projects
   - Function to query top performers
   - AD_RATES dictionary with all pricing

2. **top_performers.py** - User-facing commands
   - `/top` command handler
   - `/featured` command handler
   - Performance ranking and display
   - Integration with sponsored_projects

### 🔄 Integration Points
- Database: Uses existing `users.db` with new tables
  - `sponsored_projects` - Track paid sponsorships
  - `top_performers` - Auto-track performance metrics
  
- Bot Commands: Ready to register with main bot
  - `/top` - View top performers
  - `/featured` - View sponsorship options

---

## 💳 PAYMENT FLOW

1. **Project contacts support** → Requests sponsorship package
2. **Support generates invoice** → USDC payment address on Base
3. **Project pays USDC** → Payment confirmed on-chain
4. **Admin activates sponsorship** → Project marked as sponsored
5. **Bot automatically features** → Premium badges, promotions start
6. **Analytics tracked** → Clicks, impressions, performance

---

## 📊 REVENUE MODEL

| Package | Price | Margin | Est. Monthly |
|---------|-------|--------|--------------|
| 48h Featured | $199 | ~$150 | 1-2 per week = $300-600 |
| 7d Featured | $499 | ~$350 | 2-3 per week = $700-1,050 |
| 30d Featured | $1,299 | ~$950 | 1-2 per month = $950-1,900 |
| Single Broadcast | $99 | ~$70 | 5-10 per week = $350-700 |
| Top Performers | $299 | ~$200 | 2-3 per month = $400-600 |

**Estimated Monthly Revenue (Conservative):** $2,700-4,850

**Key Factors:**
- Growing user base = higher pricing power
- Quality filter (80+) = exclusive sponsors
- Real performance tracking = credibility
- Daily broadcasts = multiple monetization touch points

---

## 🎨 Featured Badge Display Examples

### 48h Featured
```
⭐ NEW FAIR LAUNCH ON BASE 🟢

<b>💊 BASEGOLDTOKEN</b> | <code>$BGT</code>
⭐ <b>FEATURED (48-Hour Boost)</b>

📊 METRICS
💰 Market Cap: $450.0K
💧 Liquidity: $125.0K
...
```

### 7d Featured  
```
👑 NEW FAIR LAUNCH ON BASE 🟢

<b>💊 BASEGOLDTOKEN</b> | <code>$BGT</code>
👑 <b>FEATURED (1-Week Premium)</b>

📊 METRICS
...
```

### 30d Featured
```
🏆 NEW FAIR LAUNCH ON BASE 🟢

<b>💊 BASEGOLDTOKEN</b> | <code>$BGT</code>
🏆 <b>FEATURED (30-Day Premium)</b>

📊 METRICS
...
```

---

## 🔧 HOW TO INTEGRATE

### Add to sniper_bot.py:

```python
from sponsored_projects import SponsoredProjects
from top_performers import register_top_performers_handlers

# In main():
sponsored = SponsoredProjects('users.db')

# When setting up handlers:
register_top_performers_handlers(app, sponsored)
```

### Register Commands:
```python
from telegram.ext import CommandHandler
app.add_handler(CommandHandler('top', top_performers_handler))
app.add_handler(CommandHandler('featured', featured_handler))
```

---

## 📈 TRACKING INTEGRATION

When a token is posted:
1. **Check if sponsored** → Add featured badge
2. **Track performance** → Log metrics to top_performers table
3. **Increment views** → Count impressions/clicks
4. **Update rankings** → Real-time top performers dashboard

---

## 🎯 NEXT STEPS

1. ✅ Sponsorship system created
2. ✅ Top performers tracking ready
3. 🔄 **TODO:** Integrate with sniper_bot.py main handlers
4. 🔄 **TODO:** Add payment processing integration
5. 🔄 **TODO:** Create admin dashboard for sponsorship management
6. 🔄 **TODO:** Track and display sponsored badge on all messages

---

## 💡 BUSINESS LOGIC

**Quality Filter Ensures Premium Sponsors:**
- Only 80+ security score tokens are featured
- Protects sponsor reputation
- Increases advertiser ROI
- Users trust featured projects

**Performance-Based Ranking:**
- Top performers determined by real metrics
- Organic growth + paid promotion
- Users see actual winners
- Attracts more quality project sponsors

**Multiple Touchpoints:**
- Dashboard views = impressions
- Alerts = engagement
- Links = conversions
- Analytics = ROI tracking
