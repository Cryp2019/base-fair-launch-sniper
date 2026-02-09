"""
Top-Tier Base Chain Token Scanner Design
Professional alert format for group posting
Based on SoulSniper template but optimized for Base chain
"""

def format_premium_token_alert(token_data: dict, analysis: dict, metrics: dict) -> str:
    """
    Format a premium token alert with professional design
    
    Args:
        token_data: Token name, symbol, address
        analysis: Security analysis results
        metrics: Token metrics (MC, liquidity, volume, etc)
    
    Returns:
        Formatted message for group posting
    """
    
    token_name = token_data.get('name', 'Unknown')
    token_symbol = token_data.get('symbol', 'N/A')
    contract = token_data.get('contract', '')
    dex = token_data.get('dex', 'Uniswap')
    
    security_score = analysis.get('security_score', 0)
    risk_level = analysis.get('risk_level', 'UNKNOWN')
    
    mc = metrics.get('market_cap', 0)
    liquidity = metrics.get('liquidity_usd', 0)
    volume_24h = metrics.get('volume_24h', 0)
    volume_1h = metrics.get('volume_1h', 0)
    
    # Risk color emojis
    if security_score >= 85:
        risk_emoji = "🟢"  # Green - Safe
        risk_text = "SAFE"
    elif security_score >= 70:
        risk_emoji = "🟡"  # Yellow - Medium
        risk_text = "MEDIUM"
    else:
        risk_emoji = "🔴"  # Red - Risky
        risk_text = "RISKY"
    
    # Format numbers
    def format_usd(value):
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:.0f}"
    
    message = f"""
🚀 <b>NEW FAIR LAUNCH ON BASE</b> {risk_emoji}

<b>💊 {token_name.upper()}</b> | <code>{token_symbol}</code>
┣ <b>Contract:</b> <code>{contract[:20]}...</code>
┗ <b>DEX:</b> {dex}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>METRICS</b>

💰 <b>Market Cap:</b> {format_usd(mc)}
💧 <b>Liquidity:</b> {format_usd(liquidity)}
📈 <b>Volume 24h:</b> {format_usd(volume_24h)}
📊 <b>Volume 1h:</b> {format_usd(volume_1h)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ <b>SECURITY ANALYSIS</b>

<b>Score:</b> {security_score}/100 {risk_emoji}
<b>Risk Level:</b> <b>{risk_text}</b>

✓ Ownership: {analysis.get('ownership_status', 'N/A')}
✓ Honeypot: {analysis.get('honeypot_status', 'N/A')}
✓ LP Lock: {analysis.get('lp_lock_status', 'N/A')}
✓ Tax: {analysis.get('tax_status', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ <b>QUICK LINKS</b>

<a href="https://dexscreener.com/base/{contract}">📊 DexScreener</a> | 
<a href="https://basescan.io/token/{contract}">🔍 BaseScan</a> | 
<a href="https://geckoterminal.com/base/pools/{contract}">📈 GeckoTerminal</a>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>⚠️ DISCLAIMER</b>
Not financial advice. DYOR. Most tokens fail.
Only trade with money you can afford to lose.

💳 <b>[BUY NOW]</b> | 💬 <b>Chat</b> | 📱 <b>Info</b>
"""
    
    return message


