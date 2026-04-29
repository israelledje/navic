# 🚀 Guide de Démarrage Rapide - Navic GPS Tracking

## ✅ Checklist Complète

### 1. Installation des dépendances Python
```powershell
cd c:\Users\PC\Documents\projets dev\navic
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration PostgreSQL
```sql
-- Dans PostgreSQL (psql ou pgAdmin)
CREATE DATABASE navic_db;
CREATE USER navic_user WITH PASSWORD 'navic2026';
ALTER USER navic_user WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE navic_db TO navic_user;
```

### 3. Configuration Redis
```powershell
# Installer Redis sur Windows (via WSL ou binaire Windows)
# Ou utiliser Docker:
docker run -d -p 6379:6379 --name navic-redis redis:latest
```

### 4. Configuration de l'environnement
```powershell
cd navic
cp .env.example .env
# Éditer .env avec vos paramètres (DB, Redis, etc.)
```

### 5. Migrations de base de données
```powershell
python manage.py makemigrations accounts
python manage.py makemigrations billing
python manage.py makemigrations devices
python manage.py makemigrations tracking
python manage.py makemigrations alerts
python manage.py makemigrations fleet
python manage.py migrate
```

### 6. Créer un superutilisateur
```powershell
python manage.py createsuperuser
# Email: admin@navic.cg
# Nom: Admin
# Prénom: Navic
# Password: (votre mot de passe sécurisé)
```

### 7. Créer les packages de facturation
```powershell
python manage.py shell
```

Puis dans le shell Python:
```python
from billing.models import BillingPackage

# Package Gratuit
BillingPackage.objects.create(
    name="Gratuit",
    package_type="free",
    description="Package gratuit pour tester la plateforme",
    max_devices=1,
    max_sub_accounts=0,
    history_days=7,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    geofencing=False,
    fleet_management=False,
    api_access=False,
    price_monthly=0,
    price_yearly=0,
    is_public=True
)

# Package Starter
BillingPackage.objects.create(
    name="Starter",
    package_type="starter",
    description="Package idéal pour les particuliers et petites entreprises",
    max_devices=5,
    max_sub_accounts=2,
    history_days=30,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    geofencing=True,
    fleet_management=False,
    api_access=False,
    price_monthly=15000,
    price_yearly=150000,
    is_public=True
)

# Package Professionnel
BillingPackage.objects.create(
    name="Professionnel",
    package_type="professional",
    description="Pour les entreprises avec une flotte moyenne",
    max_devices=20,
    max_sub_accounts=10,
    history_days=90,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    geofencing=True,
    fleet_management=True,
    api_access=True,
    custom_reports=True,
    price_monthly=50000,
    price_yearly=500000,
    is_public=True
)

# Package Entreprise
BillingPackage.objects.create(
    name="Entreprise",
    package_type="enterprise",
    description="Solution complète pour grandes flottes",
    max_devices=100,
    max_sub_accounts=50,
    history_days=365,
    realtime_tracking=True,
    reports_enabled=True,
    alerts_enabled=True,
    geofencing=True,
    fleet_management=True,
    api_access=True,
    custom_reports=True,
    price_monthly=150000,
    price_yearly=1500000,
    is_public=True
)

print("✅ Packages créés avec succès!")
exit()
```

### 8. Créer quelques modèles de devices (optionnel)
```powershell
python manage.py shell
```

```python
from devices.models import DeviceModel

DeviceModel.objects.create(
    name="GT06",
    manufacturer="Generic",
    protocol="GT06",
    description="Tracker GPS standard GT06"
)

DeviceModel.objects.create(
    name="TK103",
    manufacturer="Xexun",
    protocol="TK103",
    description="Tracker GPS TK103"
)

DeviceModel.objects.create(
    name="FMB920",
    manufacturer="Teltonika",
    protocol="FMXXXX",
    description="Tracker GPS Teltonika FMB920"
)

print("✅ Modèles de devices créés!")
exit()
```

### 9. Lancer les services de backend (Background Tasks)

Pour que les positions GPS soient enregistrées en base de données de manière optimale, vous devez lancer le processeur de buffer.

```powershell
# Terminal 1 - Processeur de buffer GPS (Obligatoire pour l'historique)
python manage.py process_gps_buffer --interval 30 --batch-size 500
```

### 10. Lancer le serveur Django (Web & WebSockets)

```powershell
# Terminal 2 - Serveur Web (Daphne recommandé pour les WebSockets)
daphne -b 0.0.0.0 -p 8000 navic.asgi:application

