# SPONSORSHIP ELIGIBILITY REQUIREMENTS

## Overview
Projects MUST meet strict quality requirements to use paid sponsorship options. This prevents scam projects from buying featured status and protects bot reputation.

---

## ✅ Eligibility Checklist

### MANDATORY Requirements (All Must Be Met)

#### 1. Security Score: 80+ (Out of 100)
```
✓ Required: Minimum 80/100
✗ Below 80: REJECTED - Sponsorship payment REFUNDED
```
- Prevents low-quality projects
- Same as posting to groups
- Enforced at payment processing

#### 2. Ownership MUST Be Renounced
```
✓ Renounced: ELIGIBLE
✗ Not Renounced: REJECTED
```
- **Why**: Prevents rug pulls
- **What it means**: Owner cannot control token
- **Check**: `ownership_renounced == True`

#### 3. NO Honeypot Detection
```
✓ Clear (No honeypot): ELIGIBLE
✗ Honeypot detected: REJECTED
```
- **Why**: Honeypot = scam token
- **What it means**: Users can actually sell tokens
- **Check**: `is_honeypot == False`

#### 4. Liquidity MUST Be Locked
```
✓ LP Locked: ELIGIBLE
✗ LP Not Locked: REJECTED
```
- **Why**: Prevents liquidity rug pulls
- **What it means**: LP provider can't steal liquidity
- **Check**: `lp_locked == True`

#### 5. Reasonable Taxes (Maximum)
```
Buy Tax:      ≤ 10%
Sell Tax:     ≤ 10%
Transfer Tax: ≤ 5%

Examples:
✓ 2% buy / 2% sell = ELIGIBLE
✓ 5% buy / 8% sell = ELIGIBLE
✗ 20% buy / 25% sell = REJECTED (excessive)
✗ 0% buy / 50% sell = REJECTED (rug risk)
```

---

## 📊 Real Examples

### ELIGIBLE Project (99% Approval Rate)
```
Token: LegitToken
Security Score: 88/100          ✓ Above 80
Ownership: Renounced            ✓ Safe
Honeypot: Clear                 ✓ No scam
LP Status: Locked               ✓ Safe
Buy Tax: 2%                     ✓ Reasonable
Sell Tax: 3%                    ✓ Reasonable
Transfer Tax: 0%                ✓ Reasonable

Result: ✅ ELIGIBLE FOR SPONSORSHIP
```

### INELIGIBLE Project (Rejected)
```
Token: ScamToken123
Security Score: 65/100          ✗ Below 80
Ownership: Active (Not Renounced) ✗ Rug risk
Honeypot: YES                   ✗ Scam
LP Status: Unlocked             ✗ Rug risk
Buy Tax: 15%                    ✗ Too high
Sell Tax: 50%                   ✗ Way too high
Transfer Tax: 10%               ✗ Too high

Result: ❌ REJECTED (Multiple failures)
```

---

## 🔍 Automatic Verification Flow

```
Project Sends Payment
        ↓
Payment Detected
        ↓
Check Eligibility Requirements
        ├─ Security Score 80+?          
        ├─ Ownership Renounced?         
        ├─ No Honeypot?                 
        ├─ LP Locked?                   
        └─ Reasonable Taxes?            
        ↓
All Pass? → APPROVE & ACTIVATE
        ↓
Any Fail? → REJECT & REFUND PAYMENT
```

---

## 💰 What Happens If Requirements Not Met

### Payment Processing:
1. **Project sends USDC payment**
2. **Bot detects payment**
3. **Bot checks eligibility**
4. **Eligibility check FAILS**
5. **Payment marked as rejected**
6. **NO SPONSORSHIP ACTIVATED**
7. **Admin notified of rejection**
8. **Project notified via support ticket**

### Why Rejection Happens:
- ❌ Security score too low (protection against rugs)
- ❌ Ownership not renounced (rug pull risk)
- ❌ Honeypot detected (scam token)
- ❌ LP not locked (liquidity rug risk)
- ❌ Taxes too high (potential scam)

---

## 📋 Eligibility Requirements Matrix

| Requirement | Minimum | Maximum | Why |
|-------------|---------|---------|-----|
| Security Score | 80/100 | - | Quality gate |
| Ownership | Renounced | - | No rug pulls |
| Honeypot | No | No | Not a scam |
| LP Lock | Required | - | Liquidity safe |
| Buy Tax | 0% | 10% | Reasonable |
| Sell Tax | 0% | 10% | Reasonable |
| Transfer Tax | 0% | 5% | Reasonable |

---

## 🛡️ How This Protects Users

