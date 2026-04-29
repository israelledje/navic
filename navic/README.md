# Navic - Plateforme de Tracking GPS

Plateforme complète de suivi GPS en temps réel avec gestion de flotte, alertes intelligentes et facturation intégrée.

## 🚀 Quick Start

### Prérequis
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Service d'ingestion Go (dans ../ingestion/)

### Installation

1. **Créer un environnement virtuel**
```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate
```

2. **Installer les dépendances**
```bash
pip install -r ../requirements.txt
```

3. **Configuration de l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

4. **Créer la base de données PostgreSQL**
```bash
# Dans PostgreSQL
CREATE DATABASE navic_db;
CREATE USER navic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE navic_db TO navic_user;
```

5. **Exécuter les migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

7. **Créer les données de base (packages de facturation)**
```bash
python manage.py shell
```
```python
from billing.models import BillingPackage

# Package Gratuit
BillingPackage.objects.create(
    name="Gratuit",
    package_type="free",
    max_devices=1,
    max_sub_accounts=0,
    history_days=7,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    price_monthly=0,
    price_yearly=0,
    is_public=True
)

# Package Starter
BillingPackage.objects.create(
    name="Starter",
    package_type="starter",
    max_devices=5,
    max_sub_accounts=2,
    history_days=30,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    geofencing=True,
    price_monthly=15000,
    price_yearly=150000,
    is_public=True
)

# Package Professionnel
BillingPackage.objects.create(
    name="Professionnel",
    package_type="professional",
    max_devices=20,
    max_sub_accounts=10,
    history_days=90,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    api_access=True,
    geofencing=True,
    fleet_management=True,
    custom_reports=True,
    price_monthly=50000,
    price_yearly=500000,
    is_public=True
)

# Package Entreprise
BillingPackage.objects.create(
    name="Entreprise",
    package_type="enterprise",
    max_devices=100,
    max_sub_accounts=50,
    history_days=365,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    api_access=True,
    geofencing=True,
    fleet_management=True,
    custom_reports=True,
    price_monthly=150000,
    price_yearly=1500000,
    is_public=True
)
```

8. **Lancer Redis**
```bash
# Assurez-vous que Redis est démarré
redis-server
```

9. **Lancer le serveur Django**
```bash
# Mode développement
python manage.py runserver

# Ou avec Daphne (pour WebSockets)
daphne -b 0.0.0.0 -p 8000 navic.asgi:application
```

10. **Lancer le service d'ingestion Go**
```bash
cd ../ingestion
./ingestion.exe  # Windows
# ou
./ingestion_linux  # Linux
```

## 📡 Architecture

### Applications
- **accounts**: Gestion utilisateurs, sous-comptes, permissions
- **billing**: Packages, abonnements, paiements, factures
- **devices**: Trackers GPS, commandes, configuration
- **tracking**: Positions GPS, trajets, géofences, rapports
- **alerts**: Règles d'alerte, notifications multi-canaux
- **fleet**: Groupes, conducteurs, carburant, maintenance

### Technologies
- Django 6.0.1 + Django REST Framework
- Django Channels (WebSockets temps réel)
- PostgreSQL (base de données)
- Redis (cache + channel layer)
- JWT Authentication

### Flux de données
```
GPS Tracker → Service Go (ingestion) → Django API → PostgreSQL
                                     ↓
                                  WebSocket → Frontend
                                     ↓
                                  Alertes → Email/SMS/Push
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion (JWT)
- `POST /api/auth/refresh/` - Refresh token

### Devices
- `GET /api/devices/` - Liste des devices
- `POST /api/devices/` - Créer un device
- `GET /api/devices/{id}/` - Détails
- `PUT /api/devices/{id}/` - Modifier
- `POST /api/devices/{id}/command/` - Envoyer commande

### Tracking
- `POST /api/track/ingest/` - Ingestion GPS (depuis service Go)
- `GET /api/track/positions/` - Historique positions
- `GET /api/track/trips/` - Liste des trajets
- `POST /api/track/geofences/` - Créer géofence
- `POST /api/track/reports/generate/` - Générer rapport

### Alerts
- `GET /api/alerts/` - Liste des alertes
- `GET /api/alerts/rules/` - Règles d'alerte
- `POST /api/alerts/rules/` - Créer règle
- `POST /api/alerts/{id}/acknowledge` - Acquitter

### Fleet
- `GET /api/fleet/groups/` - Groupes de devices
- `GET /api/fleet/drivers/` - Conducteurs
- `POST /api/fleet/fuel/` - Enregistrer plein
- `GET /api/fleet/statistics/` - Statistiques

## 🔄 WebSockets

### Tracking temps réel
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tracking/user/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'position_update') {
    // Mettre à jour la position sur la carte
    console.log(data.data);
  }
};
```

