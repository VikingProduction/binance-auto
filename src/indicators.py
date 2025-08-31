import pandas as pd
import ta

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # SMA courts et longs
    df['SMA_short'] = ta.trend.SMAIndicator(df['close'], window=10).sma_indicator()
    df['SMA_long']  = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
    # RSI
    df['RSI']       = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    return df
