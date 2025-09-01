# src/marketdata.py
import asyncio
import json
from typing import Dict, Optional, List
import websockets

# Cache des derniers prix (bid/ask) par symbole, ex: "BTCUSDT"
_BOOK: Dict[str, Dict[str, float]] = {}

def midprice(symbol: str) -> Optional[float]:
    sym = symbol.replace("/", "").upper()
    b = _BOOK.get(sym, {}).get("b")
    a = _BOOK.get(sym, {}).get("a")
    if b is None or a is None:
        return None
    return (b + a) / 2.0

async def run_bookticker(symbols: Optional[List[str]] = None):
    # Streams multiplexés si une liste est fournie, sinon !bookTicker global
    if symbols:
        streams = "/".join([f"{s.replace('/','').lower()}@bookTicker" for s in symbols])
        url = f"wss://stream.binance.com:9443/stream?streams={streams}"
    else:
        url = "wss://stream.binance.com:9443/ws/!bookTicker"

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=60) as ws:
                async for raw in ws:
                    msg = json.loads(raw)
                    data = msg.get("data", msg)
                    # payload keys: s (symbol), b (best bid price), B (bid qty), a (best ask price), A (ask qty)
                    s = data.get("s")
                    if not s:
                        continue
                    try:
                        bid = float(data.get("b"))
                        ask = float(data.get("a"))
                    except Exception:
                        continue
                    _BOOK[s] = {"b": bid, "a": ask}
        except Exception:
            await asyncio.sleep(3)  # reconnexion douce
