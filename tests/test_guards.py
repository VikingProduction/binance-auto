import pytest
from src.guards import round_down, apply_price_filter, apply_lot_size, check_min_notional

class DummyInfo:
    filters_dict = {
        'PRICE_FILTER': {'tickSize': '0.01'},
        'LOT_SIZE': {'stepSize': '0.1'},
        'MIN_NOTIONAL': {'minNotional': '10'}
    }

def test_round_down():
    assert round_down(1.234, 0.01) == 1.23

def test_apply_price_filter():
    assert apply_price_filter({'filters_dict': DummyInfo.filters_dict}, 1.237) == 1.23

def test_apply_lot_size():
    assert apply_lot_size({'filters_dict': DummyInfo.filters_dict}, 2.34) == 2.3

def test_check_min_notional_true():
    assert check_min_notional({'filters_dict': DummyInfo.filters_dict}, 1.0, 10.0)

def test_check_min_notional_false():
    assert not check_min_notional({'filters_dict': DummyInfo.filters_dict}, 0.5, 1.0)
