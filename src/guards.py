# src/guards.py
import math
from typing import Tuple, Dict, Any

def _round_down_to_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return math.floor(value / step) * step

def normalize_price_qty(symbol_info: Dict[str, Any], side: str, price: float, qty: float) -> Tuple[float, float]:
    """Applique PRICE_FILTER et LOT_SIZE (min/max + arrondi tick/step)."""
    filters = {f["filterType"]: f for f in symbol_info.get("filters", [])}

    pf = filters.get("PRICE_FILTER")
    if pf:
        min_price = float(pf.get("minPrice", "0"))
        max_price = float(pf.get("maxPrice", "1000000000"))
        tick = float(pf.get("tickSize", "0"))
        price = max(min_price, min(max_price, price))
        if tick > 0:
            price = _round_down_to_step(price, tick)

    ls = filters.get("LOT_SIZE") or filters.get("MARKET_LOT_SIZE")
    if ls:
        min_qty = float(ls.get("minQty", "0"))
        max_qty = float(ls.get("maxQty", "1000000000"))
        step = float(ls.get("stepSize", "0"))
        qty = max(min_qty, min(max_qty, qty))
        if step > 0:
            qty = _round_down_to_step(qty, step)

    return price, qty

def check_min_notional(symbol_info: Dict[str, Any], quote_price: float, qty: float) -> None:
    filters = {f["filterType"]: f for f in symbol_info.get("filters", [])}
    mn = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")
    if mn:
        min_notional = float(mn.get("minNotional") or mn.get("notional") or "0")
        if quote_price * qty < min_notional:
            raise ValueError("Filter failure: MIN_NOTIONAL")

def check_percent_price_filters(symbol_info: Dict[str, Any], side: str, last_price: float, order_price: float) -> None:
    """Valide PERCENT_PRICE et PERCENT_PRICE_BY_SIDE si présents."""
    filters = {f["filterType"]: f for f in symbol_info.get("filters", [])}

    pp = filters.get("PERCENT_PRICE")
    if pp:
        up = float(pp.get("multiplierUp", "999"))
        dn = float(pp.get("multiplierDown", "0"))
        if not (last_price * dn <= order_price <= last_price * up):
            raise ValueError("Filter failure: PERCENT_PRICE")

    pps = filters.get("PERCENT_PRICE_BY_SIDE")
    if pps:
        if side.upper() == "BUY":
            up = float(pps.get("askMultiplierUp", "999"))
            dn = float(pps.get("askMultiplierDown", "0"))
        else:
            up = float(pps.get("bidMultiplierUp", "999"))
            dn = float(pps.get("bidMultiplierDown", "0"))
        if not (last_price * dn <= order_price <= last_price * up):
            raise ValueError("Filter failure: PERCENT_PRICE_BY_SIDE")

def prepare_order(
    symbol_info: Dict[str, Any],
    side: str,
    last_price: float,
    desired_price: float,
    desired_qty: float,
) -> Tuple[float, float]:
    """Pipeline complet: normalisation + vérifs pour réduire les erreurs 1013."""
    price, qty = normalize_price_qty(symbol_info, side, desired_price, desired_qty)
    check_percent_price_filters(symbol_info, side, last_price, price)
    check_min_notional(symbol_info, last_price, qty)
    return price, qty
