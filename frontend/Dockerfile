# Étape 1 : Build de l'application Vite
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

# Copier le reste du code source
COPY . .
# Construire l'application pour la production (crée le dossier dist)
RUN npm run build

# Étape 2 : Serveur web Nginx (Reverse Proxy)
FROM nginx:alpine

# Copier les fichiers statiques générés par Vite
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier notre propre configuration Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
