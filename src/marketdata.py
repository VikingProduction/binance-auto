# src/marketdata.py
import asyncio, json, websockets
from collections import defaultdict

_BOOK = defaultdict(lambda: {"bid": None, "ask": None})

async def run_bookticker(symbols: list[str] | None = None):
    url = "wss://stream.binance.com:9443/stream?streams=" + "/".join([f"{s.lower()}@bookTicker" for s in symbols]) \
          if symbols else "wss://stream.binance.com:9443/ws/!bookTicker"
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=60) as ws:
                async for msg in ws:
                    data = json.loads(msg)
                    payload = data.get("data", data)
                    s = payload["s"]
                    _BOOK[s] = {"bid": float(payload["b"]), "ask": float(payload["a"])}
        except Exception:
            await asyncio.sleep(3)

def midprice(symbol: str) -> float | None:
    b = _BOOK[symbol]["bid"]; a = _BOOK[symbol]["ask"]
    return (b + a) / 2 if b and a else None