### Alertes temps réel
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'new_alert') {
    // Afficher notification
    console.log(data.data);
  }
};
```

## 🧪 Tests

```bash
# Tous les tests
python manage.py test

# Tests d'une app spécifique
python manage.py test accounts

# Avec coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 Migrations

```bash
# Créer migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations

# Annuler une migration
python manage.py migrate app_name migration_name
```

## 🗄️ Base de données

### Backup
```bash
# Backup PostgreSQL
pg_dump -U navic_user navic_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U navic_user navic_db < backup_20260119.sql
```

### Shell Django
```bash
python manage.py shell

# OU avec shell_plus (nécessite django-extensions)
python manage.py shell_plus
```

## 🔐 Sécurité

- Secret key en production à changer absolument
- DEBUG=False en production
- HTTPS uniquement en production
- CORS correctement configuré
- JWT tokens avec expiration
- Permissions granulaires par endpoint

## 🚀 Déploiement Production

### Avec Docker (recommandé)
```bash
# À créer: docker-compose.yml
docker-compose up -d
```

### Sans Docker
1. Configurer Nginx comme reverse proxy
2. Utiliser Gunicorn + Uvicorn pour ASGI
3. Systemd pour gérer les services
4. PostgreSQL et Redis en services séparés
5. SSL avec Let's Encrypt

```bash
# Gunicorn avec Uvicorn workers
gunicorn navic.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers 4 \
  --access-logfile - \
  --error-logfile -
```

## 📊 Monitoring

- Logs dans `logs/navic.log`
- Django Admin: http://localhost:8000/admin/
- Sentry pour les erreurs (optionnel)
- Prometheus pour les métriques (optionnel)

## 🛠️ Développement

### Structure des fichiers
```
navic/
├── accounts/          # App utilisateurs
├── billing/           # App facturation
├── devices/           # App trackers GPS
├── tracking/          # App suivi GPS
│   ├── consumers.py   # WebSocket consumers
│   ├── routing.py     # WebSocket routing
│   └── views.py       # API views
├── alerts/            # App alertes
│   ├── tasks.py       # Traitement alertes
│   └── notifications.py  # Envoi notifications
├── fleet/             # App gestion flotte
├── navic/             # Settings projet
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py        # ASGI config
├── logs/              # Logs
├── media/             # Fichiers uploadés
├── manage.py
└── API_ARCHITECTURE.md  # Documentation API
```

### Conventions de code
- PEP 8 pour Python
- Noms de classes en CamelCase
- Noms de fonctions en snake_case
- Constants en UPPER_CASE
- Docstrings pour toutes les fonctions

## 📚 Documentation

- Architecture complète: `API_ARCHITECTURE.md`
- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Channels: https://channels.readthedocs.io/

## 🐛 Troubleshooting

### Erreur de connexion WebSocket
- Vérifier que Redis est démarré
- Vérifier la configuration CHANNEL_LAYERS dans settings.py

### Erreur de database
- Vérifier que PostgreSQL est démarré
- Vérifier les credentials dans .env

### Erreur de migration
```bash
# Réinitialiser les migrations (ATTENTION: perte de données)
python manage.py migrate app_name zero
python manage.py makemigrations
python manage.py migrate
```

## 📞 Support

Pour toute question, consulter la documentation ou contacter l'équipe de développement.

---

**Version**: 1.0
**Date**: 19 janvier 2026
**Auteur**: Équipe Navic
