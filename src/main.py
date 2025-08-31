import os
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime
from indicators import compute_indicators
from utils import setup_logger, load_config, validate_env, safe_api_call

logger = setup_logger()

async def get_tradable_symbols(exchange, bot_cfg):
    markets = await safe_api_call(exchange.load_markets)
    syms = []
    for sym, data in markets.items():
        base, quote = sym.split('/')
        vol = float(data.get('info', {}).get('quoteVolume', 0))
        if (base in bot_cfg['filter_bases'] or quote in bot_cfg['filter_bases']) and vol > bot_cfg['volume_threshold']:
            syms.append(sym)
    return syms

async def fetch_ohlcv(exchange, symbol, bot_cfg):
    try:
        data = await safe_api_call(exchange.fetch_ohlcv, symbol, bot_cfg['timeframe'], bot_cfg['limit'])
        df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"fetch_ohlcv {symbol} failed: {e}")
        return None

async def decide_and_execute(exchange, df, cfg_bot, cfg_strat, positions):
    latest = df.iloc[-1]
    bal = await safe_api_call(exchange.fetch_free_balance)
    usdt_bal = bal.get('USDT', 0)
    # Achat
    if latest['RSI'] < cfg_strat['rsi_buy'] and latest['SMA_short'] > latest['SMA_long']:
        qty = usdt_bal * cfg_bot['position_size_pct'] / latest['close']
        order = await safe_api_call(exchange.create_market_buy_order, df.name, qty)
        return {'time': datetime.utcnow(), 'action':'BUY', 'symbol':df.name, 'price':latest['close'], 'qty':qty}
    # Vente / TP / SL
    pos = positions.get(df.name, {})
    size = pos.get('size', 0); entry = pos.get('entryPrice')
    if size > 0 and entry:
        change = (latest['close'] - entry) / entry
        if change >= cfg_strat['take_profit_pct'] or change <= -cfg_strat['trailing_stop_pct']:
            await safe_api_call(exchange.create_market_sell_order, df.name, size)
            act = 'TP' if change>=cfg_strat['take_profit_pct'] else 'SL'
            return {'time': datetime.utcnow(), 'action':act, 'symbol':df.name, 'price':latest['close']}
    return None

async def process_symbol(exchange, symbol, cfg_bot, cfg_strat):
    df = await fetch_ohlcv(exchange, symbol, cfg_bot)
    if df is None: return None
    df = compute_indicators(df, cfg_strat)
    df.name = symbol
    positions = await safe_api_call(exchange.fetch_positions)
    return await decide_and_execute(exchange, df, cfg_bot, cfg_strat, positions)

async def main():
    validate_env()
    cfg = load_config()
    cfg_bot = cfg['bot']; cfg_strat = cfg['strategy']
    exchange = getattr(ccxt, cfg_bot['exchange'])({
        'apiKey': os.getenv('API_KEY'),
        'secret': os.getenv('API_SECRET'),
        'enableRateLimit': True
    })
    symbols = await get_tradable_symbols(exchange, cfg_bot)
    tasks = [process_symbol(exchange, sym, cfg_bot, cfg_strat) for sym in symbols]
    results = await asyncio.gather(*tasks)
    journal = [r for r in results if r]
    # Exposer le rapport pour GitHub Action
    print("::set-output name=report::" + str(journal))
    await exchange.close()

if __name__ == '__main__':
    asyncio.run(main())
