FROM python:3.12-slim

# Définir le dossier de travail
WORKDIR /app

# Installer les dépendances système pour PostgreSQL, etc.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Rendre le script d'entrypoint exécutable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exposer le port
EXPOSE 8000

# Entrypoint: migrations, collectstatic, superuser, puis lancement
ENTRYPOINT ["/entrypoint.sh"]

# Commande par défaut: Daphne (ASGI)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "navic.asgi:application"]
