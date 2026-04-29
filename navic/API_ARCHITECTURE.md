# Architecture API Navic - GPS Tracking Platform

## Vue d'ensemble

Cette architecture Django fournit une plateforme complète de tracking GPS avec:
- **Communication en temps réel** via Django Channels (WebSockets)
- **API REST** pour toutes les opérations CRUD
- **Ingestion GPS** depuis le service Go
- **Système d'alertes** multi-canaux (email, SMS, push, webhook)
- **Gestion de flotte** avancée
- **Facturation** et packages d'abonnement
- **Multi-utilisateurs** avec sous-comptes et permissions

---

## 📂 Structure des Applications

### 1. **accounts** - Gestion des utilisateurs

#### Modèles:
- **User**: Utilisateur personnalisé avec support multi-types (admin, entreprise, particulier, sous-compte)
- **SubAccountPermission**: Système de permissions granulaires pour les sous-comptes
- **UserActivity**: Journal d'activité utilisateur

#### Fonctionnalités:
- Authentification JWT (Simple JWT)
- Système de sous-comptes avec permissions par device
- Gestion des profils et préférences
- Journalisation des activités

---

### 2. **billing** - Facturation et abonnements

#### Modèles:
- **BillingPackage**: Packages de facturation (Gratuit, Starter, Pro, Enterprise, Custom)
- **Subscription**: Abonnements utilisateur (mensuel/annuel)
- **Payment**: Paiements avec support Mobile Money, carte, virement
- **Invoice**: Factures générées automatiquement

#### Fonctionnalités:
- Gestion des packages avec limites (devices, sous-comptes, historique)
- Abonnements avec auto-renouvellement
- Suivi des paiements multi-méthodes
- Génération de factures

---

### 3. **devices** - Gestion des trackers GPS

#### Modèles:
- **DeviceModel**: Modèles de devices (GT06, TK103, Teltonika, etc.)
- **Device**: Devices GPS des utilisateurs avec infos véhicule
- **DeviceCommand**: Commandes envoyées aux devices (localisation, redémarrage, etc.)
- **DeviceSettings**: Configuration avancée (APN, capteurs, intervalles)

#### Fonctionnalités:
- CRUD complet des devices
- Association aux véhicules (plaque, marque, modèle, couleur)
- Envoi de commandes aux trackers
- Gestion des groupes (flotte)
- Statut en ligne/hors ligne

---

### 4. **tracking** - Suivi GPS et historique

#### Modèles:
- **GPSPosition**: Positions GPS reçues (lat, lng, vitesse, cap, capteurs)
- **Trip**: Trajets détectés automatiquement
- **Stop**: Arrêts pendant les trajets
- **Geofence**: Zones géographiques (cercle, polygone, rectangle)
- **GeofenceEvent**: Événements d'entrée/sortie de zone
- **Report**: Rapports générés (journalier, hebdomadaire, trajets, carburant)

#### Fonctionnalités:
- **Ingestion GPS** via endpoint REST (/api/track/ingest/)
- **Tracking temps réel** via WebSockets
- Détection automatique des trajets et arrêts
- Géofencing avec alertes
- Génération de rapports (PDF/Excel)
- Historique complet avec filtres

#### WebSocket Consumers:
- **DeviceTrackingConsumer**: Tracking d'un device spécifique
- **UserTrackingConsumer**: Tracking de tous les devices d'un utilisateur
- **AlertConsumer**: Alertes en temps réel

---

### 5. **alerts** - Système d'alertes

#### Modèles:
- **AlertRule**: Règles d'alerte configurables par type
- **Alert**: Alertes déclenchées
- **NotificationLog**: Journal des notifications envoyées
- **MaintenanceReminder**: Rappels de maintenance

#### Types d'alertes supportés:
- ✅ Excès de vitesse
- ✅ Entrée/sortie de géofence
- ✅ Contact allumé/éteint
- ✅ Batterie faible
- ✅ Coupure alimentation
- ✅ Remorquage (mouvement sans contact)
- ✅ Bouton SOS
- ✅ Accélération/freinage brusque
- ✅ Ralenti prolongé
- ✅ Device hors ligne
- ✅ Chute de carburant
- ✅ Température anormale

#### Canaux de notification:
- 📧 Email
- 📱 SMS
- 🔔 Push notifications
- 🔗 Webhook

#### Fonctionnalités:
- Règles avec conditions personnalisables
- Anti-spam avec cooldown configurable
- Horaires d'activité
- Destinataires multiples
- Rappels de maintenance automatiques

---

### 6. **fleet** - Gestion de flotte

