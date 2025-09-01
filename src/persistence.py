# src/persistence.py
import json
import os
from typing import Dict, Any

_STATE_PATH = os.environ.get("BOT_STATE_PATH", "state.json")

_state: Dict[str, Any] = {
    "positions": {},              # par symbole
    "entries": {},                # infos d'entrée par symbole
    "daily": {"date": None, "realized_pnl_quote": 0.0},
}

def load() -> Dict[str, Any]:
    global _state
    if os.path.exists(_STATE_PATH):
        try:
            with open(_STATE_PATH, "r", encoding="utf-8") as f:
                _state = json.load(f)
        except Exception:
            pass
    return _state

def save():
    with open(_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(_state, f, ensure_ascii=False, indent=2)

def state() -> Dict[str, Any]:
    return _state

def roll_daily_if_needed(today_iso: str):
    if _state["daily"]["date"] != today_iso:
        _state["daily"] = {"date": today_iso, "realized_pnl_quote": 0.0}
        save()

def update_realized_pnl(delta_quote: float):
    _state["daily"]["realized_pnl_quote"] += float(delta_quote)
    save()
