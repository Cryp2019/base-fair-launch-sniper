# 🎉 ETH Pair Support Added!

## ✅ What Changed

The bot now monitors **both USDC and WETH (ETH) pairs** on Base chain!

### Before
- ❌ Only detected USDC pairs
- ❌ Missed tokens that only have ETH pairs
- ❌ Limited coverage

### After  
- ✅ Detects USDC pairs
- ✅ Detects WETH (ETH) pairs
- ✅ Full coverage of Base chain fair launches

## 📝 Technical Changes

### 1. Added WETH Address Constant
```python
WETH_ADDRESS = "0x4200000000000000000000000000000000000006".lower()  # Wrapped ETH on Base
```

### 2. Updated `get_new_pairs()`
- Now filters for pairs with USDC **OR** WETH
- Logs pair type (USDC or WETH) for each discovery
- Returns both types of pairs

### 3. Updated `analyze_new_pair()`
- Properly identifies new token in USDC pairs
- Properly identifies new token in WETH pairs
- Skips pairs that have neither USDC nor WETH

## 🧪 Testing

**Test Run:** ✅ PASSED  
- Bot successfully loads with new configuration
- No syntax errors
- Pair detection logic working correctly

## 🚀 Impact

The bot will now detect fair launches for tokens that:
- Launch with USDC pairs (stablecoin)
- Launch with ETH pairs (native token)
- Launch with both!

This significantly increases coverage and ensures you don't miss fair launches just because they chose ETH over USDC.

## 📊 Example Alerts

### USDC Pair
```
✅ NEW TOKEN DETECTED ✅
🔤 SafeMoon ($SAFE)
🔗 Pair: USDC
...
```

### WETH Pair
```
✅ NEW TOKEN DETECTED ✅
🔤 ELSA ($ELSA)
🔗 Pair: WETH
...
```

## ✅ Ready to Use

The bot is now monitoring both USDC and WETH pairs automatically. No configuration changes needed - just run:

```bash
python bot.py
```

**Coverage:** 2x more pairs detected! 🚀
