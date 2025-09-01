# src/positions.py
from typing import Dict, Any
from .persistence import state, save
from .metrics import open_positions

def set_position(symbol: str, qty: float, entry_price: float):
    st = state()
    st["positions"][symbol] = {"qty": qty, "entry_price": entry_price}
    open_positions.set(len(st["positions"]))
    save()

def clear_position(symbol: str):
    st = state()
    if symbol in st["positions"]:
        del st["positions"][symbol]
    open_positions.set(len(st["positions"]))
    save()

def get_position(symbol: str) -> Dict[str, Any] | None:
    return state()["positions"].get(symbol)
