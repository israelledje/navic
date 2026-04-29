# Service d'Ingestion GPS Navic

Service d'ingestion en Go pour recevoir et décoder les trames GPS de différentes balises sur le marché.

## Architecture

Le service est organisé de manière modulaire :

- **config.go** : Configuration centralisée avec ports dédiés par protocole
- **decoders.go** : Décodeurs pour chaque protocole (GT06, GT06N, TK102, TK103, 303, TELTONIKA)
- **security.go** : Système de sécurité (rate limiting, validation, protection DoS)
- **server.go** : Serveurs TCP/UDP par protocole
- **main_ingestion.go** : Point d'entrée principal

## Protocoles Supportés

Chaque protocole écoute sur ses propres ports :

| Protocole | Port TCP | Port UDP | Statut |
|-----------|----------|----------|--------|
| GT06      | 5027     | 5028     | ✅     |
| GT06N     | 5029     | 5030     | ✅     |
| TK102     | 5031     | 5032     | ✅     |
| TK103     | 5033     | 5034     | ✅     |
| 303       | 5035     | 5036     | ✅     |
| TELTONIKA | 5037     | 5038     | ✅     |

## Sécurités Implémentées

### 1. Rate Limiting
- **Par IP** : Limite le nombre de requêtes par minute par adresse IP
- **Par IMEI** : Limite le nombre de requêtes par minute par IMEI
- **Blocage automatique** : Les IPs/IMEIs qui dépassent les limites sont bloqués temporairement

### 2. Validation des Données
- Validation de la taille des paquets (max configurable)
- Validation du format IMEI (15 chiffres)
- Validation des protocoles

### 3. Protection DoS
- Limitation du nombre de connexions simultanées
- Timeouts configurables par protocole
- Nettoyage automatique des connexions inactives

### 4. Journalisation
- Logs détaillés de toutes les connexions
- Logs des tentatives suspectes
- Logs des erreurs de décodage

## Configuration

### Variables d'Environnement

#### Configuration Django
- `DJANGO_URL` : URL de l'API Django (défaut: `http://localhost:8000/api/track/ingest/`)

#### Configuration Sécurité
- `RATE_LIMIT_PER_IP` : Nombre max de requêtes/min par IP (défaut: 100)
- `RATE_LIMIT_PER_IMEI` : Nombre max de requêtes/min par IMEI (défaut: 200)
- `MAX_CONNECTIONS` : Nombre max de connexions simultanées (défaut: 1000)
- `MAX_PACKET_SIZE` : Taille max d'un paquet en bytes (défaut: 4096)
- `ENABLE_IMEI_WHITELIST` : Activer la whitelist IMEI (défaut: true)
- `BLOCK_DURATION` : Durée de blocage en secondes (défaut: 300 = 5 min)

#### Configuration Protocoles
Chaque protocole peut être configuré individuellement :

**GT06:**
- `GT06_TCP_PORT` : Port TCP (défaut: 5027)
- `GT06_UDP_PORT` : Port UDP (défaut: 5028)
- `GT06_ENABLED` : Activer/désactiver (défaut: true)

**GT06N:**
- `GT06N_TCP_PORT` : Port TCP (défaut: 5029)
- `GT06N_UDP_PORT` : Port UDP (défaut: 5030)
- `GT06N_ENABLED` : Activer/désactiver (défaut: true)

**TK102:**
- `TK102_TCP_PORT` : Port TCP (défaut: 5031)
- `TK102_UDP_PORT` : Port UDP (défaut: 5032)
- `TK102_ENABLED` : Activer/désactiver (défaut: true)

**TK103:**
- `TK103_TCP_PORT` : Port TCP (défaut: 5033)
- `TK103_UDP_PORT` : Port UDP (défaut: 5034)
- `TK103_ENABLED` : Activer/désactiver (défaut: true)

**303:**
- `303_TCP_PORT` : Port TCP (défaut: 5035)
- `303_UDP_PORT` : Port UDP (défaut: 5036)
- `303_ENABLED` : Activer/désactiver (défaut: true)

**TELTONIKA:**
- `TELTONIKA_TCP_PORT` : Port TCP (défaut: 5037)
- `TELTONIKA_UDP_PORT` : Port UDP (défaut: 5038)
- `TELTONIKA_ENABLED` : Activer/désactiver (défaut: true)

#### Configuration Logging
- `LOG_LEVEL` : Niveau de log (défaut: INFO)
- `LOG_FILE` : Fichier de log (défaut: stdout)

## Compilation et Exécution

### Compilation
```bash
cd ingestion
go build -o main_ingestion.exe main_ingestion.go
```

### Exécution
```bash
# Avec variables d'environnement
export DJANGO_URL=http://localhost:8000/api/track/ingest/
export RATE_LIMIT_PER_IP=100
./main_ingestion.exe

# Ou directement
DJANGO_URL=http://localhost:8000/api/track/ingest/ ./main_ingestion.exe
```

### Exécution Windows
```powershell
$env:DJANGO_URL="http://localhost:8000/api/track/ingest/"
$env:RATE_LIMIT_PER_IP=100
.\main_ingestion.exe
```

## Format des Messages Envoyés à Django

Le service envoie des messages JSON au format suivant :

```json
{
  "imei": "123456789012345",
  "protocol": "GT06",
  "timestamp": "2024-01-01T12:00:00Z",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "speed": 60.5,
  "heading": 180.0,
  "altitude": 100.0,
  "satellites": 8,
  "battery": 85,
  "signal": 75,
  "alerts": ["SOS", "LOW_BATTERY"],
  "raw_data": "78780d010123456789012345...",
  "other_data": {}
}
```

## Ajout d'un Nouveau Protocole

Pour ajouter un nouveau protocole :

1. Créer un nouveau décodeur dans `decoders.go` implémentant l'interface `Decoder`
2. Ajouter la configuration dans `config.go` avec les ports dédiés
3. Enregistrer le décodeur dans la fonction `GetDecoder()`

Exemple :
```go
type MonProtocoleDecoder struct{}

func (d *MonProtocoleDecoder) GetProtocolName() string {
    return "MON_PROTOCOLE"
}

func (d *MonProtocoleDecoder) Validate(data []byte) bool {
    // Logique de validation
}

func (d *MonProtocoleDecoder) Decode(data []byte) (*GPSMessage, error) {
    // Logique de décodage
}
```

## Sécurité en Production

Pour un déploiement en production :

1. **Firewall** : Limiter l'accès aux ports uniquement aux IPs autorisées
2. **Rate Limiting** : Ajuster les limites selon votre charge
3. **Monitoring** : Surveiller les logs pour détecter les attaques
4. **HTTPS** : Utiliser HTTPS pour la communication avec Django
5. **Authentification** : Ajouter une authentification API si nécessaire
6. **Backup** : Sauvegarder régulièrement les configurations

## Dépannage

### Le service ne démarre pas
- Vérifier que les ports ne sont pas déjà utilisés
- Vérifier les permissions (ports < 1024 nécessitent root/admin)
- Vérifier les logs pour les erreurs

### Les messages ne sont pas envoyés à Django
- Vérifier que Django est démarré et accessible
- Vérifier l'URL Django dans la configuration
- Vérifier les logs pour les erreurs HTTP

### Rate limiting trop strict
- Augmenter `RATE_LIMIT_PER_IP` et `RATE_LIMIT_PER_IMEI`
- Vérifier les logs pour identifier les IPs/IMEIs bloqués