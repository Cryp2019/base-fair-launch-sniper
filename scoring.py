"""
Token Scoring Functions for Base Fair Launch Sniper
Calculates Social, Viral, Security, and Overall scores
"""

def calculate_token_scores(analysis: dict, metrics: dict) -> dict:
    """Calculate comprehensive scores for a token"""
    
    # Social Score (0-100) - based on liquidity and holder activity
    social_score = 0
    try:
        # Liquidity indicates community size
        if metrics['liquidity_usd'] > 50000:
            social_score += 30
        elif metrics['liquidity_usd'] > 10000:
            social_score += 20
        elif metrics['liquidity_usd'] > 1000:
            social_score += 10
        
        # Volume indicates active trading
        if metrics['volume_24h'] > 10000:
            social_score += 30
        elif metrics['volume_24h'] > 1000:
            social_score += 20
        elif metrics['volume_24h'] > 100:
            social_score += 10
        
        # Good liquidity/MC ratio = healthy community
        if metrics['market_cap'] > 0:
            liq_ratio = metrics['liquidity_usd'] / metrics['market_cap']
            if liq_ratio > 0.3:
                social_score += 20
            elif liq_ratio > 0.1:
                social_score += 10
        
        # Bonus for established tokens
        if metrics['volume_24h'] > 0 and metrics['liquidity_usd'] > 0:
            social_score += 20
    except:
        pass
    
    # Viral Score (0-100) - based on momentum and growth
    viral_score = 0
    try:
        # Price change indicates viral potential
        price_change = abs(metrics.get('price_change_24h', 0))
        if price_change > 100:
            viral_score += 40
        elif price_change > 50:
            viral_score += 30
        elif price_change > 20:
            viral_score += 20
        elif price_change > 10:
            viral_score += 10
        
        # High volume = viral activity
        if metrics['volume_24h'] > 50000:
            viral_score += 40
        elif metrics['volume_24h'] > 10000:
            viral_score += 30
        elif metrics['volume_24h'] > 1000:
            viral_score += 20
        elif metrics['volume_24h'] > 100:
            viral_score += 10
        
        # Small cap + high volume = viral potential
        if metrics['market_cap'] < 100000 and metrics['volume_24h'] > 1000:
            viral_score += 20
    except:
        pass
    
    # Security Score (0-100) - based on safety checks
    security_score = 0
    try:
        # Ownership renounced = safer
        if analysis.get('renounced'):
            security_score += 30
        
        # Not a honeypot = safe to trade
        if not analysis.get('is_honeypot'):
            security_score += 30
        
        # LP locked = can't rug
        if analysis.get('liquidity_locked'):
            security_score += 25
            
            # Bonus for long lock duration
            lock_days = analysis.get('lock_days', 0)
            if lock_days > 365:
                security_score += 15
            elif lock_days > 90:
                security_score += 10
            elif lock_days > 30:
                security_score += 5
        
        # Low taxes = not a scam
        buy_tax = analysis.get('buy_tax', 0)
        sell_tax = analysis.get('sell_tax', 0)
        if buy_tax < 5 and sell_tax < 5:
            security_score += 10
    except:
        pass
    
    # Overall Score - weighted average
    # Security is most important (40%), then Viral (35%), then Social (25%)
    overall_score = int(
        (social_score * 0.25) + 
        (viral_score * 0.35) + 
        (security_score * 0.40)
    )
    
    # Cap all scores at 100
    social_score = min(social_score, 100)
    viral_score = min(viral_score, 100)
    security_score = min(security_score, 100)
    overall_score = min(overall_score, 100)
    
    return {
        'social_score': social_score,
        'viral_score': viral_score,
        'security_score': security_score,
        'overall_score': overall_score
    }

def get_score_emoji(score: int) -> str:
    """Get color emoji based on score"""
    if score >= 75:
        return "🟢"  # Green - Excellent
    elif score >= 50:
        return "🟡"  # Yellow - Good
    elif score >= 25:
        return "🟠"  # Orange - Caution
    else:
        return "🔴"  # Red - Poor

def format_score(score: int) -> str:
    """Format score with emoji and value"""
    emoji = get_score_emoji(score)
    return f"{emoji} {score}/100"
