# 📋 Serializers Navic - Documentation Complète

## Vue d'ensemble

Tous les serializers Django REST Framework ont été créés pour l'ensemble de l'architecture API Navic. Ces serializers gèrent la sérialisation/désérialisation entre les modèles Django et JSON.

---

## 📁 Structure des Serializers

### 1. **accounts/serializers.py** - Gestion Utilisateurs

#### Serializers d'authentification
- **UserRegistrationSerializer**
  - Inscription nouveaux utilisateurs
  - Validation du mot de passe
  - Vérification de la correspondance des mots de passe
  
- **UserSerializer**
  - Informations utilisateur complètes
  - Champs calculés (full_name, is_sub_account, can_create_device)
  - Read-only pour les champs sensibles

- **UserUpdateSerializer**
  - Mise à jour du profil
  - Préférences utilisateur

- **ChangePasswordSerializer**
  - Changement de mot de passe
  - Validation de l'ancien mot de passe

#### Serializers de permissions
- **SubAccountPermissionSerializer**
  - Permissions des sous-comptes
  - Validation des permissions
  - Détails device et sous-compte

- **SubAccountSerializer**
  - Création de sous-comptes
  - Définition automatique du type

#### Activité
- **UserActivitySerializer**
  - Historique des activités
  - Type d'activité avec display

**Total: 7 serializers**

---

### 2. **billing/serializers.py** - Facturation

#### Packages
- **BillingPackageSerializer**
  - Packages complets avec toutes les features
  
- **BillingPackageListSerializer**
  - Version simplifiée pour les listes

#### Abonnements
- **SubscriptionSerializer**
  - Abonnements avec détails package
  - Statut et dates
  
- **SubscriptionCreateSerializer**
  - Création d'abonnement
  - Calcul automatique des dates et montants

- **SubscriptionCancelSerializer**
  - Annulation d'abonnement
  - Motif d'annulation

#### Paiements
- **PaymentSerializer**
  - Paiements avec détails
  
- **PaymentCreateSerializer**
  - Création de paiement
  - Génération transaction_id

#### Factures
- **InvoiceSerializer**
  - Factures complètes
  
- **InvoiceCreateSerializer**
  - Création de facture
  - Calcul TVA et total automatique
  - Génération numéro de facture

**Total: 9 serializers**

---

### 3. **devices/serializers.py** - Devices GPS

#### Modèles de devices
- **DeviceModelSerializer**
  - Modèles de trackers GPS
  - Protocoles supportés

#### Devices
- **DeviceSerializer**
  - Device complet avec infos véhicule
  - Validation IMEI unique
  - Vérification du quota utilisateur

- **DeviceListSerializer**
  - Version simplifiée pour listes

- **DeviceCreateSerializer**
  - Création de device
  - Validation IMEI

- **DeviceUpdateSerializer**
  - Mise à jour device
  - Champs modifiables uniquement

#### Configuration
- **DeviceSettingsSerializer**
  - Paramètres device (APN, capteurs, intervalles)

#### Commandes
- **DeviceCommandSerializer**
  - Commandes envoyées aux devices
  
- **DeviceCommandCreateSerializer**
  - Création de commande
  - Vérification device en ligne
  - Génération commande brute

#### Statut
- **DeviceStatusSerializer**
  - Statut temps réel

**Total: 9 serializers**

---

### 4. **tracking/serializers.py** - Suivi GPS

#### Positions
- **GPSPositionSerializer**
  - Positions GPS complètes
  - Champ location calculé
  
- **GPSPositionListSerializer**
  - Version simplifiée

#### Trajets
- **TripSerializer**
  - Trajets avec positions start/end
  - Statistiques de trajet
  
- **TripListSerializer**
  - Version simplifiée

- **TripStatisticsSerializer**
  - Statistiques agrégées

#### Arrêts
- **StopSerializer**
  - Arrêts pendant trajets

#### Géofences
- **GeofenceSerializer**
  - Géofences (cercle, polygone, rectangle)
  - Validation de géométrie
  
- **GeofenceEventSerializer**
  - Événements entrée/sortie

#### Rapports
- **ReportSerializer**
  - Rapports générés
  
- **ReportCreateSerializer**
  - Création de rapport
  - Validation des dates et devices

#### Filtres
- **PositionHistoryFilterSerializer**
  - Filtrage de l'historique

**Total: 11 serializers**

---

### 5. **alerts/serializers.py** - Système d'Alertes

#### Règles
- **AlertRuleSerializer**
  - Règles d'alerte complètes
  - Validation selon le type
  
- **AlertRuleCreateSerializer**
  - Création de règle

#### Alertes
- **AlertSerializer**
  - Alertes déclenchées avec détails
  
- **AlertListSerializer**
  - Version simplifiée

- **AlertAcknowledgeSerializer**
  - Acquittement d'alerte

- **AlertStatisticsSerializer**
  - Statistiques d'alertes

#### Notifications
- **NotificationLogSerializer**
  - Journal des notifications

#### Maintenance
- **MaintenanceReminderSerializer**
  - Rappels de maintenance
  
- **MaintenanceReminderCreateSerializer**
  - Création de rappel
  - Validation selon le type

