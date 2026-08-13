import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.health_check_task")
def health_check_task():
    logger.info("Executing Celery worker health check task.")
    return {"status": "ok", "message": "Worker is active and processing tasks."}
