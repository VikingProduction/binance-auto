async def fetch_multiple_ohlcv(exchange, symbols, timeframe, limit):
    tasks = [
        safe_api_call(exchange.fetch_ohlcv, symbol, timeframe, limit)
        for symbol in symbols[:10]  # Batch de 10 max
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {symbol: result for symbol, result in zip(symbols, results) 
            if not isinstance(result, Exception)}
