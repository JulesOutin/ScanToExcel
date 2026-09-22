"""Instance Celery, pour lancer un worker : celery -A app.workers.celery_app worker"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("scantoexcel", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_routes = {"app.workers.tasks.*": {"queue": "extraction"}}
celery_app.autodiscover_tasks(["app.workers"])
