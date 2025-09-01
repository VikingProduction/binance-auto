# src/utils.py
import asyncio
import time
from typing import Dict, Any, Callable, Awaitable, Optional

from ccxt.base.errors import ExchangeError

_EXINFO_CACHE: Dict[str, Any] = {}
_EXINFO_TS = 0.0
_EXINFO_TTL = 600.0  # 10 minutes

async def get_exchange_info(exchange) -> Dict[str, Any]:
    global _EXINFO_CACHE, _EXINFO_TS
    now = time.time()
    if _EXINFO_CACHE and now - _EXINFO_TS < _EXINFO_TTL:
        return _EXINFO_CACHE
    # ccxt binance: endpoint brut
    info = await exchange.publicGetExchangeInfo()
    _EXINFO_CACHE = info
    _EXINFO_TS = now
    return info

async def get_symbol_info(exchange, symbol: str) -> Dict[str, Any]:
    info = await get_exchange_info(exchange)
    for s in info.get("symbols", []):
        if s.get("symbol") == symbol.replace("/", ""):
            return s
    raise KeyError(f"Symbol info not found for {symbol}")

async def with_rate_limit_retry(fn: Callable[..., Awaitable], *args, **kwargs):
    """Enveloppe d'appel avec respect de Retry-After en cas de 429/418."""
    try:
        return await fn(*args, **kwargs)
    except ExchangeError as e:
        # ccxt n'expose pas toujours headers; fallback 60s
        retry_after = 60
        hdrs = getattr(e, "response_headers", None)
        if hdrs and isinstance(hdrs, dict):
            ra = hdrs.get("Retry-After")
            if ra:
                try:
                    retry_after = int(ra)
                except Exception:
                    pass
        await asyncio.sleep(retry_after)
        raise
