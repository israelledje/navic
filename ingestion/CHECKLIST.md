# Checklist de Préparation - Service d'Ingestion Navic

## ✅ Composants Principaux

### 1. Architecture Modulaire
- [x] Configuration centralisée (`config.go`)
- [x] Système de sécurité (`security.go`)
- [x] Gestionnaire de connexions (`connection_manager.go`)
- [x] Serveurs par protocole (`server.go`)
- [x] Point d'entrée principal (`main_ingestion.go`)

### 2. Protocoles Supportés
- [x] **GT06** : Package complet avec décodage et commandes
- [x] **GT06N** : Supporté (utilise GT06)
- [x] **TK102** : Package de commandes
- [x] **TK103** : Package complet avec décodage et commandes
- [x] **303** : Décodeur de base
- [x] **FMXXXX/TELTONIKA** : Package complet avec décodage et commandes

### 3. Sécurités Implémentées
- [x] Rate limiting par IP
- [x] Rate limiting par IMEI
- [x] Blocage automatique des abus
- [x] Validation des paquets
- [x] Validation des IMEI
- [x] Limitation des connexions simultanées
- [x] Timeouts configurables
- [x] Nettoyage automatique des connexions

### 4. Système de Commandes
- [x] Gestionnaire de connexions actives par IMEI
- [x] Packages de commandes pour chaque protocole
- [x] Serveur HTTP pour recevoir les commandes
- [x] Envoi individuel à une seule balise
- [x] Support des commandes : cut_engine, restore_engine, set_output, etc.

### 5. Intégration Django
- [x] Endpoint d'ingestion des données GPS
- [x] Endpoint d'envoi de commandes
- [x] Vérification des IMEI autorisés
- [x] Vérification de propriété des balises
- [x] Authentification requise pour les commandes

## 📋 Points à Vérifier Avant Production

### Configuration
- [ ] Vérifier que tous les ports sont disponibles
- [ ] Configurer les variables d'environnement
- [ ] Configurer l'URL Django
- [ ] Ajuster les limites de rate limiting selon la charge

### Base de Données Django
- [ ] Créer les migrations : `python manage.py makemigrations`
- [ ] Appliquer les migrations : `python manage.py migrate`
- [ ] Créer un superutilisateur : `python manage.py createsuperuser`
- [ ] Ajouter des IMEI autorisés dans l'admin Django
- [ ] Assigner des balises aux utilisateurs

### Tests
- [ ] Tester la réception de données GPS
- [ ] Tester l'envoi de commandes
- [ ] Vérifier que les connexions sont bien enregistrées
- [ ] Tester avec plusieurs protocoles simultanément

### Sécurité Production
- [ ] Configurer le firewall pour limiter l'accès aux ports
- [ ] Utiliser HTTPS pour Django
- [ ] Configurer l'authentification API si nécessaire
- [ ] Mettre en place le monitoring et les alertes
- [ ] Configurer les backups de la base de données

## 🚀 Démarrage

### 1. Démarrer Django
```bash
cd navic
python manage.py runserver
```

### 2. Démarrer le Service d'Ingestion
```bash
cd ingestion
go build -o main_ingestion.exe .
./main_ingestion.exe
```

Ou avec variables d'environnement :
```bash
export DJANGO_URL=http://localhost:8000/api/track/ingest/
export COMMAND_PORT=8080
./main_ingestion.exe
```

## 📝 Notes

- Le service écoute sur les ports configurés pour chaque protocole
- Le serveur de commandes écoute sur le port 8080 par défaut
- Les balises doivent être connectées via TCP pour recevoir des commandes
- Les utilisateurs ne peuvent envoyer des commandes qu'à leurs propres balises