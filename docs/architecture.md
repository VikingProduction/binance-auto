# Architecture du Trading Bot

flowchart LR
A[GitHub Actions] --> B[Container Python Bot]
B --> C[fetch_markets & exchangeInfo]
C --> D[build_filters & normalize_positions]
B --> E[fetch_ohlcv (async)]
E --> F[compute_indicators]
F --> G[decide_and_execute (guards)]
G --> H[create_order]
H --> I[persistence & metrics]
I --> J[Prometheus endpoint]
A --> K[action-send-mail report]
