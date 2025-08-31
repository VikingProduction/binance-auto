import pandas as pd
import ta

def compute_indicators(df: pd.DataFrame, strat_cfg: dict) -> pd.DataFrame:
    rsi_w = strat_cfg['rsi_window']
    sma_s = strat_cfg['sma_short_window']
    sma_l = strat_cfg['sma_long_window']
    df['SMA_short'] = ta.trend.SMAIndicator(df['close'], window=sma_s).sma_indicator()
    df['SMA_long']  = ta.trend.SMAIndicator(df['close'], window=sma_l).sma_indicator()
    df['RSI']       = ta.momentum.RSIIndicator(df['close'], window=rsi_w).rsi()
    return df
