# src/metrics.py

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Métriques principales
bot_order_total = Counter(
    "bot_order_total",
    "Nombre total d’ordres exécutés par le bot",
    ["action"]  # 'buy' ou 'sell'
)
bot_rate_limit_total = Counter(
    "bot_rate_limit_total",
    "Nombre de fois que le bot a été throttlé par l’API"
)
bot_ban_total = Counter(
    "bot_ban_total",
    "Nombre de bannissements (HTTP 418) détectés"
)
bot_daily_pnl = Gauge(
    "bot_daily_pnl",
    "Profit ou perte cumulé(e) du jour (en quote asset)"
)
open_positions = Gauge(
    "bot_open_positions",
    "Nombre de positions ouvertes actuellement"
)
order_latency = Histogram(
    "bot_order_latency_seconds",
    "Temps de latence pour placer un ordre (secondes)"
)

# Indicateur global pour éviter de relancer plusieurs serveurs HTTP
_metrics_started = False

def start_metrics_server(port: int = 8000) -> None:
    """
    Démarre le serveur HTTP Prometheus sur le port spécifié (par défaut 8000).
    Appeler une seule fois au démarrage du bot.
    """
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True

def record_order(action: str, latency: float) -> None:
    """
    Incrémente le compteur d’ordres et enregistre la latence.
    :param action: 'buy' ou 'sell'
    :param latency: délai (en secondes) entre l’envoi et la confirmation de l’ordre
    """
    bot_order_total.labels(action=action).inc()
    order_latency.observe(latency)

def record_rate_limit() -> None:
    """
    Incrémente le compteur de rate limits.
    """
    bot_rate_limit_total.inc()

def record_ban() -> None:
    """
    Incrémente le compteur de bans.
    """
    bot_ban_total.inc()

def update_daily_pnl(amount: float) -> None:
    """
    Met à jour la gauge du P&L quotidien en ajoutant le montant spécifié.
    :param amount: profit (positif) ou perte (négatif) en quote asset
    """
    # Lecture de la valeur actuelle puis mise à jour
    current = bot_daily_pnl._value.get()
    bot_daily_pnl.set(current + amount)

def set_open_positions(count: int) -> None:
    """
    Définit le nombre de positions ouvertes.
    :param count: nombre total de positions ouvertes
    """
    open_positions.set(count)
