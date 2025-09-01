import numpy as np
from sklearn.ensemble import RandomForestClassifier

class MLSignalGenerator:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.is_trained = False
    
    def prepare_features(self, df):
        features = []
        # RSI
        features.append(df['RSI'].iloc[-1])
        # SMA ratio
        features.append(df['SMA_short'].iloc[-1] / df['SMA_long'].iloc[-1])
        # Volume trend
        features.append(df['volume'].rolling(5).mean().iloc[-1])
        return np.array(features).reshape(1, -1)
    
    async def get_signal(self, df):
        if not self.is_trained:
            return {'action': 'HOLD', 'confidence': 0.0}
        
        features = self.prepare_features(df)
        prediction = self.model.predict_proba(features)[0]
        
        if prediction[1] > 0.7:  # Buy probability > 70%
            return {'action': 'BUY', 'confidence': prediction[1]}
        elif prediction[0] > 0.7:  # Sell probability > 70%
            return {'action': 'SELL', 'confidence': prediction[0]}
        
        return {'action': 'HOLD', 'confidence': max(prediction)}
