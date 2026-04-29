# Configuration des Variables d'Environnement

## Fichiers d'exemple

- **`env.example`** : Fichier d'exemple avec toutes les variables
- **`ENV_EXAMPLE.md`** : Documentation détaillée des variables

## Utilisation

### Option 1 : Variables d'environnement système (recommandé)

Le service Go lit directement les variables d'environnement du système.

#### Windows PowerShell
```powershell
$env:DJANGO_URL="http://localhost:8000/api/track/ingest/"
$env:COMMAND_PORT="8080"
$env:GT06_ENABLED="true"
.\main_ingestion.exe
```

#### Linux/Mac
```bash
export DJANGO_URL=http://localhost:8000/api/track/ingest/
export COMMAND_PORT=8080
export GT06_ENABLED=true
./main_ingestion
```

### Option 2 : Fichier .env avec godotenv

Si vous préférez utiliser un fichier `.env`, ajoutez le package `godotenv` :

1. Ajouter au `go.mod` :
```bash
go get github.com/joho/godotenv
```

2. Modifier `main_ingestion.go` :
```go
import "github.com/joho/godotenv"

func main() {
    // Charger le fichier .env
    godotenv.Load()
    
    // ... reste du code
}
```

3. Créer un fichier `.env` à partir de `env.example`

## Variables Requises (Minimum)

Pour un fonctionnement de base, seules ces variables sont nécessaires :

```bash
DJANGO_URL=http://localhost:8000/api/track/ingest/
COMMAND_PORT=8080
```

Toutes les autres variables ont des valeurs par défaut.

## Variables par Catégorie

### Obligatoires
- `DJANGO_URL` : URL de l'API Django

### Optionnelles mais Recommandées
- `COMMAND_PORT` : Port du serveur de commandes
- `RATE_LIMIT_PER_IP` : Protection contre les abus
- `RATE_LIMIT_PER_IMEI` : Protection par IMEI

### Configuration Protocoles
Toutes les variables `*_TCP_PORT`, `*_UDP_PORT`, `*_ENABLED` sont optionnelles.
Par défaut, tous les protocoles sont activés sur les ports standards.

## Production

Pour la production, configurez :

```bash
# Sécurité renforcée
RATE_LIMIT_PER_IP=50
RATE_LIMIT_PER_IMEI=100
MAX_CONNECTIONS=500
BLOCK_DURATION=600

# Logging
LOG_LEVEL=WARN
LOG_FILE=/var/log/navic/ingestion.log

# Désactiver les protocoles non utilisés
TK102_ENABLED=false
303_ENABLED=false
```