import time
from typing import Dict, Optional
import pandas as pd

class OHLCVCache:
    def __init__(self, ttl_seconds=300):  # 5 min TTL
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl_seconds
    
    def get(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        key = f"{symbol}_{timeframe}"
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None
    
    def set(self, symbol: str, timeframe: str, data: pd.DataFrame):
        key = f"{symbol}_{timeframe}"
        self.cache[key] = (data, time.time())
