import ccxt.pro as ccxtpro
import asyncio
import logging

logger = logging.getLogger(__name__)


class WebSocketStreamer:
    def __init__(self, exchange):
        self.exchange = exchange
        self.price_data = {}
    
    async def stream_tickers(self, symbols):
        while True:
            try:
                ticker = await self.exchange.watch_ticker(symbols[0])
                self.price_data[ticker['symbol']] = ticker
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)
