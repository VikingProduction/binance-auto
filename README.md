# binance-auto

Un bot de trading automatisé asynchrone pour Binance, conçu pour être robuste, sécurisé et prêt pour la production. Il applique systématiquement les règles d’Exchange, gère les limites d’API, expose des métriques Prometheus et persiste l’état des positions pour un trailing-stop fiable.

## ⚙️ Fonctionnalités principales

- **Stratégie multi-indicateurs**  
  - RSI(14), SMA courte (10) et SMA longue (50)  
  - Signaux d’achat (RSI < 30 & SMA_short > SMA_long)  
  - Take-profit et trailing-stop configurables  

- **Conformité Exchange**  
  - Guards PRICE_FILTER, LOT_SIZE et MIN_NOTIONAL avant chaque ordre  
  - Erreurs “Filter failure” quasi éliminées  

- **Asynchronisme & résilience**  
  - `ccxt.async_support` + `asyncio` pour appels parallèles  
  - Retry exponentiel + jitter sur erreurs réseau et rate limits  
  - Détection et journalisation des bans (HTTP 418)  

- **Observabilité & alerting**  
  - Serveur Prometheus exposant compteurs d’ordres, rate limits, bans et pertes journalières  
  - Intégration possible avec Grafana et notifications Slack/Telegram  

- **Gestion de l’état**  
  - Normalisation de tous les formats renvoyés par `fetch_positions()`  
  - Persistance des prix d’entrée des positions pour reprise après redémarrage  

- **CI/CD & reporting**  
  - Exécution horaire via GitHub Actions  
  - Rapport quotidien envoyé par `action-send-mail`  
  - Pas de gestion SMTP dans le code  

- **Documentation & tests**  
  - Schéma d’architecture Mermaid (`docs/architecture.md`)  
  - Guide de déploiement (`docs/deployment.md`)  
  - Tests Pytest pour les guards et la normalisation des positions  

---

## 📁 Structure du dépôt

```
.
├── .github
│   └── workflows
│       └── deploy.yml
├── docs
│   ├── architecture.md
│   └── deployment.md
├── src
│   ├── guards.py
│   ├── indicators.py
│   ├── main.py
│   ├── metrics.py
│   ├── persistence.py
│   ├── positions.py
│   └── utils.py
├── tests
│   └── test_guards.py
├── config.yml
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

1. Clonez le dépôt  
   ```bash
   git clone https://github.com/VikingProduction/binance-auto.git
   cd binance-auto
   ```
2. Installez les dépendances  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Créez et éditez `config.yml` à la racine du dépôt (exemple ci-dessous).

---

## 📝 Exemple de config.yml

```yaml
bot:
  exchange: binance
  timeframe: '1h'
  limit: 200
  filter_bases: ['BTC','ETH','USDT','EUR']
  volume_threshold: 100000
  position_size_pct: 0.02

strategy:
  rsi_window: 14
  sma_short_window: 10
  sma_long_window: 50
  rsi_buy: 30
  rsi_sell: 70
  trailing_stop_pct: 0.02
  take_profit_pct: 0.05

risk:
  daily_loss_limit_pct: 0.05
  max_consecutive_losses: 3
  cooldown_hours: 4

email:
  to: ${{ secrets.EMAIL_TO }}
```

---

## 🚀 Déploiement (GitHub Actions)

Le workflow `.github/workflows/deploy.yml` exécute le bot toutes les heures et envoie le rapport quotidien par email :

- Seuls les secrets `API_KEY`, `API_SECRET`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO` sont nécessaires.  
- La sortie du bot (`journal`) est capturée et envoyée via `dawidd6/action-send-mail`.

---

## 📊 Monitoring & Alerting

- Démarrage automatique d’un serveur Prometheus sur le port `8000`.  
- Metrics exportées :  
  - `bot_order_total{action="buy"}` et `bot_order_total{action="sell"}`  
  - `bot_rate_limit_total`  
  - `bot_ban_total`  
  - `bot_daily_loss`  
- Configuration recommandée :  
  1. Scraper `http://<runner>:8000/metrics` depuis Prometheus.  
  2. Créer un dashboard Grafana.  
  3. Ajouter alertes Slack/Telegram pour les bans et pertes journalières.

---

## 🛠 Tests

Lancez les tests Pytest pour valider les guards et la normalisation des positions :

```bash
pytest --maxfail=1 --disable-warnings -q
```

---

## 📚 Documentation

- `docs/architecture.md` : schéma Mermaid de l’architecture.  
- `docs/deployment.md` : guide détaillé de déploiement et de monitoring.

---

> **Mainteneurs** : VikingProduction  
> **Licence** : MIT  
> **Contact** : via issues sur GitHub.
