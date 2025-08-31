# src/persistence.py
import json
from threading import Lock

_path = 'entries.json'
_lock = Lock()

def load_entries():
    try:
        with open(_path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_entries(data):
    with _lock:
        with open(_path, 'w') as f:
            json.dump(data, f, indent=2)

def set_entry(symbol, price):
    data = load_entries()
    data[symbol] = price
    save_entries(data)

def get_entry(symbol):
    return load_entries().get(symbol)
