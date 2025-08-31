# Guide de déploiement

## Prérequis
- Clés API Binance (spot/futures)
- GitHub repository avec Secrets :
  - API_KEY, API_SECRET
  - EMAIL_USER, EMAIL_PASS, EMAIL_TO

## Étapes
1. Cloner le dépôt  
git clone ... && cd binance-auto

2. Ajouter `config.yml` à la racine.  
3. Installer les dépendances  
pip install -r requirements.txt

4. Créer les dossiers `docs/` et y placer `architecture.md` et `deployment.md`.  
5. Pousser les changements et vérifier le workflow GitHub Actions.  
6. Accéder aux métriques sur `http://<runner-ip>:8000/metrics`.  

## Monitoring & Alerting
- Prometheus scrape `:8000/metrics`.  
- Configurer Grafana pour dashboard.  
- Alerts Slack sur bans et pertes journalières via webhook.
