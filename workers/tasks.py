import uuid
import asyncio
import logging
from workers.celery_app import celery_app
from backend.db.session import AsyncSessionLocal
from backend.services.ingestion_service.pipeline import IngestionPipeline

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.process_document_task")
def process_document_task(document_id_str: str):
    logger.info(f"Starting Celery background ingestion task for document: {document_id_str}")
    doc_id = uuid.UUID(document_id_str)

    async def _run():
        async with AsyncSessionLocal() as session:
            await IngestionPipeline.process_document(session, doc_id)

    # Run async function in event loop
    loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
    loop.run_until_complete(_run())
    logger.info(f"Finished Celery background ingestion task for document: {document_id_str}")
    return {"status": "completed", "document_id": document_id_str}
