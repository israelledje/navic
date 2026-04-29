# Package GT06

Package de décodage pour le protocole GPS GT06 (version 1.8.1).

## Structure

- **types.go** : Types de base (`Packet`, `DeviceEvent`)
- **decoder.go** : Fonctions utilitaires de décodage (BCD, temps, coordonnées, vitesse, cap)
- **packets.go** : Décodage des différents types de paquets (Login, GPS, Alarm, Status)
- **router.go** : Décodage de la trame complète avec validation CRC
- **crc.go** : Calcul du CRC-16 pour validation
- **alarms.go** : Mapping des codes d'alarme vers leurs noms

## Types de Paquets Supportés

### LOGIN (0x01)
Paquet d'authentification contenant l'IMEI de la balise en format BCD.

### GPS (0x12)
Paquet de données GPS contenant :
- Timestamp
- Latitude/Longitude
- Vitesse
- Cap
- Informations de status (batterie, signal)
- Informations LBS (optionnelles)

### ALARM (0x16)
Paquet d'alarme contenant les mêmes données que GPS avec des flags d'alarme.

### STATUS (0x13)
Paquet d'information de status du terminal.

## Format de Trame

```
[0x78/0x79][0x78/0x79][length][protocol][payload...][serial_HI][serial_LO][CRC_HI][CRC_LO][0x0D][0x0A]
```

- **Header** : 0x78 0x78 ou 0x79 0x79 (fixe)
- **Length** : Longueur du payload
- **Protocol** : Type de paquet (0x01, 0x12, 0x13, 0x16, etc.)
- **Payload** : Données selon le type de paquet
- **Serial** : Numéro de séquence (2 bytes)
- **CRC** : Checksum CRC-16 sur [length][protocol][payload][serial]
- **Tail** : 0x0D 0x0A (CRLF)

## Utilisation

```go
import "navic/ingestion/gt06"

// Décoder une trame
packet, err := gt06.DecodeFrame(data)
if err != nil {
    // Gérer l'erreur
}

// Décoder selon le type
switch packet.Protocol {
case 0x01:
    imei := gt06.DecodeLogin(packet)
case 0x12:
    event := gt06.DecodeGPS(packet)
case 0x16:
    event := gt06.DecodeAlarm(packet)
case 0x13:
    event := gt06.DecodeStatus(packet)
}
```