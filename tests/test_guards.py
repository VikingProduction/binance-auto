# tests/test_guards.py
import pytest
from src.guards import normalize_price_qty, check_percent_price_filters, check_min_notional, prepare_order

def test_normalize_and_round():
    symbol_info = {
        "filters": [
            {"filterType":"PRICE_FILTER","minPrice":"0.01","maxPrice":"100000","tickSize":"0.05"},
            {"filterType":"LOT_SIZE","minQty":"0.001","maxQty":"1000","stepSize":"0.001"},
        ]
    }
    p, q = normalize_price_qty(symbol_info, "BUY", 123.123, 0.123456)
    assert abs((p*20) - round(p*20)) < 1e-9  # tick 0.05
    assert abs((q*1000) - round(q*1000)) < 1e-9  # step 0.001

def test_percent_price_filters_ok():
    symbol_info = {"filters":[{"filterType":"PERCENT_PRICE","multiplierUp":"1.10","multiplierDown":"0.90"}]}
    check_percent_price_filters(symbol_info, "BUY", 100.0, 105.0)  # ok

def test_percent_price_filters_raises():
    symbol_info = {"filters":[{"filterType":"PERCENT_PRICE","multiplierUp":"1.10","multiplierDown":"0.90"}]}
    with pytest.raises(ValueError):
        check_percent_price_filters(symbol_info, "BUY", 100.0, 80.0)

def test_prepare_order_min_notional():
    symbol_info = {
        "filters": [
            {"filterType":"PRICE_FILTER","minPrice":"0.01","maxPrice":"100000","tickSize":"0.01"},
            {"filterType":"LOT_SIZE","minQty":"0.001","maxQty":"1000","stepSize":"0.001"},
            {"filterType":"MIN_NOTIONAL","minNotional":"10"}
        ]
    }
    with pytest.raises(ValueError):
        prepare_order(symbol_info, "BUY", 1.0, 1.0, 5.0)  # notional=5 < 10
