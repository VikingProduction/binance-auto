# binance-auto

Un bot de trading automatisé asynchrone pour Binance, conçu pour être robuste, sécurisé et prêt pour la production. Il applique systématiquement les règles d'Exchange, gère les limites d'API, expose des métriques Prometheus et persiste l'état des positions pour un trailing-stop fiable.

## ⚙️ Fonctionnalités principales

- **Stratégie multi-indicateurs**
  - RSI(14), SMA courte (10) et SMA longue (50)
  - Signaux d'achat (RSI < 30 & SMA_short > SMA_long)
  - Take-profit et trailing-stop configurables

- **Conformité Exchange**
  - Guards PRICE_FILTER, LOT_SIZE et MIN_NOTIONAL avant chaque ordre
  - Erreurs "Filter failure" quasi éliminées

- **Asynchronisme & résilience**
  - `ccxt.async_support` + `asyncio` pour appels parallèles
  - Retry exponentiel + jitter sur erreurs réseau et rate limits
  - Détection et journalisation des bans (HTTP 418)

- **Observabilité & alerting**
  - Serveur Prometheus exposant compteurs d'ordres, rate limits, bans et pertes journalières
  - Intégration possible avec Grafana et notifications Slack/Telegram

- **Gestion de l'état**
  - Normalisation de tous les formats renvoyés par `fetch_positions()`
  - Persistance des prix d'entrée des positions pour reprise après redémarrage

- **CI/CD & reporting**
  - Exécution horaire via GitHub Actions
  - Rapport quotidien envoyé par `action-send-mail`
  - Pas de gestion SMTP dans le code

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

## 🔐 Configuration des secrets GitHub

Avant de déployer le bot, vous devez configurer les secrets suivants dans votre dépôt GitHub :

### Secrets requis

| Secret | Description | Comment l'obtenir |
|--------|-------------|-------------------|
| `API_KEY` | Clé API Binance | Voir section "Création des clés API Binance" |
| `API_SECRET` | Secret API Binance | Obtenu en même temps que l'API_KEY |
| `EMAIL_USER` | Adresse Gmail pour l'envoi de rapports | Votre adresse Gmail complète |
| `EMAIL_PASS` | Mot de passe d'application Gmail | Voir section "Création du mot de passe d'application Gmail" |
| `EMAIL_TO` | Adresse de réception des rapports | Adresse email où recevoir les rapports |

### Comment ajouter les secrets GitHub

1. Allez sur la page principale de votre dépôt GitHub
2. Cliquez sur **Settings** (Paramètres)
3. Dans la barre latérale, sous "Security", cliquez sur **Secrets and variables** → **Actions**
4. Cliquez sur **New repository secret**
5. Entrez le nom du secret (ex: `API_KEY`)
6. Entrez la valeur du secret
7. Cliquez sur **Add secret**

### Création des clés API Binance

1. **Connectez-vous à votre compte Binance**
   - Assurez-vous que votre compte est entièrement vérifié (Basic + Intermediate)
   - Effectuez un premier dépôt pour activer l'API

2. **Accédez à la gestion API**
   - Cliquez sur votre icône de profil → **Account**
   - Sélectionnez **API Management**

3. **Créez une nouvelle API**
   - Cliquez sur **Create API**
   - Choisissez "System Generated" (recommandé)
   - Donnez un nom descriptif (ex: "Trading Bot")

4. **Configurez les permissions** ⚠️ **IMPORTANT**
   - **Enable Spot & Margin Trading** : ✅ Activé
   - **Enable Futures** : ❌ Désactivé (pour plus de sécurité)
   - **Enable Withdrawals** : ❌ Désactivé (fortement recommandé)

5. **Restrictions IP** (Fortement recommandé)
   - Ajoutez les IPs de GitHub Actions ou votre serveur
   - Pour GitHub Actions, vous pouvez utiliser des services comme ngrok pour obtenir une IP fixe

6. **Sauvegardez vos clés**
   - Copiez immédiatement l'**API Key** et l'**API Secret**
   - ⚠️ L'API Secret ne sera plus jamais affiché
   - Stockez-les de manière sécurisée

### Création du mot de passe d'application Gmail

1. **Activez la vérification en 2 étapes**
   - Allez sur https://myaccount.google.com/security
   - Sous "Se connecter à Google", activez la "Validation en 2 étapes"
   - Suivez les instructions pour configurer votre téléphone