def format_ultra_premium_alert(token_data: dict, analysis: dict, metrics: dict, holders_data: dict = None) -> str:
    """
    Ultra premium format with holder analysis and dev info
    (Advanced version with more details)
    """
    
    token_name = token_data.get('name', 'Unknown')
    token_symbol = token_data.get('symbol', 'N/A')
    contract = token_data.get('contract', '')
    
    security_score = analysis.get('security_score', 0)
    
    # Risk indicators
    if security_score >= 85:
        risk_emoji = "🟢"
        rating_bar = "████████░ 85+"
    elif security_score >= 70:
        risk_emoji = "🟡"
        rating_bar = "██████░░░ 70-84"
    else:
        risk_emoji = "🔴"
        rating_bar = "████░░░░░ <70"
    
    # Format numbers
    def format_usd(value):
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:.0f}"
    
    def fmt_num(value):
        if value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{int(value)}"
    
    mc = metrics.get('market_cap', 0)
    liquidity = metrics.get('liquidity_usd', 0)
    volume_24h = metrics.get('volume_24h', 0)
    
    holders = holders_data.get('total', 0) if holders_data else 0
    top_holder_pct = holders_data.get('top_holder_pct', 0) if holders_data else 0
    
    message = f"""
<b>💊 {token_symbol}</b> <code>{token_name}</code>
{risk_emoji} Security: {rating_bar}

┏━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 💰 MC: <b>{format_usd(mc)}</b>
┃ 💧 LIQ: <b>{format_usd(liquidity)}</b>
┃ 📊 VOL: <b>{format_usd(volume_24h)}</b>
┗━━━━━━━━━━━━━━━━━━━━━━━━━┛

🔗 <a href="https://basescan.io/token/{contract}">BaseScan</a> | 
📈 <a href="https://dexscreener.com/base/{contract}">DexScreener</a> | 
📊 <a href="https://geckoterminal.com/base/pools/{contract}">Terminal</a>

👥 Holders: {fmt_num(holders)} | Top: {top_holder_pct:.1f}%

🛡️ Safety:
├─ Owner: {'✅ Renounced' if analysis.get('owner_renounced') else '⚠️ Active'}
├─ Honeypot: {'✅ Clear' if analysis.get('no_honeypot') else '⚠️ Risk'}
├─ Locks: {'✅ Locked' if analysis.get('lp_locked') else '⚠️ Unlocked'}
└─ Tax: {analysis.get('tax', 'N/A')}

<b>[🚀 BUY]</b> <b>[📊 CHART]</b> <b>[ℹ️ INFO]</b>
"""
    
    return message


def format_minimal_alert(token_data: dict, analysis: dict, metrics: dict) -> str:
    """
    Minimal but professional format for quick scanning
    """
    
    token_symbol = token_data.get('symbol', 'N/A')
    token_name = token_data.get('name', 'Unknown')
    contract = token_data.get('contract', '')
    
    score = analysis.get('security_score', 0)
    emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
    
    mc = metrics.get('market_cap', 0)
    liq = metrics.get('liquidity_usd', 0)
    
    def fmt(val):
        if val >= 1_000_000:
            return f"${val/1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val/1_000:.1f}K"
        return f"${val:.0f}"
    
    return f"""
{emoji} <b>{token_symbol}</b> | {token_name}
MC: {fmt(mc)} | LIQ: {fmt(liq)} | Score: {score}/100

<a href="https://basescan.io/token/{contract}">📍 BaseScan</a> | 
<a href="https://dexscreener.com/base/{contract}">📊 Dex</a>

<b>[💳 BUY]</b> <b>[📈 CHART]</b> <b>[ℹ️ INFO]</b>
"""


# Example usage
if __name__ == "__main__":
    sample_token = {
        'name': 'Base Coin',
        'symbol': 'BASE',
        'contract': '0x4158734D47Fc31Ab7b2B941f08f83469DA6d99315',
        'dex': 'Uniswap V3'
    }
    
    sample_analysis = {
        'security_score': 82,
        'risk_level': 'SAFE',
        'ownership_status': '✅ Renounced',
        'honeypot_status': '✅ Clear',
        'lp_lock_status': '✅ Locked 6 months',
        'tax_status': '0% Buy/Sell',
        'owner_renounced': True,
        'no_honeypot': True,
        'lp_locked': True,
        'tax': '0%'
    }
    
    sample_metrics = {
        'market_cap': 256000,
        'liquidity_usd': 72200,
        'volume_24h': 64300,
        'volume_1h': 8500
    }
    
    sample_holders = {
        'total': 7042,
        'top_holder_pct': 16.6
    }
    
    print("=== STANDARD ALERT ===")
    print(format_premium_token_alert(sample_token, sample_analysis, sample_metrics))
    
    print("\n=== ULTRA PREMIUM ALERT ===")
    print(format_ultra_premium_alert(sample_token, sample_analysis, sample_metrics, sample_holders))
    
    print("\n=== MINIMAL ALERT ===")
    print(format_minimal_alert(sample_token, sample_analysis, sample_metrics))
