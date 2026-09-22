"""Instance Celery, pour lancer un worker : celery -A app.workers.celery_app worker"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("scantoexcel", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_routes = {"app.workers.tasks.*": {"queue": "extraction"}}
celery_app.autodiscover_tasks(["app.workers"])

# Suppression automatique des fichiers originaux passé leur délai de rétention.
# Lancer un worker dédié : celery -A app.workers.celery_app beat --loglevel=info
celery_app.conf.beat_schedule = {
    "purge-expired-originals": {
        "task": "app.workers.tasks.purge_expired_originals",
        "schedule": 3600.0,  # toutes les heures
    },
}
celery_app.conf.timezone = "UTC"
