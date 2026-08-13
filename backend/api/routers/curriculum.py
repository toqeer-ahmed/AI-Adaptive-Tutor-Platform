import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.curriculum_service.service import CurriculumService
from backend.models.user import User

router = APIRouter(prefix="/curricula", tags=["Curriculum"])

class CreateCurriculumRequest(BaseModel):
    name: str
    grade_level: int
    subject_name: str
    description: Optional[str] = None

class CreateVersionRequest(BaseModel):
    change_log: str

class TransitionStatusRequest(BaseModel):
    status: str # REVIEW, APPROVED, PUBLISHED, ARCHIVED

class CreateChapterRequest(BaseModel):
    name: str
    description: Optional[str] = None
    sequence_order: int = 1
    source_document_id: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class CreateTopicRequest(BaseModel):
    name: str
    description: Optional[str] = None
    sequence_order: int = 1
    source_document_id: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class CreateConceptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty_level: int = 3
    sequence_order: int = 1
    source_document_id: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None

class CreateObjectiveRequest(BaseModel):
    code: str
    description: str
    bloom_taxonomy_level: str = "Understand"

@router.post("", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def create_curriculum(
    req: CreateCurriculumRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    curriculum = await CurriculumService.create_curriculum(
        session=session,
        creator=current_user,
        name=req.name,
        grade_level=req.grade_level,
        subject_name=req.subject_name,
        description=req.description
    )

    return {
        "data": {
            "id": str(curriculum.id),
            "organization_id": str(curriculum.organization_id),
            "name": curriculum.name,
            "grade_level": curriculum.grade_level,
            "subject_name": curriculum.subject_name,
            "description": curriculum.description,
            "versions": [
                {
                    "id": str(v.id),
                    "version_number": v.version_number,
                    "status": v.status
                } for v in curriculum.versions
            ],
            "created_at": curriculum.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("", response_model=dict)
async def list_curricula(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    curricula = await CurriculumService.list_curricula(session, current_user.organization_id)
    return {
        "data": [
            {
                "id": str(c.id),
                "name": c.name,
                "grade_level": c.grade_level,
                "subject_name": c.subject_name,
                "versions": [
                    {
                        "id": str(v.id),
                        "version_number": v.version_number,
                        "status": v.status
                    } for v in c.versions
                ]
            } for c in curricula
        ],
        "error": None,
        "meta": {"count": len(curricula)}
    }

@router.get("/versions/{version_id}", response_model=dict)
async def get_version_tree(
    version_id: str,
    session: AsyncSession = Depends(get_db)
):
    ver_uuid = uuid.UUID(version_id)
    version = await CurriculumService.get_version_by_id(session, ver_uuid)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum version not found.")

    return {
        "data": {
            "id": str(version.id),
            "curriculum_id": str(version.curriculum_id),
            "version_number": version.version_number,
            "status": version.status,
            "published_at": version.published_at.isoformat() if version.published_at else None,
            "chapters": [
                {
                    "id": str(ch.id),
                    "name": ch.name,
                    "sequence_order": ch.sequence_order,
                    "topics": [
                        {
                            "id": str(tp.id),
                            "name": tp.name,
                            "sequence_order": tp.sequence_order,
                            "concepts": [
                                {
                                    "id": str(cp.id),
                                    "name": cp.name,
                                    "difficulty_level": cp.difficulty_level,
                                    "sequence_order": cp.sequence_order,
                                    "learning_objectives": [
                                        {
                                            "id": str(lo.id),
                                            "code": lo.code,
                                            "description": lo.description,
                                            "bloom_taxonomy_level": lo.bloom_taxonomy_level
                                        } for lo in cp.learning_objectives
                                    ]
                                } for cp in tp.concepts
                            ]
                        } for tp in ch.topics
                    ]
                } for ch in version.chapters
            ]
        },
        "error": None,
        "meta": {}
    }

@router.post("/versions/{version_id}/status", response_model=dict)
async def transition_version_status(
    version_id: str,
    req: TransitionStatusRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        version = await CurriculumService.transition_version_status(
            session=session,
            version_id=uuid.UUID(version_id),
            target_status=req.status,
            actor=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return {
        "data": {
            "id": str(version.id),
            "version_number": version.version_number,
            "status": version.status,
            "published_at": version.published_at.isoformat() if version.published_at else None
        },
        "error": None,
        "meta": {}
    }

@router.post("/versions/{version_id}/chapters", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def create_chapter(
    version_id: str,
    req: CreateChapterRequest,
    session: AsyncSession = Depends(get_db)
):
    doc_uuid = uuid.UUID(req.source_document_id) if req.source_document_id else None
    try:
        ch = await CurriculumService.create_chapter(
            session=session,
            version_id=uuid.UUID(version_id),
            name=req.name,
            description=req.description,
            sequence_order=req.sequence_order,
            source_document_id=doc_uuid,
            source_page=req.source_page,
            source_section=req.source_section
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"data": {"id": str(ch.id), "name": ch.name, "sequence_order": ch.sequence_order}, "error": None, "meta": {}}

@router.post("/chapters/{chapter_id}/topics", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def create_topic(
    chapter_id: str,
    req: CreateTopicRequest,
    session: AsyncSession = Depends(get_db)
):
    doc_uuid = uuid.UUID(req.source_document_id) if req.source_document_id else None
    try:
        tp = await CurriculumService.create_topic(
            session=session,
            chapter_id=uuid.UUID(chapter_id),
            name=req.name,
            description=req.description,
            sequence_order=req.sequence_order,
            source_document_id=doc_uuid,
            source_page=req.source_page,
            source_section=req.source_section
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"data": {"id": str(tp.id), "name": tp.name, "sequence_order": tp.sequence_order}, "error": None, "meta": {}}

@router.post("/topics/{topic_id}/concepts", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def create_concept(
    topic_id: str,
    req: CreateConceptRequest,
    session: AsyncSession = Depends(get_db)
):
    doc_uuid = uuid.UUID(req.source_document_id) if req.source_document_id else None
    try:
        cp = await CurriculumService.create_concept(
            session=session,
            topic_id=uuid.UUID(topic_id),
            name=req.name,
            description=req.description,
            difficulty_level=req.difficulty_level,
            sequence_order=req.sequence_order,
            source_document_id=doc_uuid,
            source_page=req.source_page,
            source_section=req.source_section
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"data": {"id": str(cp.id), "name": cp.name, "difficulty_level": cp.difficulty_level}, "error": None, "meta": {}}

@router.post("/concepts/{concept_id}/objectives", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def create_objective(
    concept_id: str,
    req: CreateObjectiveRequest,
    session: AsyncSession = Depends(get_db)
):
    try:
        lo = await CurriculumService.create_learning_objective(
            session=session,
            concept_id=uuid.UUID(concept_id),
            code=req.code,
            description=req.description,
            bloom_taxonomy_level=req.bloom_taxonomy_level
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"data": {"id": str(lo.id), "code": lo.code, "description": lo.description}, "error": None, "meta": {}}
