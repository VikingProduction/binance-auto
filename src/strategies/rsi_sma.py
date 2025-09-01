class RSISMAStrategy(BaseStrategy):
    async def generate_signal(self, df, symbol_info):
        latest = df.iloc[-1]
        if latest['RSI'] < self.config['rsi_buy'] and latest['SMA_short'] > latest['SMA_long']:
            return {'action': 'BUY', 'confidence': 0.7}
        return {'action': 'HOLD', 'confidence': 0.5}
