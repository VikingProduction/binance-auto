# src/main.py
import os
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

import yaml
import pandas as pd
import ccxt.async_support as ccxt

# Imports locaux ABSOLUS
from metrics import start_metrics_server, bot_daily_pnl, order_latency, bot_order_total
from marketdata import run_bookticker, midprice
from utils import get_symbol_info, with_rate_limit_retry
from guards import prepare_order
from persistence import load as load_state, state as get_state, roll_daily_if_needed, update_realized_pnl
from positions import get_position, set_position, clear_position
from indicators import compute_indicators
from cache import OHLCVCache
from strategies.rsi_sma import RSISMAStrategy

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get("BOT_CONFIG", "config.yml")

def load_config() -> Dict[str, Any]:
    """Charge la configuration depuis config.yml"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def create_exchange(cfg: Dict[str, Any]):
    """Initialise l'exchange avec gestion testnet"""
    ex_name = cfg["bot"].get("exchange", "binance")
    klass = getattr(ccxt, ex_name)
    exchange = klass({
        "apiKey": os.environ.get("API_KEY", ""),
        "secret": os.environ.get("API_SECRET", ""),
        "enableRateLimit": True,
    })
    if cfg["bot"].get("testnet") or os.environ.get("TESTNET") == "1":
        exchange.set_sandbox_mode(True)
        logger.info("Mode testnet activé")
    return exchange

async def risk_gate(exchange, cfg: Dict[str, Any]) -> bool:
    """Kill-switch basé sur la perte journalière. Retourne True si trading autorisé"""
    risk = cfg.get("risk", {})
    limit_pct = float(risk.get("daily_loss_limit_pct") or 0.0)
    if limit_pct <= 0:
        return True
    try:
        bal = await exchange.fetch_balance()
        quote_equity = bal["total"].get("USDT") or bal["total"].get("EUR") or 0.0
        st = get_state()
        pnl = float(st["daily"]["realized_pnl_quote"])
        bot_daily_pnl.set(pnl)
        if quote_equity and pnl / quote_equity <= -abs(limit_pct):
            logger.critical(f"Kill-switch activé: PnL journalier {pnl/quote_equity:.2%} > limite {limit_pct:.2%}")
            return False
    except Exception as e:
        logger.error(f"Erreur risk_gate: {e}")
        return False
    return True

async def fetch_ohlcv_cached(exchange, symbol: str, timeframe: str, limit: int, cache: OHLCVCache) -> pd.DataFrame:
    """Récupère OHLCV avec cache"""
    cached = cache.get(symbol, timeframe)
    if cached is not None:
        return cached
    try:
        data = await with_rate_limit_retry(exchange.fetch_ohlcv, symbol, timeframe, limit)
        df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        cache.set(symbol, timeframe, df)
        return df
    except Exception as e:
        logger.error(f"Erreur fetch OHLCV {symbol}: {e}")
        return None

async def analyze_symbol(exchange, symbol: str, cfg: Dict[str, Any], cache: OHLCVCache, strategy) -> Dict[str, Any]:
    """Analyse un symbole et génère un signal de trading"""
    try:
        df = await fetch_ohlcv_cached(exchange, symbol, cfg["bot"]["timeframe"], cfg["bot"]["limit"], cache)
        if df is None or len(df) < 50:
            return None
        df = compute_indicators(df, cfg["strategy"])
        if df['RSI'].isna().any() or df['SMA_short'].isna().any():
            return None
        signal = await strategy.generate_signal(df, None)
        if signal['action'] == 'HOLD':
            return None
        latest = df.iloc[-1]
        current_price = midprice(symbol) or latest['close']
        return {
            'symbol': symbol,
            'signal': signal,
            'price': current_price,
            'rsi': latest['RSI'],
            'sma_short': latest['SMA_short'],
            'sma_long': latest['SMA_long'],
            'volume': latest['volume']
        }
    except Exception as e:
        logger.error(f"Erreur analyse {symbol}: {e}")
        return None

async def execute_trade(exchange, analysis: Dict[str, Any], cfg: Dict[str, Any]) -> bool:
    """Exécute un trade basé sur l'analyse"""
    symbol = analysis['symbol']
    signal = analysis['signal']
    price = analysis['price']
    try:
        existing_pos = get_position(symbol)
        if existing_pos and signal['action'] == 'BUY':
            logger.info(f"Position déjà ouverte sur {symbol}, skip BUY")
            return False
        balance = await exchange.fetch_balance()
        quote = symbol.split('/')[1] if '/' in symbol else 'USDT'
        free_quote = float(balance["free"].get(quote, 0))
        position_size_pct = float(cfg["bot"].get("position_size_pct", 0.02))
        notional_target = free_quote * position_size_pct
        if notional_target < 10:
            return False
        qty = notional_target / price
        symbol_info = await get_symbol_info(exchange, symbol)
        final_price, final_qty = prepare_order(symbol_info, signal['action'], price, price, qty)
        if cfg["bot"].get("dry_run") or os.environ.get("DRY_RUN") == "1":
            logger.info(f"DRY RUN: {signal['action']} {final_qty} {symbol} @ {final_price}")
            return True
        t0 = time.monotonic()
        order = await exchange.create_order(symbol, 'market', signal['action'].lower(), final_qty, final_price)
        order_latency.observe(time.monotonic() - t0)
        bot_order_total.labels(action=signal['action'].lower()).inc()
        if signal['action'] == 'BUY':
            set_position(symbol, final_qty, final_price)
            logger.info(f"Position ouverte: {final_qty} {symbol} @ {final_price}")
        else:
            clear_position(symbol)
            if existing_pos:
                pnl = (final_price - existing_pos['entry_price']) * existing_pos['qty']
                update_realized_pnl(pnl)
                logger.info(f"Position fermée: {symbol}, PnL: {pnl:.2f}")
        return True
    except Exception as e:
        logger.error(f"Erreur exécution trade {symbol}: {e}")
        return False

