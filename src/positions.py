# src/positions.py
import logging

logger = logging.getLogger('trading_bot')

def normalize_positions(raw):
    """
    Prend en entrée raw = list ou dict retourné par fetch_positions()
    et renvoie un dict {symbol: {'size': float, 'entryPrice': float}}
    """
    out = {}
    # Cas dict {symbol: {...}}
    if isinstance(raw, dict):
        items = raw.items()
    # Cas list [{'symbol':..., 'positionAmt':..., 'entryPrice':...}, ...]
    else:
        items = [(p.get('symbol'), p) for p in raw]
    for symbol, data in items:
        try:
            size = float(data.get('size') or data.get('positionAmt') or 0)
            entry = float(data.get('entryPrice') or data.get('entryPrice') or 0)
            out[symbol] = {'size': size, 'entryPrice': entry}
        except Exception as e:
            logger.error(f"normalize_positions failed for {symbol}: {e}")
    return out
