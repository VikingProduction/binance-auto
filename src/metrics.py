# src/metrics.py
from prometheus_client import Counter, Gauge, Histogram, start_http_server

bot_order_total = Counter("bot_order_total", "Orders", ["action"])
bot_rate_limit_total = Counter("bot_rate_limit_total", "Rate limit hits")
bot_ban_total = Counter("bot_ban_total", "IP bans")
bot_daily_pnl = Gauge("bot_daily_pnl", "Daily PnL (quote)")
open_positions = Gauge("bot_open_positions", "Number of open positions")
order_latency = Histogram("bot_order_latency_seconds", "Latency to place orders (s)")

_metrics_started = False

def start_metrics_server(port: int = 8000):
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True
