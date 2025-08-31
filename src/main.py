import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime
from indicators import compute_indicators
from reporter import send_report
from utils import setup_logger, load_config

logger = setup_logger()

async def get_tradable_symbols(exchange, config):
    markets = await exchange.load_markets()
    syms = []
    for sym, data in markets.items():
        base, quote = sym.split('/')
        vol = float(data.get('info', {}).get('quoteVolume', 0))
        if (base in config['filter_bases'] or quote in config['filter_bases']) and vol > config['volume_threshold']:
            syms.append(sym)
    return syms

async def fetch_ohlcv(exchange, symbol, config):
    try:
        data = await exchange.fetch_ohlcv(symbol, timeframe=config['timeframe'], limit=config['limit'])
        df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"fetch_ohlcv {symbol} failed: {e}")
        return None

async def decide_and_execute(exchange, df, symbol, config):
    latest = df.iloc[-1]
    bal = await exchange.fetch_free_balance()
    usdt_bal = bal.get('USDT', 0)
    # Achat
    if latest['RSI'] < config['indicators']['rsi_buy'] and latest['SMA_short'] > latest['SMA_long']:
        qty = usdt_bal * config['position_size_pct'] / latest['close']
        order = await exchange.create_market_buy_order(symbol, qty)
        entry = latest['close']
        return {'time': datetime.utcnow(), 'action':'BUY', 'symbol':symbol, 'price':entry, 'qty':qty}
    # Vente / TP / SL
    pos = (await exchange.fetch_positions()).get(symbol, {})
    size = pos.get('size', 0)
    entry = pos.get('entryPrice')
    if size > 0 and entry:
        change = (latest['close'] - entry) / entry
        if change >= config['take_profit_pct']:
            await exchange.create_market_sell_order(symbol, size)
            return {'time': datetime.utcnow(), 'action':'TP', 'symbol':symbol, 'price':latest['close']}
        if change <= -config['trailing_stop_pct']:
            await exchange.create_market_sell_order(symbol, size)
            return {'time': datetime.utcnow(), 'action':'SL', 'symbol':symbol, 'price':latest['close']}
    return None

async def process_symbol(exchange, symbol, config):
    df = await fetch_ohlcv(exchange, symbol, config)
    if df is None: return None
    df = compute_indicators(df, config)
    return await decide_and_execute(exchange, df, symbol, config)

async def main():
    config = load_config()
    exchange = getattr(ccxt, config['exchange'])({
        'apiKey': os.getenv('API_KEY'),
        'secret': os.getenv('API_SECRET'),
        'enableRateLimit': True
    })
    symbols = await get_tradable_symbols(exchange, config)
    tasks = [process_symbol(exchange, sym, config) for sym in symbols]
    results = await asyncio.gather(*tasks)
    journal = [r for r in results if r]
    await send_report(journal, config)
    await exchange.close()

if __name__ == '__main__':
    asyncio.run(main())
