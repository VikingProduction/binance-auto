# src/strategies/rsi_sma.py
import pandas as pd
from strategies.base import BaseStrategy

class RSISMAStrategy(BaseStrategy):
    """Stratégie basée sur RSI et croisement SMA"""

    def get_required_indicators(self):
        return ['RSI', 'SMA_short', 'SMA_long']

    async def generate_signal(self, df, symbol_info):
        """Génère un signal de trading basé sur RSI < 30 et SMA_short > SMA_long"""
        if df is None or len(df) == 0:
            return {'action': 'HOLD', 'confidence': 0.0}

        latest = df.iloc[-1]
        if any(pd.isna(latest[ind]) for ind in self.get_required_indicators()):
            return {'action': 'HOLD', 'confidence': 0.0}

        rsi = latest['RSI']
        sma_short = latest['SMA_short']
        sma_long = latest['SMA_long']

        if rsi < self.config['rsi_buy'] and sma_short > sma_long:
            confidence = min(0.9,
                (self.config['rsi_buy'] - rsi) / self.config['rsi_buy'] * 0.5 + 0.4
            )
            return {'action': 'BUY', 'confidence': confidence}

        elif rsi > self.config['rsi_sell'] and sma_short < sma_long:
            confidence = min(0.9,
                (rsi - self.config['rsi_sell']) / (100 - self.config['rsi_sell']) * 0.5 + 0.4
            )
            return {'action': 'SELL', 'confidence': confidence}

        return {'action': 'HOLD', 'confidence': 0.5}

    def validate_signal(self, signal, symbol_info=None):
        """Validation du signal (peut être étendue)"""
        return signal['confidence'] >= 0.3
