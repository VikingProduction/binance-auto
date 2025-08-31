# src/main.py

import os
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime
from utils import setup_logger, load_config, validate_env, safe_api_call, track_rate_limit
from indicators import compute_indicators
from guards import build_filters, apply_price_filter, apply_lot_size, check_min_notional
from positions import normalize_positions
from persistence import get_entry, set_entry
from metrics import start_metrics_server, ORDER_COUNT, RATE_LIMITS, BANS

logger = setup_logger()

async def init_exchange(cfg_bot):
    exchange = getattr(ccxt, cfg_bot['exchange'])({
        'apiKey': os.getenv('API_KEY'),
        'secret': os.getenv('API_SECRET'),
        'enableRateLimit': True
    })
    # Hooker les réponses pour traquer les rate limits et bans
    exchange.session.hooks['response'] = [track_rate_limit]
    markets = await safe_api_call(exchange.fetch_markets)
    filters = build_filters(markets)
    return exchange, filters

async def get_tradable_symbols(exchange, cfg_bot):
    markets = await safe_api_call(exchange.fetch_markets)
    syms = []
    for m in markets:
        base, quote = m['base'], m['quote']
        vol = float(m['info'].get('quoteVolume', 0))
        if (base in cfg_bot['filter_bases'] or quote in cfg_bot['filter_bases']) and vol > cfg_bot['volume_threshold']:
            syms.append(m['symbol'])
    return syms

async def fetch_ohlcv(exchange, symbol, cfg_bot):
    try:
        data = await safe_api_call(exchange.fetch_ohlcv, symbol, cfg_bot['timeframe'], cfg_bot['limit'])
        df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"fetch_ohlcv {symbol} failed: {e}")
        return None

async def decide_and_execute(exchange, filters, df, symbol, cfg_bot, cfg_strat):
    latest = df.iloc[-1]
    bal = await safe_api_call(exchange.fetch_free_balance)
    usdt_bal = bal.get('USDT', 0)
    info = filters[symbol]

    # Achat
    if latest['RSI'] < cfg_strat['rsi_buy'] and latest['SMA_short'] > latest['SMA_long']:
        price = apply_price_filter(info, latest['close'])
        qty_raw = usdt_bal * cfg_bot['position_size_pct'] / price
        qty = apply_lot_size(info, qty_raw)
        if not check_min_notional(info, price, qty):
            logger.warning(f"{symbol} minNotional non atteint: price×qty={price*qty}")
            return None
        await safe_api_call(exchange.create_order, symbol, 'MARKET', 'buy', qty, price)
        set_entry(symbol, price)
        ORDER_COUNT.labels(action='buy').inc()
        return {'time': datetime.utcnow(), 'action':'BUY', 'symbol': symbol, 'price': price, 'qty': qty}

    # Vente / TP / SL
    raw_pos = await safe_api_call(exchange.fetch_positions) if hasattr(exchange, 'fetch_positions') else {}
    positions = normalize_positions(raw_pos)
    p = positions.get(symbol, {})
    size, entry_api = p.get('size', 0), p.get('entryPrice')
    entry = get_entry(symbol) or entry_api
    if size > 0 and entry:
        change = (latest['close'] - entry) / entry
        # Take-profit
        if change >= cfg_strat['take_profit_pct']:
            price = apply_price_filter(info, latest['close'])
            qty = apply_lot_size(info, size)
            await safe_api_call(exchange.create_order, symbol, 'MARKET', 'sell', qty, price)
            ORDER_COUNT.labels(action='sell').inc()
            return {'time': datetime.utcnow(), 'action':'TP', 'symbol': symbol, 'price': price}
        # Trailing-stop
        if change <= -cfg_strat['trailing_stop_pct']:
            price = apply_price_filter(info, latest['close'])
            qty = apply_lot_size(info, size)
            await safe_api_call(exchange.create_order, symbol, 'MARKET', 'sell', qty, price)
            ORDER_COUNT.labels(action='sell').inc()
            return {'time': datetime.utcnow(), 'action':'SL', 'symbol': symbol, 'price': price}

    return None

async def process_symbol(exchange, filters, symbol, cfg_bot, cfg_strat):
    df = await fetch_ohlcv(exchange, symbol, cfg_bot)
    if df is None:
        return None
    df = compute_indicators(df, cfg_strat)
    return await decide_and_execute(exchange, filters, df, symbol, cfg_bot, cfg_strat)

async def main():
    # Validation de l'environnement et démarrage des métriques
    validate_env()
    start_metrics_server(port=8000)

    cfg = load_config()
    cfg_bot, cfg_strat = cfg['bot'], cfg['strategy']

    exchange, filters = await init_exchange(cfg_bot)
    symbols = await get_tradable_symbols(exchange, cfg_bot)

    tasks = [
        process_symbol(exchange, filters, sym, cfg_bot, cfg_strat)
        for sym in symbols
    ]
    results = await asyncio.gather(*tasks)
    journal = [r for r in results if r]

    # Exposer le rapport pour GitHub Actions
    print("::set-output name=report::" + str(journal))

    await exchange.close()

if __name__ == '__main__':
    asyncio.run(main())
