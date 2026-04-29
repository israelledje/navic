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

# Exposer le port
EXPOSE 8000

# Démarrer avec Daphne pour supporter les WebSockets
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "navic.asgi:application"]
