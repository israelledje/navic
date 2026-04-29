FROM golang:1.21-alpine AS builder

# Dossier de travail
WORKDIR /app

# Copier les fichiers go
COPY go.mod ./
# Si vous avez un go.sum, décommentez la ligne suivante
# COPY go.sum ./
RUN go mod download

# Copier le code source
COPY . .

# Compiler l'application
RUN CGO_ENABLED=0 GOOS=linux go build -o ingestion_service main_ingestion.go

# Image finale allégée
FROM alpine:latest
WORKDIR /app

# Récupérer l'exécutable compilé
COPY --from=builder /app/ingestion_service .
# Copier le fichier d'exemple env si besoin
COPY env.example .env

# Exposer les ports de tous les protocoles prévus
EXPOSE 5027-5038
EXPOSE 5027-5038/udp

# Démarrer le service
CMD ["./ingestion_service"]
