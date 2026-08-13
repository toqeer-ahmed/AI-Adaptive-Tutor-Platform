import uuid
import asyncio
import logging
from workers.celery_app import celery_app
from backend.db.session import AsyncSessionLocal
from backend.services.ingestion_service.pipeline import IngestionPipeline
from backend.services.ai_orchestration.pipeline import CurriculumExtractionPipeline
from backend.models.user import User

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.process_document_task")
def process_document_task(document_id_str: str):
    logger.info(f"Starting Celery background ingestion task for document: {document_id_str}")
    doc_id = uuid.UUID(document_id_str)

    async def _run():
        async with AsyncSessionLocal() as session:
            await IngestionPipeline.process_document(session, doc_id)

    loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
    loop.run_until_complete(_run())
    logger.info(f"Finished Celery background ingestion task for document: {document_id_str}")
    return {"status": "completed", "document_id": document_id_str}

@celery_app.task(name="workers.extract_curriculum_task")
def extract_curriculum_task(document_id_str: str, curriculum_id_str: str, user_id_str: str, provider: str = "mock"):
    logger.info(f"Starting Celery AI curriculum extraction task for document: {document_id_str}")
    doc_id = uuid.UUID(document_id_str)
    curr_id = uuid.UUID(curriculum_id_str)
    usr_id = uuid.UUID(user_id_str)

    async def _run():
        async with AsyncSessionLocal() as session:
            # Fetch user
            user_res = await session.get(User, usr_id)
            if user_res:
                await CurriculumExtractionPipeline.extract_from_document(
                    session=session,
                    document_id=doc_id,
                    curriculum_id=curr_id,
                    actor=user_res,
                    provider=provider
                )

    loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
    loop.run_until_complete(_run())
    logger.info(f"Finished Celery AI curriculum extraction task for document: {document_id_str}")
    return {"status": "completed", "curriculum_id": curriculum_id_str}
