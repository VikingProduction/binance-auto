# src/metrics.py
from prometheus_client import Counter, Histogram, start_http_server
import threading

# Compteurs
ORDER_COUNT = Counter('bot_order_total', 'Total orders placed', ['action'])
RATE_LIMITS = Counter('bot_rate_limit_total', 'Total rate limit hits')
BANS = Counter('bot_ban_total', 'Total ban (418) events')
DAILY_LOSS = Histogram('bot_daily_loss', 'Daily PnL losses')

def start_metrics_server(port=8000):
    thread = threading.Thread(target=start_http_server, args=(port,), daemon=True)
    thread.start()