async def manage_existing_positions(exchange, cfg: Dict[str, Any], cache: OHLCVCache):
    """Gère les positions ouvertes (take-profit, stop-loss)"""
    st = get_state()
    positions = st.get("positions", {})
    for symbol, pos_data in list(positions.items()):
        try:
            current_price = midprice(symbol)
            if current_price is None:
                ticker = await exchange.fetch_ticker(symbol)
                current_price = float(ticker.get("last") or ticker.get("close"))
            entry_price = pos_data['entry_price']
            qty = pos_data['qty']
            pnl_pct = (current_price - entry_price) / entry_price
            tp_pct = cfg["strategy"].get("take_profit_pct", 0.05)
            if pnl_pct >= tp_pct:
                logger.info(f"Take profit {symbol}: {pnl_pct:.2%}")
                await execute_sell(exchange, symbol, qty, current_price, "TAKE_PROFIT")
            sl_pct = cfg["strategy"].get("trailing_stop_pct", 0.02)
            if pnl_pct <= -sl_pct:
                logger.info(f"Stop loss {symbol}: {pnl_pct:.2%}")
                await execute_sell(exchange, symbol, qty, current_price, "STOP_LOSS")
        except Exception as e:
            logger.error(f"Erreur gestion position {symbol}: {e}")

async def execute_sell(exchange, symbol: str, qty: float, price: float, reason: str):
    """Exécute une vente"""
    try:
        symbol_info = await get_symbol_info(exchange, symbol)
        final_price, final_qty = prepare_order(symbol_info, "SELL", price, price, qty)
        order = await exchange.create_order(symbol, 'market', 'sell', final_qty, final_price)
        bot_order_total.labels(action='sell').inc()
        pos = get_position(symbol)
        if pos:
            pnl = (final_price - pos['entry_price']) * final_qty
            update_realized_pnl(pnl)
        clear_position(symbol)
        logger.info(f"{reason}: Vendu {final_qty} {symbol} @ {final_price}")
    except Exception as e:
        logger.error(f"Erreur vente {symbol}: {e}")

async def get_tradable_symbols(exchange, cfg: Dict[str, Any]) -> List[str]:
    """Sélectionne les symboles tradables selon critères config"""
    symbols = cfg["bot"].get("symbols")
    if symbols:
        return symbols
    markets = await exchange.load_markets()
    tradable = []
    for symbol, market in markets.items():
        if not market.get('active', True):
            continue
        base, quote = market['base'], market['quote']
        if not any(b in [base, quote] for b in cfg["bot"].get("filter_bases", [])):
            continue
        volume_threshold = cfg["bot"].get("volume_threshold", 0)
        if volume_threshold > 0:
            try:
                ticker = await exchange.fetch_ticker(symbol)
                if float(ticker.get('quoteVolume', 0)) < volume_threshold:
                    continue
            except:
                continue
        tradable.append(symbol)
        if len(tradable) >= 50:
            break
    return tradable

async def trading_loop(exchange, cfg: Dict[str, Any]):
    """Boucle principale de trading"""
    start_metrics_server(int(cfg["bot"].get("metrics_port", 8000)))
    load_state()
    cache = OHLCVCache(ttl_seconds=cfg.get("performance", {}).get("cache_ttl", 300))
    strategy = RSISMAStrategy(cfg["strategy"])
    symbols = await get_tradable_symbols(exchange, cfg)
    if cfg.get("performance", {}).get("websocket_enabled", True):
        asyncio.create_task(run_bookticker(symbols[:20]))
    logger.info(f"Bot démarré - {len(symbols)} symboles surveillés")
    while True:
        try:
            roll_daily_if_needed(datetime.now(timezone.utc).date().isoformat())
            if not await risk_gate(exchange, cfg):
                logger.warning("Trading suspendu par kill-switch")
                await asyncio.sleep(60)
                continue
            await manage_existing_positions(exchange, cfg, cache)
            batch_size = cfg.get("performance", {}).get("batch_size", 10)
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i+batch_size]
                tasks = [analyze_symbol(exchange, sym, cfg, cache, strategy) for sym in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if result and not isinstance(result, Exception):
                        await execute_trade(exchange, result, cfg)
                        await asyncio.sleep(1)
                await asyncio.sleep(2)
            await asyncio.sleep(cfg["bot"].get("cycle_interval", 30))
        except Exception as e:
            logger.error(f"Erreur boucle principale: {e}")
            await asyncio.sleep(10)

async def main():
    try:
        cfg = load_config()
        exchange = await create_exchange(cfg)
        await trading_loop(exchange, cfg)
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")  
        raise
    finally:
        if 'exchange' in locals():
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())
