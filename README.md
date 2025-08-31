# Trading Bot Automatisé

## Description
Bot Python multi-indicateurs (RSI, SMA) déployé via GitHub Actions pour exécuter et gérer plusieurs positions simultanément sur Binance.

## Configuration
1. Forkez ce dépôt.  
2. Ajoutez vos **Secrets** GitHub :  
   - `API_KEY`, `API_SECRET`  
   - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO`  

## Utilisation
- Le bot s’exécute chaque heure (cron) ou manuellement via GitHub Actions.  
- Un rapport journalier de vos ordres est envoyé par email.

## Structure
- `src/indicators.py` : calcul des indicateurs.  
- `src/main.py`       : logique de trading.  
- `src/reporter.py`   : envoi d’email.  
- `.github/workflows/deploy.yml` : CI/CD.

## Personnalisation
- Modifiez la liste `SYMBOLS` dans `main.py` pour ajouter vos paires.  
- Ajustez les paramètres RSI et SMA selon votre stratégie.
