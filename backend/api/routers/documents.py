import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.ingestion_service.security import DocumentSecurityValidator
from backend.services.ingestion_service.storage import StorageService
from backend.services.ingestion_service.pipeline import IngestionPipeline
from backend.services.audit_service import AuditService
from backend.models.curriculum import SourceDocument, DocumentChunk
from backend.models.user import User

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def upload_document(
    file: UploadFile = File(...),
    curriculum_id: Optional[str] = Form(None),
    curriculum_version_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    file_bytes = await file.read()
    file_name = file.filename or "uploaded_document.pdf"

    # 1. Security Validation
    try:
        DocumentSecurityValidator.validate_file_metadata(file_name, len(file_bytes), file.content_type or "")
        DocumentSecurityValidator.validate_magic_bytes(file_bytes, file_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    doc_id = uuid.uuid4()
    curr_uuid = uuid.UUID(curriculum_id) if curriculum_id else None
    ver_uuid = uuid.UUID(curriculum_version_id) if curriculum_version_id else None

    # 2. Storage
    storage_path = StorageService.get_storage_path(current_user.organization_id, doc_id, file_name)
    saved_path = await StorageService.save_file(storage_path, file_bytes)

    # 3. Create SourceDocument Record
    doc = SourceDocument(
        id=doc_id,
        organization_id=current_user.organization_id,
        school_id=current_user.school_id,
        curriculum_id=curr_uuid,
        curriculum_version_id=ver_uuid,
        uploaded_by_id=current_user.id,
        file_name=file_name,
        file_path=storage_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "application/octet-stream",
        status="UPLOADED"
    )
    session.add(doc)
    await session.commit()

    await AuditService.log_event(
        session=session,
        action="DOCUMENT_UPLOADED",
        resource_type="source_document",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(doc.id),
        details={"file_name": file_name, "file_size": len(file_bytes)}
    )

    # 4. Trigger Ingestion Pipeline (Inline + Async Celery integration)
    await IngestionPipeline.process_document(session, doc.id)
    await session.refresh(doc)

    return {
        "data": {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "status": doc.status,
            "error_message": doc.error_message,
            "created_at": doc.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("", response_model=dict)
async def list_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stmt = select(SourceDocument).where(SourceDocument.organization_id == current_user.organization_id).order_by(SourceDocument.created_at.desc())
    res = await session.execute(stmt)
    docs = res.scalars().all()

    return {
        "data": [
            {
                "id": str(d.id),
                "file_name": d.file_name,
                "file_size": d.file_size,
                "status": d.status,
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat()
            } for d in docs
        ],
        "error": None,
        "meta": {"count": len(docs)}
    }

@router.get("/{document_id}/status", response_model=dict)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    doc_uuid = uuid.UUID(document_id)
    res = await session.execute(
        select(SourceDocument).where(
            SourceDocument.id == doc_uuid,
            SourceDocument.organization_id == current_user.organization_id
        )
    )
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or forbidden.")

    return {
        "data": {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "status": doc.status,
            "error_message": doc.error_message,
            "metadata": doc.metadata_json,
            "created_at": doc.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/{document_id}/chunks", response_model=dict)
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    doc_uuid = uuid.UUID(document_id)
    # Check document ownership
    doc_res = await session.execute(
        select(SourceDocument).where(
            SourceDocument.id == doc_uuid,
            SourceDocument.organization_id == current_user.organization_id
        )
    )
    if not doc_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or forbidden.")

    res = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_uuid)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = res.scalars().all()

    return {
        "data": [
            {
                "id": str(c.id),
                "chunk_index": c.chunk_index,
                "text": c.text,
                "page_number": c.page_number,
                "section": c.section
            } for c in chunks
        ],
        "error": None,
        "meta": {"count": len(chunks)}
    }
