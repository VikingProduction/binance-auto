# src/guards.py
import math

def round_down(value: float, step: float) -> float:
    return math.floor(value / step) * step

def apply_price_filter(symbol_info: dict, price: float) -> float:
    tick = float(symbol_info['filters_dict']['PRICE_FILTER']['tickSize'])
    return round_down(price, tick)

def apply_lot_size(symbol_info: dict, qty: float) -> float:
    step = float(symbol_info['filters_dict']['LOT_SIZE']['stepSize'])
    return round_down(qty, step)

def check_min_notional(symbol_info: dict, price: float, qty: float) -> bool:
    min_notional = float(symbol_info['filters_dict']['MIN_NOTIONAL']['minNotional'])
    return (price * qty) >= min_notional

def build_filters(markets: list) -> dict:
    """
    Retourne un dict {symbol: {'filters_dict': {filterType: filterObj}}}
    """
    mf = {}
    for m in markets:
        d = {f['filterType']: f for f in m['filters']}
        mf[m['symbol']] = {'filters_dict': d}
    return mf
