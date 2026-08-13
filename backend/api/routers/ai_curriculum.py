import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.ai_orchestration.pipeline import CurriculumExtractionPipeline
from backend.services.curriculum_service.service import CurriculumService
from backend.models.curriculum import Curriculum, CurriculumVersion, Chapter, Topic, Concept
from backend.models.user import User

router = APIRouter(prefix="/curricula", tags=["AI Curriculum Extraction"])

class ExtractCurriculumRequest(BaseModel):
    document_id: str
    provider: Optional[str] = "mock"

class BatchEditNodesRequest(BaseModel):
    # Action type: EDIT, MERGE, SPLIT, DELETE, ADD
    action: str
    target_node_type: str # chapter, topic, concept, objective
    node_id: Optional[str] = None
    payload: Dict[str, Any] = {}

@router.post("/{curriculum_id}/extract", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def trigger_ai_extraction(
    curriculum_id: str,
    req: ExtractCurriculumRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    curr_uuid = uuid.UUID(curriculum_id)
    doc_uuid = uuid.UUID(req.document_id)

    # Check curriculum exists
    curr = await CurriculumService.get_curriculum_by_id(session, curr_uuid)
    if not curr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found.")

    try:
        new_version = await CurriculumExtractionPipeline.extract_from_document(
            session=session,
            document_id=doc_uuid,
            curriculum_id=curr_uuid,
            actor=current_user,
            provider=req.provider or "mock"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "version_id": str(new_version.id),
            "version_number": new_version.version_number,
            "status": new_version.status,
            "metadata": new_version.metadata_json,
            "change_log": new_version.change_log
        },
        "error": None,
        "meta": {}
    }

@router.post("/versions/{version_id}/nodes/batch", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def batch_edit_proposed_nodes(
    version_id: str,
    req: BatchEditNodesRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    ver_uuid = uuid.UUID(version_id)
    version = await CurriculumService.get_version_by_id(session, ver_uuid)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum version not found.")

    if version.status in ["PUBLISHED", "ARCHIVED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot edit nodes of a {version.status} version.")

    # Perform batch node edits
    if req.action == "DELETE" and req.node_id:
        n_id = uuid.UUID(req.node_id)
        if req.target_node_type == "chapter":
            res = await session.get(Chapter, n_id)
            if res: await session.delete(res)
        elif req.target_node_type == "topic":
            res = await session.get(Topic, n_id)
            if res: await session.delete(res)
        elif req.target_node_type == "concept":
            res = await session.get(Concept, n_id)
            if res: await session.delete(res)
        await session.commit()

    elif req.action == "EDIT" and req.node_id:
        n_id = uuid.UUID(req.node_id)
        if req.target_node_type == "concept":
            cp = await session.get(Concept, n_id)
            if cp:
                if "name" in req.payload: cp.name = req.payload["name"]
                if "difficulty_level" in req.payload: cp.difficulty_level = req.payload["difficulty_level"]
                await session.commit()

    return {
        "data": {
            "status": "success",
            "action": req.action,
            "version_id": version_id
        },
        "error": None,
        "meta": {}
    }