#### Modèles:
- **DeviceGroup**: Groupes hiérarchiques de devices
- **Driver**: Conducteurs avec permis
- **DriverAssignment**: Assignation conducteurs↔véhicules
- **FuelEntry**: Entrées de carburant avec calcul de consommation
- **MaintenanceRecord**: Historique de maintenance
- **FleetStatistics**: Statistiques agrégées quotidiennes

#### Fonctionnalités:
- Organisation hiérarchique des flottes
- Gestion des conducteurs (RFID/iButton)
- Suivi carburant avec analyse de consommation
- Historique de maintenance complet
- Statistiques de flotte (distance, carburant, alertes)

---

## 🔌 API Endpoints (À créer)

### Authentication
```
POST   /api/auth/register/          # Inscription
POST   /api/auth/login/             # Connexion (JWT)
POST   /api/auth/refresh/           # Refresh token
POST   /api/auth/logout/            # Déconnexion
POST   /api/auth/reset-password/    # Réinitialisation mot de passe
```

### Devices
```
GET    /api/devices/                # Liste des devices
POST   /api/devices/                # Créer un device
GET    /api/devices/{id}/           # Détails d'un device
PUT    /api/devices/{id}/           # Modifier un device
DELETE /api/devices/{id}/           # Supprimer un device
POST   /api/devices/{id}/command/   # Envoyer une commande
GET    /api/devices/{id}/position/  # Dernière position
```

### Tracking
```
POST   /api/track/ingest/              # Ingestion GPS (depuis Go service)
GET    /api/track/positions/           # Historique positions
GET    /api/track/trips/               # Liste des trajets
GET    /api/track/trips/{id}/          # Détails d'un trajet
POST   /api/track/geofences/           # Créer une géofence
GET    /api/track/geofences/           # Liste des géofences
POST   /api/track/reports/generate/    # Générer un rapport
GET    /api/track/reports/             # Liste des rapports
```

### Alerts
```
GET    /api/alerts/                 # Liste des alertes
GET    /api/alerts/rules/           # Règles d'alerte
POST   /api/alerts/rules/           # Créer une règle
PUT    /api/alerts/rules/{id}/      # Modifier une règle
POST   /api/alerts/{id}/acknowledge # Acquitter une alerte
POST   /api/alerts/{id}/resolve     # Résoudre une alerte
```

### Fleet
```
GET    /api/fleet/groups/           # Groupes de devices
POST   /api/fleet/groups/           # Créer un groupe
GET    /api/fleet/drivers/          # Liste des conducteurs
POST   /api/fleet/drivers/          # Ajouter un conducteur
POST   /api/fleet/fuel/             # Ajouter une entrée carburant
GET    /api/fleet/fuel/             # Historique carburant
POST   /api/fleet/maintenance/      # Ajouter une maintenance
GET    /api/fleet/statistics/       # Statistiques de flotte
```

### Billing
```
GET    /api/billing/packages/       # Packages disponibles
POST   /api/billing/subscribe/      # S'abonner à un package
GET    /api/billing/subscription/   # Abonnement actuel
POST   /api/billing/payment/        # Effectuer un paiement
GET    /api/billing/invoices/       # Liste des factures
GET    /api/billing/invoices/{id}/  # Télécharger une facture
```

### Admin
```
GET    /api/admin/users/            # Gestion utilisateurs
POST   /api/admin/users/            # Créer un utilisateur
GET    /api/admin/packages/         # Gestion packages
POST   /api/admin/packages/         # Créer un package
GET    /api/admin/statistics/       # Statistiques globales
```

---

## 🔄 WebSocket Endpoints

### Tracking en temps réel
```
ws://domain/ws/tracking/{device_id}/     # Tracking d'un device spécifique
ws://domain/ws/tracking/user/            # Tous les devices de l'utilisateur
```

**Messages envoyés au client:**
```json
{
  "type": "position_update",
  "data": {
    "device_id": 123,
    "device_name": "Véhicule 1",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "speed": 65.5,
    "heading": 180.0,
    "timestamp": "2026-01-19T15:00:00Z",
    "is_online": true
  }
}
```

### Alertes en temps réel
```
ws://domain/ws/alerts/                   # Alertes de l'utilisateur
```

**Messages envoyés au client:**
```json
{
  "type": "new_alert",
  "data": {
    "id": 456,
    "title": "Excès de vitesse",
    "message": "Le véhicule roule à 135 km/h",
    "severity": "critical",
    "device_id": 123,
    "device_name": "Véhicule 1",
    "triggered_at": "2026-01-19T15:00:00Z"
  }
}
```

---

## 🔐 Authentification & Permissions

### JWT Authentication
- **Access Token**: 1 heure
- **Refresh Token**: 7 jours
- Rotation automatique des tokens
- Blacklist après rotation

