# Trading Bot Automatisé Avancé

## Description
Bot Python asynchrone multi-indicateurs (RSI, SMA) avec trailing-stop et take-profit, backtesting, filtrage dynamique de paires, déployé via GitHub Actions.

## Fichiers clés
- `config.yml`        : paramètres de stratégie et API  
- `src/utils.py`      : logging et chargement de config  
- `src/indicators.py` : calcul des indicateurs  
- `src/main.py`       : bot asynchrone  
- `src/reporter.py`   : reporting avancé avec graphique  
- `src/backtest.py`   : script de backtest  
- `.github/workflows/deploy.yml` : CI GitHub Actions  

## Installation
pip install -r requirements.txt


## Configuration
1. Éditez `config.yml`.  
2. Ajoutez les **Secrets** GitHub :  
   - `API_KEY`, `API_SECRET`  
   - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO`  

## Usage
- **Bot réel** : CI horaire ou manuel via GitHub Actions.  
- **Backtest** :  python src/backtest.py
