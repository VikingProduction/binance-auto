import os
import ccxt
import pandas as pd
from datetime import datetime
from indicators.py import compute_indicators
from reporter import send_report

# Configuration
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

def fetch_ohlcv(symbol, timeframe='1h', limit=100):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def decide_and_execute(df, symbol):
    latest = df.iloc[-1]
    balance = exchange.fetch_free_balance()['USDT']
    # Conditions d’achat
    if latest['RSI'] < 30 and latest['SMA_short'] > latest['SMA_long']:
        amount = balance * 0.1 / latest['close']
        exchange.create_market_buy_order(symbol, amount)
        return f"BUY {symbol} @ {latest['close']}"
    # Conditions de vente
    if latest['RSI'] > 70 and latest['SMA_short'] < latest['SMA_long']:
        pos = exchange.fetch_positions()[symbol]['size']
        if pos > 0:
            exchange.create_market_sell_order(symbol, pos)
            return f"SELL {symbol} @ {latest['close']}"
    return None

def main():
    journal = []
    for symbol in SYMBOLS:
        df = fetch_ohlcv(symbol)
        df = compute_indicators(df)
        action = decide_and_execute(df, symbol)
        if action:
            journal.append(f"{datetime.utcnow()} - {action}")
    send_report(journal)

if __name__ == '__main__':
    main()
