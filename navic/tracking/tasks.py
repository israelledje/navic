from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger('tracking')

@shared_task
def cleanup_history_task():
    """
    Tâche Celery pour purger l'historique GPS selon le BillingPackage.
    S'exécute de façon périodique (via Celery Beat).
    """
    logger.info("Début de la tâche planifiée: Purge de l'historique GPS")
    try:
        call_command('cleanup_history')
        logger.info("Tâche planifiée terminée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la purge de l'historique (Tâche Celery): {e}")
