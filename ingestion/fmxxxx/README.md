# Package FMXXXX

Package de décodage pour le protocole GPS FMXXXX (Teltonika).

## Structure

- **types.go** : Types de base (`Packet`, `AVLData`, `GPSData`, `IOData`)
- **decoder.go** : Fonctions utilitaires de décodage (timestamp, coordonnées)
- **packets.go** : Décodage des paquets et codecs (8, 12, 16)
- **router.go** : Décodage de la trame complète et validation

## Codecs Supportés

### Codec 8 (0x08, 0x8E)
Format standard avec données GPS et IO.

### Codec 12 (0x0C, 0x8C)
Similaire au codec 8.

### Codec 16 (0x0E, 0x8E)
Format étendu avec plus de champs IO.

## Format de Trame

```
[IMEI_LENGTH][IMEI][CODEC_ID][AVL_DATA_ARRAY]
```

- **IMEI_LENGTH** : Longueur de l'IMEI (1 byte)
- **IMEI** : Identifiant de l'appareil (variable)
- **CODEC_ID** : Identifiant du codec (1 byte)
- **AVL_DATA_ARRAY** : Tableau de données AVL

## Format AVL Data

Chaque élément AVL contient :
- **Timestamp** : 8 bytes (Unix timestamp en millisecondes)
- **Priority** : 1 byte
- **GPS Element** : Longitude, Latitude, Altitude, Angle, Satellites, Speed
- **IO Element** : Données d'entrées/sorties (1, 2, 4, 8 bytes)

## Utilisation

```go
import "navic/ingestion/fmxxxx"

// Décoder une trame
avlDataList, imei, err := fmxxxx.DecodeFrame(data)
if err != nil {
    // Gérer l'erreur
}

// Parcourir les données AVL
for _, avlData := range avlDataList {
    if avlData.GPS != nil {
        // Utiliser les données GPS
        lat := avlData.GPS.Latitude
        lon := avlData.GPS.Longitude
    }
}
```