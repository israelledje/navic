#!/bin/bash
set -e

echo "=========================================="
echo "  NAVIC Backend - Entrypoint"
echo "=========================================="

# --- Attendre que la base de données soit prête ---
echo "[1/4] Attente de la base de données..."
MAX_RETRIES=30
RETRY_COUNT=0
until python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='${DB_NAME}',
        user='${DB_USER}',
        password='${DB_PASSWORD}',
        host='${DB_HOST}',
        port='${DB_PORT}'
    )
    conn.close()
    print('DB ready!')
except Exception as e:
    print(f'DB not ready: {e}')
    exit(1)
" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERREUR: La base de données n'est pas disponible après ${MAX_RETRIES} tentatives."
        exit 1
    fi
    echo "  Tentative $RETRY_COUNT/$MAX_RETRIES - DB pas encore prête, attente 2s..."
    sleep 2
done
echo "  ✓ Base de données prête!"

# --- Appliquer les migrations ---
echo "[2/4] Application des migrations..."
python manage.py migrate --noinput
echo "  ✓ Migrations appliquées!"

# --- Collecter les fichiers statiques ---
echo "[3/4] Collecte des fichiers statiques..."
python manage.py collectstatic --noinput 2>/dev/null || echo "  (collectstatic ignoré)"
echo "  ✓ Fichiers statiques collectés!"

# --- Créer le superuser par défaut ---
echo "[4/4] Vérification du superuser..."
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'navic.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'support@dis-network.net')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@2026')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f'  ✓ Superuser créé: {email}')
else:
    print(f'  ✓ Superuser existe déjà: {email}')
"

echo "=========================================="
echo "  Initialisation terminée!"
echo "=========================================="

# --- Lancer la commande passée en argument ---
exec "$@"
