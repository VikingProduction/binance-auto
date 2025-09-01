# src/positions.py
import time
from typing import Dict, Any, Optional, Union
from persistence import state, save
from metrics import open_positions

def set_position(symbol: str, qty: float, entry_price: float):
    """Enregistre une nouvelle position"""
    st = state()
    st["positions"][symbol] = {
        "qty": float(qty),
        "entry_price": float(entry_price),
        "timestamp": time.time(),
        "symbol": symbol
    }
    open_positions.set(len(st["positions"]))
    save()

def clear_position(symbol: str):
    """Supprime une position"""
    st = state()
    if symbol in st["positions"]:
        del st["positions"][symbol]
    open_positions.set(len(st["positions"]))
    save()

def get_position(symbol: str) -> Union[Dict[str, Any], None]:
    """Récupère les informations d'une position"""
    return state()["positions"].get(symbol)

def get_all_positions() -> Dict[str, Dict[str, Any]]:
    """Retourne toutes les positions ouvertes"""
    return state()["positions"]

def update_position_qty(symbol: str, new_qty: float):
    """Met à jour la quantité d'une position"""
    st = state()
    if symbol in st["positions"]:
        st["positions"][symbol]["qty"] = float(new_qty)
        if new_qty <= 0:
            del st["positions"][symbol]
        open_positions.set(len(st["positions"]))
        save()

def get_position_pnl(symbol: str, current_price: float) -> Optional[float]:
    """Calcule le PnL d'une position"""
    pos = get_position(symbol)
    if not pos:
        return None
    entry_price = pos['entry_price']
    qty = pos['qty']
    return (current_price - entry_price) * qty

def get_total_portfolio_value(current_prices: Dict[str, float]) -> float:
    """Calcule la valeur totale du portfolio"""
    total = 0.0
    for symbol, pos in get_all_positions().items():
        if symbol in current_prices:
            total += pos['qty'] * current_prices[symbol]
    return total

def close_all_positions():
    """Ferme toutes les positions (emergency stop)"""
    st = state()
    st["positions"] = {}
    open_positions.set(0)
    save()
