# Variables d'Environnement - Service d'Ingestion GPS Navic

Copiez ce fichier en `.env` et configurez les valeurs selon votre environnement.

## Configuration Django

```bash
# URL de l'API Django pour recevoir les données GPS décodées
DJANGO_URL=http://localhost:8000/api/track/ingest/
```

## Configuration Sécurité

```bash
# Nombre maximum de requêtes par minute par adresse IP
RATE_LIMIT_PER_IP=100

# Nombre maximum de requêtes par minute par IMEI
RATE_LIMIT_PER_IMEI=200

# Nombre maximum de connexions simultanées
MAX_CONNECTIONS=1000

# Taille maximum d'un paquet en bytes
MAX_PACKET_SIZE=4096

# Activer la whitelist IMEI (true/false)
ENABLE_IMEI_WHITELIST=true

# Durée de blocage en secondes après dépassement de limite (défaut: 300 = 5 minutes)
BLOCK_DURATION=300
```

## Configuration Serveur de Commandes

```bash
# Port du serveur HTTP pour recevoir les commandes depuis Django
COMMAND_PORT=8080
```

## Configuration Protocole GT06

```bash
GT06_TCP_PORT=5027
GT06_UDP_PORT=5028
GT06_ENABLED=true
```

## Configuration Protocole GT06N

```bash
GT06N_TCP_PORT=5029
GT06N_UDP_PORT=5030
GT06N_ENABLED=true
```

## Configuration Protocole TK102

```bash
TK102_TCP_PORT=5031
TK102_UDP_PORT=5032
TK102_ENABLED=true
```

## Configuration Protocole TK103

```bash
TK103_TCP_PORT=5033
TK103_UDP_PORT=5034
TK103_ENABLED=true
```

## Configuration Protocole 303

```bash
303_TCP_PORT=5035
303_UDP_PORT=5036
303_ENABLED=true
```

## Configuration Protocole FMXXXX/TELTONIKA

```bash
FMXXXX_TCP_PORT=5039
FMXXXX_UDP_PORT=5040
FMXXXX_ENABLED=true
```

## Configuration Logging

```bash
# Niveau de log (DEBUG, INFO, WARN, ERROR)
LOG_LEVEL=INFO

# Fichier de log (laisser vide pour stdout)
LOG_FILE=
```

## Exemple de fichier .env complet

```bash
# ============================================
# Configuration Service d'Ingestion GPS Navic
# ============================================

# Configuration Django
DJANGO_URL=http://localhost:8000/api/track/ingest/

# Configuration Sécurité
RATE_LIMIT_PER_IP=100
RATE_LIMIT_PER_IMEI=200
MAX_CONNECTIONS=1000
MAX_PACKET_SIZE=4096
ENABLE_IMEI_WHITELIST=true
BLOCK_DURATION=300

# Configuration Serveur de Commandes
COMMAND_PORT=8080

# Configuration Protocoles
GT06_TCP_PORT=5027
GT06_UDP_PORT=5028
GT06_ENABLED=true

GT06N_TCP_PORT=5029
GT06N_UDP_PORT=5030
GT06N_ENABLED=true

TK102_TCP_PORT=5031
TK102_UDP_PORT=5032
TK102_ENABLED=true

TK103_TCP_PORT=5033
TK103_UDP_PORT=5034
TK103_ENABLED=true

303_TCP_PORT=5035
303_UDP_PORT=5036
303_ENABLED=true

FMXXXX_TCP_PORT=5039
FMXXXX_UDP_PORT=5040
FMXXXX_ENABLED=true

# Configuration Logging
LOG_LEVEL=INFO
LOG_FILE=
```

## Notes importantes

- Les ports TCP/UDP doivent être disponibles et non utilisés par d'autres services
- Les ports < 1024 nécessitent des privilèges root/admin sous Linux/Mac
- Pour désactiver un protocole, mettre `*_ENABLED=false`
- Pour la production, utiliser des valeurs plus restrictives pour la sécurité
- Le service Go lit directement les variables d'environnement du système
- Pour Windows PowerShell : `$env:VARIABLE_NAME="value"`
- Pour Linux/Mac : `export VARIABLE_NAME="value"`

## Utilisation

### Windows PowerShell
```powershell
# Charger depuis un fichier .env (nécessite un script)
$env:DJANGO_URL="http://localhost:8000/api/track/ingest/"
$env:COMMAND_PORT="8080"
$env:GT06_ENABLED="true"
.\main_ingestion.exe
```

### Linux/Mac
```bash
# Charger depuis un fichier .env
export $(cat .env | xargs)
./main_ingestion

# Ou directement
export DJANGO_URL=http://localhost:8000/api/track/ingest/
export COMMAND_PORT=8080
./main_ingestion
```

### Avec un fichier .env (nécessite un package Go comme godotenv)
Si vous souhaitez utiliser un fichier `.env`, vous devrez ajouter le package `github.com/joho/godotenv` :

```go
import "github.com/joho/godotenv"

func main() {
    godotenv.Load() // Charge le fichier .env
    // ... reste du code
}
```