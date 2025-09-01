# tests/test_risk.py
from src.persistence import load, state, roll_daily_if_needed

def test_daily_rollover_and_pnl(tmp_path, monkeypatch):
    monkeypatch.setenv("BOT_STATE_PATH", str(tmp_path / "state.json"))
    s = load()
    assert s["daily"]["realized_pnl_quote"] == 0.0
    roll_daily_if_needed("2025-09-01")
    st = state()
    assert st["daily"]["date"] == "2025-09-01"
