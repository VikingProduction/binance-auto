# src/main.py
import os
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any

import yaml
import ccxt.async_support as ccxt

from .metrics import start_metrics_server, bot_daily_pnl, order_latency, bot_order_total
from .marketdata import run_bookticker, midprice
from .utils import get_symbol_info, with_rate_limit_retry
from .guards import prepare_order
from .persistence import load as load_state, state as get_state, roll_daily_if_needed

CONFIG_PATH = os.environ.get("BOT_CONFIG", "config.yml")

def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def create_exchange(cfg: Dict[str, Any]):
    ex_name = cfg["bot"].get("exchange", "binance")
    klass = getattr(ccxt, ex_name)
    exchange = klass({
        "apiKey": os.environ.get("API_KEY", ""),
        "secret": os.environ.get("API_SECRET", ""),
        "enableRateLimit": True,
    })
    # Testnet/dry-run
    if cfg["bot"].get("testnet") or os.environ.get("TESTNET") == "1":
        exchange.set_sandbox_mode(True)
    return exchange

async def risk_gate(exchange, cfg: Dict[str, Any]) -> bool:
    """Retourne True si on peut trader; False si kill-switch actif."""
    risk = cfg.get("risk", {})
    limit_pct = float(risk.get("daily_loss_limit_pct") or 0.0)
    if limit_pct <= 0:
        return True

    # Equity en quote principal (priorité USDT puis EUR)
    bal = await exchange.fetch_balance()
    quote_equity = bal["total"].get("USDT") or bal["total"].get("EUR") or 0.0

    st = get_state()
    pnl = float(st["daily"]["realized_pnl_quote"])
    bot_daily_pnl.set(pnl)

    if quote_equity and pnl / quote_equity <= -abs(limit_pct):
        return False
    return True

async def place_limit_order(exchange, symbol: str, side: str, price: float, qty: float):
    t0 = time.monotonic()
    try:
        order = await exchange.create_order(symbol, "limit", side, qty, price)
    finally:
        order_latency.observe(time.monotonic() - t0)
    bot_order_total.labels(action=side.lower()).inc()
    return order

async def trading_loop(exchange, cfg: Dict[str, Any]):
    symbols = cfg["bot"].get("symbols")  # optionnel: liste blanche
    metrics_port = int(cfg["bot"].get("metrics_port", 8000))
    start_metrics_server(metrics_port)

    # État
    load_state()

    # WebSocket prix
    asyncio.create_task(run_bookticker(symbols))

    # Exemple de boucle simple
    position_size_pct = float(cfg["bot"].get("position_size_pct", 0.02))

    while True:
        # reset jour et kill-switch
        roll_daily_if_needed(datetime.now(timezone.utc).date().isoformat())
        if not await risk_gate(exchange, cfg):
            await asyncio.sleep(30)
            continue

        # Sélection symboles à scanner (fallback: tous les marchés majeurs)
        if not symbols:
            markets = await exchange.load_markets()
            symbols = [s for s in markets.keys() if s.endswith("/USDT")][:50]

        for sym in symbols:
            try:
                s_info = await get_symbol_info(exchange, sym)
                lp = midprice(sym)  # None si pas encore arrivé
                if lp is None:
                    ticker = await exchange.fetch_ticker(sym)
                    lp = float(ticker.get("last") or ticker.get("close") or 0)
                if lp <= 0:
                    continue

                # Exemple: buy sur micro-ordre pour la démo (à personnaliser par ta stratégie)
                balance = await exchange.fetch_balance()
                quote = "USDT" if sym.endswith("USDT") else sym.split("/")[1]
                free_quote = float(balance["free"].get(quote, 0))

                order_notional_target = free_quote * position_size_pct
                if order_notional_target <= 0:
                    continue

                desired_qty = order_notional_target / lp
                desired_price = lp  # limit au mid pour l'exemple

                price, qty = prepare_order(s_info, "BUY", lp, desired_price, desired_qty)

                # dry-run
                dry = cfg["bot"].get("dry_run") or os.environ.get("DRY_RUN") == "1"
                if dry:
                    continue

                await place_limit_order(exchange, sym, "buy", price, qty)

            except Exception:
                # volontairement sobre; à compléter avec logs/alerte
                pass

        await asyncio.sleep(2)

async def main():
    cfg = load_config()
    exchange = await create_exchange(cfg)
    try:
        await trading_loop(exchange, cfg)
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())