2. **Créez le mot de passe d'application**
   - Allez sur https://myaccount.google.com/apppasswords
   - Ou cherchez "app password" dans les paramètres de votre compte
   - Entrez un nom pour l'application (ex: "Binance Bot")
   - Cliquez sur **Create**

3. **Sauvegardez le mot de passe**
   - Copiez immédiatement le mot de passe généré (16 caractères)
   - ⚠️ Il ne sera plus jamais affiché
   - Utilisez ce mot de passe comme valeur pour `EMAIL_PASS`

## ⚙️ Installation

1. **Clonez le dépôt**
   ```bash
   git clone https://github.com/VikingProduction/binance-auto.git
   cd binance-auto
   ```

2. **Installez les dépendances**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Créez et éditez `config.yml`**
   ```bash
   cp config.yml.example config.yml
   # Éditez le fichier selon vos besoins
   ```

## 📝 Configuration (config.yml)

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

## 🚀 Déploiement via GitHub Actions

Le workflow `.github/workflows/deploy.yml` s'exécute automatiquement :
- **Fréquence** : Toutes les heures
- **Rapport quotidien** : Envoyé par email avec les résultats
- **Secrets requis** : Tous les secrets listés ci-dessus

### Activation du workflow

1. Après avoir configuré tous les secrets, le workflow se déclenchera automatiquement
2. Vous pouvez aussi le déclencher manuellement depuis l'onglet "Actions" de votre dépôt
3. Les logs d'exécution sont visibles dans la section "Actions"

## 📊 Monitoring & Alerting

### Métriques Prometheus disponibles

- `bot_order_total{action="buy"}` : Nombre total d'ordres d'achat
- `bot_order_total{action="sell"}` : Nombre total d'ordres de vente
- `bot_rate_limit_total` : Nombre de rate limits rencontrés
- `bot_ban_total` : Nombre de bans détectés
- `bot_daily_loss` : Pertes journalières

### Configuration recommandée

1. **Prometheus** : Scraper `http://<runner>:8000/metrics`
2. **Grafana** : Créer un dashboard avec les métriques ci-dessus
3. **Alertes** : Configurer des notifications Slack/Telegram pour :
   - Détection de bans (`bot_ban_total`)
   - Pertes journalières excessives (`bot_daily_loss`)
   - Rate limits fréquents (`bot_rate_limit_total`)

## 🛠 Tests

Validez l'installation avec les tests automatisés :

```bash
pytest --maxfail=1 --disable-warnings -q
```

## 🔒 Sécurité & Bonnes Pratiques

### Sécurité des API Binance
- ✅ Utilisez des restrictions IP quand possible
- ✅ Désactivez les retraits sur l'API
- ✅ Limitez aux permissions Spot Trading uniquement
- ✅ Surveillez régulièrement l'activité de l'API
- ✅ Renouvelez périodiquement vos clés API

### Sécurité GitHub
- ✅ Ne commitez jamais vos clés dans le code
- ✅ Utilisez uniquement les GitHub Secrets
- ✅ Limitez l'accès au dépôt aux personnes autorisées
- ✅ Activez la vérification en 2 étapes sur GitHub

### Gestion des risques
- ⚠️ Commencez avec de petites positions (`position_size_pct: 0.01`)
- ⚠️ Testez en mode paper trading d'abord si disponible
- ⚠️ Surveillez les performances quotidiennement
- ⚠️ Définissez des limites de perte strictes

## 📚 Documentation

- `docs/architecture.md` : Schéma Mermaid de l'architecture
- `docs/deployment.md` : Guide détaillé de déploiement et monitoring

## 🤝 Support

- **Issues** : Utilisez les GitHub Issues pour signaler des bugs
- **Discussions** : Section Discussions GitHub pour les questions
- **Email** : Contact via les issues uniquement

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

## ⚠️ Avertissement

Ce bot est fourni à des fins éducatives. Le trading automatisé comporte des risques significatifs. Utilisez-le uniquement avec des fonds que vous pouvez vous permettre de perdre. Les développeurs ne sont pas responsables des pertes financières.

**Mainteneur** : VikingProduction  
**Version** : 1.0.0  
**Dernière mise à jour** : Septembre 2025