### Before Sponsorship:
- Users see all tokens (good + bad)
- Can't distinguish quality
- Scam projects get same exposure as legit ones

### With Sponsorship & Eligibility:
- ✅ Only 80+ projects can pay for featured status
- ✅ Users trust featured projects more
- ✅ Scammers can't buy credibility
- ✅ Featured = actually vetted
- ✅ Bot reputation stays strong

---

## 💡 Requirements Explanation

### Why Security Score 80+?
```
0-40: Likely scam, many red flags
40-60: Risky, multiple issues
60-80: Borderline, some concerns
80-100: Quality, limited issues
↓
Only 80+ gets featured badge
Prevents sponsoring unknown/risky projects
```

### Why Ownership Renounced?
```
If NOT renounced:
→ Owner can change contract
→ Owner can add sell restrictions
→ Owner can freeze transfers
→ Owner can rug pull
↓
MUST be renounced for sponsorship
```

### Why No Honeypot?
```
Honeypot = Token sells but can't resell
Users buy → Can't sell → Trapped
→ Classic scam structure
↓
If honeypot detected = REJECT
```

### Why LP Must Be Locked?
```
If NOT locked:
→ LP provider can remove all liquidity
→ Price crashes → Users lose money
→ Liquidity rug pull
↓
MUST be locked for sponsorship
```

### Why Tax Limits?
```
0% tax: Too good to be true? Maybe
5% tax: Reasonable, normal
10% tax: High but acceptable
15%+ tax: Suspicious, possible scam
50%+ tax: Definite scam
↓
Limits protect against hidden rug mechanics
```

---

## 📲 User-Facing Message

When a project tries to buy sponsorship but FAILS eligibility:

```
❌ SPONSORSHIP REQUEST REJECTED

Your project does not meet our quality requirements.

REASONS:
• Security Score: 65/100 (minimum 80 required)
• Ownership: Not Renounced (rug pull risk)
• Sell Tax: 25% (maximum 10% allowed)

To become eligible:
1. Renounce ownership
2. Improve security score (fix any issues)
3. Reduce taxes to reasonable levels

After improvements, you can try again.
Contact support@bot.com for assistance.
```

---

## ✨ Benefits of Strict Requirements

### For Users:
- ✅ Featured projects are actually vetted
- ✅ Can trust sponsored tokens more
- ✅ Protected from scams buying exposure
- ✅ Higher quality recommendations

### For You:
- ✅ Bot reputation stays strong
- ✅ No scam projects on featured list
- ✅ Users more likely to trade featured projects
- ✅ Higher revenue (quality sponsors pay more)

### For Legitimate Projects:
- ✅ Featured status means something
- ✅ Verified by automated system
- ✅ Competes with other quality projects only
- ✅ Users trust featured badge

---

## 🔐 Implementation Details

### Eligibility Check Location:
```python
# In automated_sponsorship.py
def check_project_eligibility(token_address):
    # Verifies all requirements BEFORE payment activation
    # Logs all failures for admin review
    # Returns eligible/not eligible + reason
```

### When Check Runs:
1. **Payment received** from project
2. **Eligibility check triggered** automatically
3. **All requirements verified** against security_scanner
4. **If ANY requirement fails** → Payment rejected
5. **If ALL requirements pass** → Sponsorship activated

### Automatic Enforcement:
- ✅ No manual review needed
- ✅ Instant feedback to project
- ✅ Transparent criteria
- ✅ On-chain verifiable

---

## 📞 Support for Projects

When projects ask "Why was my payment rejected?":

```
Standard Response Template:

"Our sponsorship system requires projects to meet 
these minimum quality standards:

✓ Security Score: 80+
✓ Ownership: Renounced
✓ No Honeypot
✓ LP: Locked
✓ Taxes: ≤10% buy/sell, ≤5% transfer

Your project failed: [SPECIFIC REASONS]

To qualify, please:
1. [Fix specific issue]
2. [Fix specific issue]
3. Resubmit when ready

We maintain high standards to protect users
and ensure featured status means something."
```

---

## 🚀 Status

✅ **Implemented**: Eligibility check in automated_sponsorship.py
✅ **Automatic**: Runs at payment time
✅ **Transparent**: Clear requirements listed
✅ **Enforceable**: No exceptions/manual overrides
✅ **User-Friendly**: Clear rejection messages

---

## Summary

**Projects must meet ALL of these to buy sponsorship:**

1. ✅ Security Score 80+
2. ✅ Ownership Renounced
3. ✅ No Honeypot
4. ✅ LP Locked
5. ✅ Reasonable Taxes

**This prevents scams from buying exposure while maintaining bot credibility!**
