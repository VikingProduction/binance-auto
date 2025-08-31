import os
import ccxt
import pandas as pd
from datetime import datetime
from indicators import compute_indicators
from reporter import send_report

# Configuration CCXT
API_KEY    = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

def get_tradable_symbols():
    markets = exchange.load_markets()                # Charge tous les marchés
    symbols = []
    for sym, m in markets.items():
        base, quote = sym.split('/')
        # Garder toutes les paires où base ou quote est dans la liste cible
        if base in ('BTC','ETH','USDT','EUR') or quote in ('BTC','ETH','USDT','EUR'):
            symbols.append(sym)
    return symbols

def fetch_ohlcv(symbol, timeframe='1h', limit=100):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def decide_and_execute(df, symbol):
    latest = df.iloc[-1]
    balance = exchange.fetch_free_balance().get('USDT', 0)
    if latest['RSI'] < 30 and latest['SMA_short'] > latest['SMA_long']:
        amount = balance * 0.1 / latest['close']
        exchange.create_market_buy_order(symbol, amount)
        return f"BUY {symbol} @ {latest['close']:.2f}"
    if latest['RSI'] > 70 and latest['SMA_short'] < latest['SMA_long']:
        positions = exchange.fetch_positions()
        pos_size = positions.get(symbol, {}).get('size', 0)
        if pos_size > 0:
            exchange.create_market_sell_order(symbol, pos_size)
            return f"SELL {symbol} @ {latest['close']:.2f}"
    return None

def main():
    journal = []
    symbols = get_tradable_symbols()
    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol)
            df = compute_indicators(df)
            action = decide_and_execute(df, symbol)
            if action:
                journal.append(f"{datetime.utcnow()} - {action}")
        except Exception as e:
            # Ignorer les symboles non tradables ou erreurs ponctuelles
            continue
    send_report(journal)

if __name__ == '__main__':
    main()