### Permissions
- **Propriétaire**: Accès complet à ses devices
- **Sous-compte**: Permissions granulaires par device
  - `view`: Voir les infos
  - `track`: Suivre en temps réel
  - `history`: Voir l'historique
  - `reports`: Générer des rapports
  - `alerts`: Gérer les alertes
  - `edit`: Modifier les paramètres
- **Admin**: Accès global

---

## 📊 Flux de données

### 1. Ingestion GPS (Service Go → Django)
```
GPS Tracker → Service Go → HTTP POST → Django API
                                     → Enregistrement en DB
                                     → WebSocket Broadcast
                                     → Traitement alertes
```

### 2. Tracking temps réel (Frontend ← Django)
```
Frontend → WebSocket Connect → Django Channels
                             → Authentification
                             → Join Group
                             ← Position initiale
                             ← Mises à jour temps réel
```

### 3. Alertes
```
Position GPS → Vérification règles → Alerte déclenchée
                                   → Enregistrement DB
                                   → WebSocket Broadcast
                                   → Notifications (Email/SMS/Push/Webhook)
```

---

## 🗄️ Base de données

### PostgreSQL (Recommandé)
- Support des requêtes complexes
- PostGIS pour fonctions géospatiales
- Partitionnement pour positions GPS
- Indexation optimisée

### Redis (Requis pour Channels)
- Channel layer pour WebSockets
- Cache pour sessions
- Queue pour tâches asynchrones

---

## 🚀 Déploiement

### Requirements
```bash
Django==6.0.1
djangorestframework==3.16.1
djangorestframework-simplejwt
daphne
channels
channels-redis
django-cors-headers
django-redis
psycopg2-binary
Pillow
requests
```

### Services requis
- ✅ PostgreSQL
- ✅ Redis
- ✅ Service d'ingestion Go (déjà créé)
- ⚙️ Celery (optionnel, pour tâches asynchrones)
- ⚙️ Nginx (reverse proxy)

### Configuration
1. Variables d'environnement (.env):
```bash
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=navic.cg,www.navic.cg

DB_NAME=navic_db
DB_USER=navic_user
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

INGESTION_HOST=localhost
INGESTION_COMMAND_PORT=8080

CORS_ALLOWED_ORIGINS=https://app.navic.cg

SMS_API_URL=https://sms-provider.com/api/send
SMS_API_KEY=...
```

2. Migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Créer un superuser:
```bash
python manage.py createsuperuser
```

4. Collecter les fichiers statiques:
```bash
python manage.py collectstatic
```

5. Lancer les services:
```bash
# Django avec Daphne (ASGI)
daphne -b 0.0.0.0 -p 8000 navic.asgi:application

# Ou avec Gunicorn + Uvicorn workers
gunicorn navic.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## 📝 Prochaines étapes

1. **Créer les serializers** pour chaque modèle
2. **Créer les ViewSets** pour les API REST
3. **Configurer le routing** URL
4. **Créer les tests** unitaires et d'intégration
5. **Documenter l'API** avec Swagger/OpenAPI
6. **Implémenter Celery** pour tâches asynchrones
7. **Mettre en place CI/CD**
8. **Configurer le monitoring** (Sentry, Prometheus)

---

## 🔧 Commandes utiles

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer des données de test
python manage.py shell
>>> from billing.models import BillingPackage
>>> BillingPackage.objects.create(
...     name="Gratuit",
...     package_type="free",
...     max_devices=1,
...     max_sub_accounts=0,
...     history_days=7
... )

# Lancer le serveur de développement
python manage.py runserver

# Tester les WebSockets
python manage.py runserver
# Puis se connecter avec un client WebSocket
```

---

## 📚 Documentation technique

### Modèles de données
- 6 applications Django
- 30+ modèles
- Relations complexes avec ForeignKey, ManyToMany
- Indexation optimisée pour performances

### Technologies utilisées
- **Backend**: Django 6.0.1
- **API**: Django REST Framework
- **WebSockets**: Django Channels + Redis
- **Auth**: Simple JWT
- **Database**: PostgreSQL
- **Cache**: Redis
- **Storage**: Stockage local/S3 pour fichiers

### Performance
- Indexation DB pour requêtes fréquentes
- Pagination pour listes
- Cache Redis pour données récurrentes
- Partitionnement potentiel pour positions GPS
- Compression WebSocket

---

## 📞 Support & Contact

Pour toute question sur l'architecture ou l'implémentation, consulter la documentation Django:
- https://docs.djangoproject.com/
- https://www.django-rest-framework.org/
- https://channels.readthedocs.io/

---

**Date de création**: 19 janvier 2026
**Version**: 1.0
**Statut**: Architecture complète - Prêt pour implémentation des endpoints
