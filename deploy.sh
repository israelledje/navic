#!/bin/bash
# Script de déploiement automatisé pour Navic V2 sur VPS
# Utilisation : chmod +x deploy.sh && ./deploy.sh

echo "🚀 Début du déploiement de Navic V2..."

# 1. Mise à jour du code (optionnel, décommenter si vous utilisez Git sur le VPS)
# echo "📥 Récupération des dernières mises à jour Git..."
# git pull origin main

# 2. Reconstruction des images et démarrage des conteneurs
# L'option --build s'assure que le frontend et le backend sont recompilés si le code a changé
echo "🐳 Construction et démarrage des conteneurs Docker..."
docker-compose up -d --build

# 3. Application des migrations de base de données (PostgreSQL)
echo "🗄️ Application des migrations Django..."
# -T est utilisé pour éviter les erreurs "the input device is not a TTY" dans certains terminaux/CI
docker-compose exec -T backend python manage.py migrate

# 4. Collecte des fichiers statiques (Essentiel pour que l'interface admin Django s'affiche bien)
echo "📁 Collecte des fichiers statiques Django..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# 5. Création optionnelle d'un compte superadmin par défaut s'il n'existe pas
# echo "👤 Création du compte super-administrateur (admin/admin)..."
# docker-compose exec -T backend python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@navic.cg', 'admin')"

echo "✅ Déploiement terminé avec succès !"
echo "🌐 L'interface utilisateur est accessible sur le port 80."
echo "📡 Les ports d'ingestion GPS (5027-5038) sont prêts à recevoir des données."
