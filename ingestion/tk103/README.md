# Package TK103

Package de décodage pour le protocole GPS TK103.

## Structure

- **types.go** : Types de base (`Packet`, `DeviceEvent`)
- **decoder.go** : Fonctions utilitaires de décodage (BCD, temps, coordonnées)
- **packets.go** : Décodage des différents types de paquets (Login, GPS, Alarm)
- **router.go** : Décodage de la trame complète avec validation CRC
- **crc.go** : Calcul du CRC X25 pour validation
- **alarms.go** : Mapping des codes d'alarme vers leurs noms

## Types de Paquets Supportés

### LOGIN (0x01)
Paquet d'authentification contenant l'IMEI de la balise.

### GPS (0x12 / 0x1A)
Paquet de données GPS contenant :
- Timestamp
- Latitude
- Longitude
- Vitesse

### ALARM (0x26)
Paquet d'alarme contenant :
- Code d'alarme
- Timestamp
- Nom de l'alarme

## Format de Trame

```
[0x78][0x78][length][protocol][payload...][CRC_HI][CRC_LO][0x0D][0x0A]
```

- **Header** : 0x78 0x78 (fixe)
- **Length** : Longueur du payload
- **Protocol** : Type de paquet (0x01, 0x12, 0x1A, 0x26, etc.)
- **Payload** : Données selon le type de paquet
- **CRC** : Checksum X25 sur [length][protocol][payload]
- **Tail** : 0x0D 0x0A (CRLF)

## Utilisation

```go
import "navic/ingestion/tk103"

// Décoder une trame
packet, err := tk103.DecodeFrame(data)
if err != nil {
    // Gérer l'erreur
}

// Décoder selon le type
switch packet.Protocol {
case 0x01:
    imei := tk103.DecodeLogin(packet)
case 0x12, 0x1A:
    event := tk103.DecodeGPS(packet)
case 0x26:
    event := tk103.DecodeAlarm(packet)
}
```