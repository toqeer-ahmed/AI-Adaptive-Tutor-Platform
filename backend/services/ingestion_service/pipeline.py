import uuid
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.curriculum import SourceDocument, DocumentChunk
from backend.services.ingestion_service.security import DocumentSecurityValidator, MalwareScanner
from backend.services.ingestion_service.storage import StorageService
from backend.services.ingestion_service.parser import DocumentParser, DocumentChunker
from backend.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class IngestionPipeline:
    @staticmethod
    async def process_document(session: AsyncSession, document_id: uuid.UUID) -> SourceDocument:
        # Fetch document
        res = await session.execute(select(SourceDocument).where(SourceDocument.id == document_id))
        doc = res.scalars().first()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        try:
            # 1. SCANNING Stage
            doc.status = "SCANNING"
            await session.commit()

            file_bytes = await StorageService.read_file(doc.file_path)
            is_clean, scan_msg = MalwareScanner.scan_content(file_bytes)
            if not is_clean:
                doc.status = "FAILED"
                doc.error_message = f"Malware scan failed: {scan_msg}"
                await session.commit()
                return doc

            # 2. PROCESSING Stage
            doc.status = "PROCESSING"
            await session.commit()

            format_type = DocumentSecurityValidator.validate_magic_bytes(file_bytes, doc.file_name)

            # 3. PARSING Stage
            doc.status = "PARSING"
            await session.commit()

            needs_ocr = False
            if format_type == "pdf":
                pages, needs_ocr = DocumentParser.parse_pdf(file_bytes)
            elif format_type == "docx":
                pages = DocumentParser.parse_docx(file_bytes)
            else:
                pages = DocumentParser.parse_txt(file_bytes)

            if needs_ocr:
                doc.status = "OCR_REQUIRED"
                doc.error_message = "Low text density detected. OCR required for scanned pages."
                # Store partial text or proceed to chunking with OCR notice
            
            # 4. CHUNKING Stage
            doc.status = "CHUNKING"
            await session.commit()

            raw_chunks = DocumentChunker.chunk_pages(pages)

            # Delete existing chunks if retrying
            existing_chunks = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id))
            for c in existing_chunks.scalars().all():
                await session.delete(c)
            await session.flush()

            # Insert new chunks
            for c in raw_chunks:
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    organization_id=doc.organization_id,
                    curriculum_id=doc.curriculum_id,
                    curriculum_version_id=doc.curriculum_version_id,
                    chunk_index=c["chunk_index"],
                    text=c["text"],
                    page_number=c["page_number"],
                    section=c["section"]
                )
                session.add(chunk)

            # 5. COMPLETED Stage
            doc.status = "COMPLETED" if not needs_ocr else "REVIEW_REQUIRED"
            doc.metadata_json = {
                "format": format_type,
                "total_pages": len(pages),
                "total_chunks": len(raw_chunks),
                "needs_ocr": needs_ocr
            }
            await session.commit()

            await AuditService.log_event(
                session=session,
                action="DOCUMENT_INGESTION_COMPLETED",
                resource_type="source_document",
                actor_id=doc.uploaded_by_id,
                organization_id=doc.organization_id,
                resource_id=str(doc.id),
                details={"file_name": doc.file_name, "total_chunks": len(raw_chunks)}
            )

            return doc

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
            doc.status = "FAILED"
            doc.error_message = str(e)
            await session.commit()
            return doc