- **MaintenanceCompleteSerializer**
  - Marquer comme complété

**Total: 10 serializers**

---

### 6. **fleet/serializers.py** - Gestion de Flotte

#### Groupes
- **DeviceGroupSerializer**
  - Groupes de devices
  
- **DeviceGroupTreeSerializer**
  - Hiérarchie de groupes (récursif)

#### Conducteurs
- **DriverSerializer**
  - Conducteurs complets
  - Assignation actuelle
  
- **DriverListSerializer**
  - Version simplifiée

#### Assignations
- **DriverAssignmentSerializer**
  - Assignations conducteur-véhicule
  
- **DriverAssignmentCreateSerializer**
  - Création d'assignation
  - Vérification chevauchements

#### Carburant
- **FuelEntrySerializer**
  - Entrées de carburant
  - Calcul de consommation
  
- **FuelEntryCreateSerializer**
  - Création d'entrée
  - Calcul prix par litre

- **FuelAnalysisSerializer**
  - Analyse de consommation

#### Maintenance
- **MaintenanceRecordSerializer**
  - Enregistrements de maintenance
  
- **MaintenanceRecordCreateSerializer**
  - Création d'enregistrement
  - Calcul coût total

- **MaintenanceSummarySerializer**
  - Résumé de maintenance

#### Statistiques
- **FleetStatisticsSerializer**
  - Statistiques de flotte
  
- **FleetSummarySerializer**
  - Résumé temps réel

**Total: 14 serializers**

---

## 📊 Récapitulatif

### Statistiques globales
- **Total de serializers créés**: **60 serializers**
- **6 fichiers serializers.py** créés
- Support complet de toutes les opérations CRUD
- Validation de données robuste
- Champs calculés et SerializerMethodField
- Serializers imbriqués pour les relations
- Serializers de création/liste/mise à jour séparés

### Répartition par type
```
accounts:   7 serializers  (12%)
billing:    9 serializers  (15%)
devices:    9 serializers  (15%)
tracking:  11 serializers  (18%)
alerts:    10 serializers  (17%)
fleet:     14 serializers  (23%)
```

---

## 🎯 Fonctionnalités des Serializers

### ✅ Fonctionnalités implémentées

1. **Validation automatique**
   - Validation des champs selon le type
   - Validation personnalisée par serializer
   - Validation croisée dans `validate()`

2. **Champs calculés**
   - `SerializerMethodField` pour champs dynamiques
   - Champs read-only pour données dérivées
   - Source pour accès aux relations

3. **Relations imbriquées**
   - DetailSerializer pour relations
   - ListSerializer pour listes simplifiées
   - Support des relations M2M et ForeignKey

4. **Permissions**
   - Vérification des droits dans `validate()`
   - Contrôle d'accès aux ressources
   - Validation du propriétaire

5. **Optimisations**
   - Serializers simplifiés pour les listes
   - Champs read-only pour performances
   - Select_related/prefetch_related (dans ViewSets)

6. **Transformation de données**
   - Calculs automatiques (totaux, dates)
   - Génération d'identifiants uniques
   - Formatage de données

---

## 🔧 Utilisation des Serializers

### Exemple: Créer un device
```python
from devices.serializers import DeviceCreateSerializer

# Dans une view
serializer = DeviceCreateSerializer(
    data=request.data,
    context={'request': request}
)
if serializer.is_valid():
    device = serializer.save(owner=request.user)
    return Response(
        DeviceSerializer(device).data,
        status=status.HTTP_201_CREATED
    )
return Response(
    serializer.errors,
    status=status.HTTP_400_BAD_REQUEST
)
```

### Exemple: Lister avec filtrage
```python
from devices.serializers import DeviceListSerializer

devices = Device.objects.filter(owner=request.user, status='active')
serializer = DeviceListSerializer(devices, many=True)
return Response(serializer.data)
```

### Exemple: Mise à jour
```python
from devices.serializers import DeviceUpdateSerializer

serializer = DeviceUpdateSerializer(
    instance=device,
    data=request.data,
    partial=True  # Pour PATCH
)
if serializer.is_valid():
    serializer.save()
    return Response(serializer.data)
```

---

## 📝 Prochaines Étapes

Maintenant que les serializers sont créés, la prochaine étape est :

1. **Créer les ViewSets** pour chaque modèle
2. **Configurer les URLs** (routers DRF)
3. **Ajouter les permissions classes**
4. **Implémenter les filtres et recherche**
5. **Ajouter la pagination**
6. **Créer les tests unitaires**

---

## 🔍 Convention de nommage

Les serializers suivent une convention stricte:

- **ModelSerializer**: Serializer complet du modèle
- **ModelListSerializer**: Version simplifiée pour listes
- **ModelCreateSerializer**: Création uniquement
- **ModelUpdateSerializer**: Mise à jour uniquement
- **ActionSerializer**: Pour actions spécifiques (Acknowledge, Cancel, etc.)
- **StatisticsSerializer**: Pour données agrégées

---

**Date de création**: 19 janvier 2026
**Version**: 1.0
**Statut**: ✅ Tous les serializers créés et documentés
