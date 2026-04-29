"""
Système de notification pour les alertes
"""
import logging
import requests
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('tracking')


def send_alert_notifications(alert):
    """
    Envoie les notifications pour une alerte selon les préférences de la règle
    
    Args:
        alert: Instance de Alert
    """
    from .models import NotificationLog
    
    rule = alert.rule
    if not rule:
        return
    
    # Email
    if rule.notify_email:
        send_email_notification(alert)
    
    # SMS
    if rule.notify_sms:
        send_sms_notification(alert)
    
    # Push notification
    if rule.notify_push:
        send_push_notification(alert)
    
    # Webhook
    if rule.notify_webhook and rule.webhook_url:
        send_webhook_notification(alert, rule.webhook_url)


def send_email_notification(alert):
    """Envoie une notification par email"""
    from .models import NotificationLog
    
    rule = alert.rule
    user = alert.user
    
    # Liste des destinataires
    recipients = [user.email]
    if rule.additional_emails:
        recipients.extend(rule.additional_emails)
    
    subject = f"[Navic Alert] {alert.title}"
    
    message = f"""
Bonjour,

Une alerte a été déclenchée:

Titre: {alert.title}
Message: {alert.message}
Sévérité: {alert.get_severity_display()}
Device: {alert.device.name}
Date: {alert.triggered_at.strftime('%d/%m/%Y %H:%M:%S')}

Détails:
- Latitude: {alert.position.latitude if alert.position else 'N/A'}
- Longitude: {alert.position.longitude if alert.position else 'N/A'}
- Vitesse: {alert.position.speed if alert.position else 'N/A'} km/h

Cordialement,
L'équipe Navic
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@navic.cg',
            recipients,
            fail_silently=False,
        )
        
        # Logger le succès
        for recipient in recipients:
            NotificationLog.objects.create(
                alert=alert,
                notification_type='email',
                recipient=recipient,
                subject=subject,
                content=message,
                status='sent',
                sent_at=timezone.now()
            )
        
        alert.email_sent = True
        alert.save(update_fields=['email_sent'])
        
        logger.info(f"Email de notification envoyé pour l'alerte {alert.id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email pour l'alerte {alert.id}: {str(e)}")
        
        NotificationLog.objects.create(
            alert=alert,
            notification_type='email',
            recipient=', '.join(recipients),
            subject=subject,
            content=message,
            status='failed',
            error_message=str(e)
        )


def send_sms_notification(alert):
    """Envoie une notification par SMS"""
    from .models import NotificationLog
    
    rule = alert.rule
    user = alert.user
    
    # Liste des numéros
    phone_numbers = []
    if user.phone:
        phone_numbers.append(user.phone)
    if rule.additional_phones:
        phone_numbers.extend(rule.additional_phones)
    
    if not phone_numbers:
        return
    
    # Message court pour SMS
    message = f"Navic Alert: {alert.title}. {alert.device.name}. {alert.triggered_at.strftime('%d/%m %H:%M')}"
    
    # Intégration avec un service SMS (à adapter selon le fournisseur)
    # Exemple avec une API générique
    sms_api_url = getattr(settings, 'SMS_API_URL', None)
    sms_api_key = getattr(settings, 'SMS_API_KEY', None)
    
    if not sms_api_url or not sms_api_key:
        logger.warning("Service SMS non configuré")
        return
    
    for phone in phone_numbers:
        try:
            # Exemple d'appel API (à adapter)
            response = requests.post(
                sms_api_url,
                json={
                    'to': phone,
                    'message': message,
                },
                headers={
                    'Authorization': f'Bearer {sms_api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                NotificationLog.objects.create(
                    alert=alert,
                    notification_type='sms',
                    recipient=phone,
                    content=message,
                    status='sent',
                    sent_at=timezone.now(),
                    response=response.text
                )
                
                alert.sms_sent = True
                alert.save(update_fields=['sms_sent'])
                
                logger.info(f"SMS envoyé à {phone} pour l'alerte {alert.id}")
            else:
                raise Exception(f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du SMS à {phone}: {str(e)}")
            
            NotificationLog.objects.create(
                alert=alert,
                notification_type='sms',
                recipient=phone,
                content=message,
                status='failed',
                error_message=str(e)
            )


def send_push_notification(alert):
    """Envoie une notification push"""
    from .models import NotificationLog
    
    # Intégration avec Firebase Cloud Messaging ou autre service
    # À implémenter selon les besoins
    
    logger.info(f"Push notification pour l'alerte {alert.id} (non implémenté)")
    
    # Marquer comme envoyée
    alert.push_sent = True
    alert.save(update_fields=['push_sent'])


def send_webhook_notification(alert, webhook_url):
    """Envoie une notification via webhook"""
    from .models import NotificationLog
    
    payload = {
        'alert_id': alert.id,
        'title': alert.title,
        'message': alert.message,
        'severity': alert.severity,
        'alert_type': alert.alert_type,
        'device': {
            'id': alert.device.id,
            'name': alert.device.name,
            'imei': alert.device.imei,
        },
        'position': {
            'latitude': alert.position.latitude if alert.position else None,
            'longitude': alert.position.longitude if alert.position else None,
            'speed': alert.position.speed if alert.position else None,
            'timestamp': alert.position.timestamp.isoformat() if alert.position else None,
        },
        'triggered_at': alert.triggered_at.isoformat(),
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        NotificationLog.objects.create(
            alert=alert,
            notification_type='webhook',
            recipient=webhook_url,
            content=str(payload),
            status='sent' if response.status_code == 200 else 'failed',
            sent_at=timezone.now(),
            response=response.text
        )
        
        alert.webhook_sent = True
        alert.save(update_fields=['webhook_sent'])
        
        logger.info(f"Webhook envoyé pour l'alerte {alert.id}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du webhook pour l'alerte {alert.id}: {str(e)}")
        
        NotificationLog.objects.create(
            alert=alert,
            notification_type='webhook',
            recipient=webhook_url,
            content=str(payload),
            status='failed',
            error_message=str(e)
        )