# Ou pour le développement simple (sans WebSocket):
# python manage.py runserver
```

### 11. Lancer le service d'ingestion Go

```powershell
# Terminal 3 - Service de réception des données trackers
cd c:\Users\PC\Documents\projets dev\navic\ingestion
.\ingestion.exe
```

### 12. Lancer le frontend (React)

```powershell
# Terminal 4 - Interface utilisateur
cd c:\Users\PC\Documents\projets dev\navic\frontend
npm run dev
```

### 13. Vérifier que tout fonctionne

**Django Admin:**
- URL: http://localhost:8000/admin/
- Login avec le superuser créé à l'étape 6

**Service d'ingestion:**
- Serveur de commandes: http://localhost:8080
- Ports GPS ouverts (5027, 5029, 5031, 5033, 5035, 5039)

### 12. Test de l'API (optionnel)

**Créer un utilisateur via l'API:**
```powershell
# Utiliser Postman, curl ou httpie
curl -X POST http://localhost:8000/api/auth/register/ `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@navic.cg",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+242 06 123 45 67",
    "user_type": "individual"
  }'
```

**Se connecter:**
```powershell
curl -X POST http://localhost:8000/api/auth/login/ `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@navic.cg",
    "password": "Test123!"
  }'
```

## 📝 Commandes Utiles

### Développement
```powershell
# Shell Django
python manage.py shell

# Créer une nouvelle app
python manage.py startapp nom_app

# Créer des données de test
python manage.py loaddata fixtures/test_data.json

# Générer un fichier de fixtures
python manage.py dumpdata app.Model --indent 2 > fixtures/data.json
```

### Database
```powershell
# Reset complet de la DB (ATTENTION: perte de données!)
python manage.py flush

# Migrations
python manage.py showmigrations
python manage.py sqlmigrate app_name migration_name
```

### Collecte de fichiers statiques
```powershell
python manage.py collectstatic --noinput
```

## 🧪 Tests Rapides

### Test WebSocket (avec wscat)
```powershell
# Installer wscat
npm install -g wscat

# Tester WebSocket tracking
wscat -c "ws://localhost:8000/ws/tracking/user/"

# Tester WebSocket alertes
wscat -c "ws://localhost:8000/ws/alerts/"
```

### Test ingestion GPS
```powershell
# Envoyer des données GPS de test
curl -X POST http://localhost:8000/api/track/ingest/ `
  -H "Content-Type: application/json" `
  -d '{
    "imei": "123456789012345",
    "protocol": "GT06",
    "timestamp": "2026-01-19T15:00:00Z",
    "latitude": -4.2634,
    "longitude": 15.2429,
    "speed": 45.5,
    "heading": 180.0,
    "altitude": 300.0,
    "satellites": 12
  }'
```

## 🔧 Problèmes Courants

### "ModuleNotFoundError"
```powershell
# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

### "relation does not exist"
```powershell
# Recréer les migrations
python manage.py makemigrations
python manage.py migrate
```

### "Redis connection refused"
```powershell
# Vérifier que Redis est démarré
redis-cli ping
# Devrait retourner "PONG"
```

### "psycopg2 not found"
```powershell
# Installer psycopg2
pip install psycopg2-binary
```

## 📋 Prochaines Étapes

1. ✅ Installer et configurer l'environnement
2. ✅ Créer la structure de la base de données
3. ⏭️ Créer les serializers pour chaque modèle
4. ⏭️ Créer les ViewSets pour l'API REST
5. ⏭️ Configurer les URLs de l'API
6. ⏭️ Tester l'ingestion GPS end-to-end
7. ⏭️ Développer le frontend (React/Vue/Angular)
8. ⏭️ Déployer en production

## 🎯 Architecture Complète

Pour comprendre l'architecture complète, consultez:
- `API_ARCHITECTURE.md` - Documentation technique détaillée
- `README.md` - Guide d'utilisation complet

---

**Bon développement ! 🚀**

En cas de problème, vérifier:
1. Tous les services sont démarrés (Django, Redis, PostgreSQL, Service Go)
2. Les variables d'environnement sont correctes (.env)
3. Les migrations sont à jour
4. Les logs dans `logs/navic.log`
