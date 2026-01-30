"""
AI-Powered Honeypot Prediction
Only implement after collecting 5,000+ verified rug samples
"""
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os

class AIRugPredictor:
    def __init__(self, model_path="rug_model.pkl"):
        try:
            self.model = joblib.load(model_path)
            self.is_trained = True
        except FileNotFoundError:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.is_trained = False
    
    def extract_features(self, token_data: dict) -> np.ndarray:
        """Convert token contract data into ML features"""
        features = [
            token_data.get('pre_mine_percent', 0) / 100,  # Normalize to 0-1
            1 if token_data.get('ownership_renounced', False) else 0,
            token_data.get('buy_tax', 0) / 25,  # Normalize (max 25% tax)
            token_data.get('sell_tax', 0) / 25,
            1 if token_data.get('liquidity_locked', False) else 0,
            token_data.get('holder_count', 0) / 1000,  # Normalize
            token_data.get('age_hours', 0) / 24,  # Normalize to days
            token_data.get('top10_concentration', 0) / 100,
            token_data.get('contract_verified', 0),  # 1 if verified on Basescan
            token_data.get('social_links_count', 0) / 5,  # Normalize
        ]
        return np.array(features).reshape(1, -1)
    
    def predict_rug_risk(self, token_data: dict) -> dict:
        """Return risk score 0-100 + confidence"""
        if not self.is_trained:
            return {
                "risk_score": 50, 
                "confidence": 0.3, 
                "reason": "model_not_trained",
                "recommendation": "USE_BASIC_CHECKS"
            }
        
        features = self.extract_features(token_data)
        proba = self.model.predict_proba(features)[0]
        
        # Class 1 = rug, Class 0 = legit
        risk_score = int(proba[1] * 100)
        confidence = max(proba)
        
        reasons = []
        if token_data.get('pre_mine_percent', 0) > 30:
            reasons.append("high_pre_mine")
        if not token_data.get('ownership_renounced', False):
            reasons.append("ownership_not_renounced")
        if token_data.get('sell_tax', 0) > 10:
            reasons.append("high_sell_tax")
        if not token_data.get('liquidity_locked', False):
            reasons.append("unlocked_liquidity")
        if token_data.get('top10_concentration', 0) > 80:
            reasons.append("whale_concentration")
        
        return {
            "risk_score": risk_score,
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "recommendation": "AVOID" if risk_score > 75 else "CAUTION" if risk_score > 50 else "MONITOR"
        }
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train on labeled rug/legit samples"""
        self.model.fit(X_train, y_train)
        self.is_trained = True
        joblib.dump(self.model, "rug_model.pkl")
        accuracy = self.model.score(X_train, y_train)
        print(f"✅ Model trained on {len(y_train)} samples. Accuracy: {accuracy:.2%}")
        return accuracy
    
    def add_training_sample(self, token_data: dict, is_rug: bool):
        """Incrementally add samples for future training"""
        # Save to training dataset
        sample = {
            'features': self.extract_features(token_data).tolist(),
            'label': 1 if is_rug else 0,
            'token_address': token_data.get('address'),
            'timestamp': token_data.get('timestamp')
        }
        
        # Append to training data file
        import json
        training_file = "training_data.json"
        try:
            with open(training_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        
        data.append(sample)
        
        with open(training_file, 'w') as f:
            json.dump(data, f, indent=2)

# Usage in bot.py after basic checks:
# predictor = AIRugPredictor()
# if predictor.is_trained:
#     risk = predictor.predict_rug_risk(token_data)
#     if risk['risk_score'] > 75:
#         alert += f"\n🤖 AI Risk Score: {risk['risk_score']}/100 (Confidence: {risk['confidence']})"
#         alert += f"\n⚠️ Recommendation: {risk['recommendation']}"
