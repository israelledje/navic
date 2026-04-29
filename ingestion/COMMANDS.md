# Système de Commandes GPS

Le service d'ingestion permet d'envoyer des commandes aux balises GPS connectées via TCP.

## Architecture

- **ConnectionManager** : Gère les connexions TCP actives par IMEI et protocole
- **CommandSender** : Envoie les commandes aux balises
- **Command Server** : Serveur HTTP pour recevoir les commandes depuis Django
- **Packages de commandes** : Encodage spécifique pour chaque protocole

## Protocoles Supportés

### GT06 / GT06N

Commandes disponibles :
- `cut_engine` : Coupure moteur
- `restore_engine` : Restauration moteur
- `set_output` : Activer une sortie (param: `output` - numéro de sortie)
- `clear_output` : Désactiver une sortie (param: `output` - numéro de sortie)
- `request_gps` : Demander une position GPS
- `set_interval` : Définir l'intervalle de rapport (param: `interval` - en secondes)
- `set_speed_limit` : Définir la limite de vitesse (param: `speed` - en km/h)
- `set_geofence` : Définir une géofence (params: `latitude`, `longitude`, `radius`)

### TK102 / TK103

Commandes disponibles :
- `CUTENGINE` : Coupure moteur
- `RESTOREENGINE` : Restauration moteur
- `SETOUTPUT` : Activer une sortie (param: `output` - numéro de sortie)
- `CLEAROUTPUT` : Désactiver une sortie (param: `output` - numéro de sortie)
- `REQUESTGPS` : Demander une position GPS
- `SETINTERVAL` : Définir l'intervalle (param: `interval` - en secondes)

### FMXXXX / TELTONIKA

Commandes disponibles :
- `get_status` : Obtenir le status de la balise
- `set_io` : Définir une IO (params: `io_id`, `value`)
- `cut_engine` : Coupure moteur
- `restore_engine` : Restauration moteur
- `request_gps` : Demander une position GPS
- `set_interval` : Définir l'intervalle (param: `interval` - en secondes)

## API Django

### Endpoint : `/api/track/command/`

**Méthode** : POST

**Format JSON** :
```json
{
    "protocol": "GT06",
    "imei": "123456789012345",
    "command": "cut_engine",
    "params": {
        "output": 1
    }
}
```

**Réponse succès** :
```json
{
    "success": true,
    "message": "Commande 'cut_engine' envoyée avec succès à 123456789012345 (GT06)"
}
```

**Réponse erreur** :
```json
{
    "success": false,
    "error": "connexion non disponible: aucune connexion active pour IMEI 123456789012345 (protocole GT06)"
}
```

## API Directe (Service Go)

### Endpoint : `http://localhost:8080/api/command`

**Méthode** : POST

Même format JSON que l'API Django.

### Endpoints supplémentaires

- `GET /health` : Vérification de santé
- `GET /api/connections` : Liste des connexions actives (debug)

## Exemples d'utilisation

### Coupure moteur (GT06)
```bash
curl -X POST http://localhost:8000/api/track/command/ \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "GT06",
    "imei": "123456789012345",
    "command": "cut_engine"
  }'
```

### Activer une sortie (TK103)
```bash
curl -X POST http://localhost:8000/api/track/command/ \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "TK103",
    "imei": "123456789012345",
    "command": "SETOUTPUT",
    "params": {
      "output": 1
    }
  }'
```

### Définir une géofence (GT06)
```bash
curl -X POST http://localhost:8000/api/track/command/ \
  -H "Content-Type: application/json" \
  -d '{
    "protocol": "GT06",
    "imei": "123456789012345",
    "command": "set_geofence",
    "params": {
      "latitude": 48.8566,
      "longitude": 2.3522,
      "radius": 1000
    }
  }'
```

## Notes importantes

1. **Connexion requise** : La balise doit être connectée via TCP pour recevoir des commandes
2. **IMEI autorisé** : L'IMEI doit être dans la liste des IMEI autorisés (pour l'API Django)
3. **Timeout** : Les commandes ont un timeout de 5 secondes
4. **Protocole** : Le protocole doit correspondre au protocole utilisé par la balise

## Configuration

Le port du serveur de commandes peut être configuré via la variable d'environnement :
```bash
export COMMAND_PORT=8080
```

Par défaut, le port est 8080.