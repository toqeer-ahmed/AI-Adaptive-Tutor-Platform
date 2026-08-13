import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.rag_service.indexer import CurriculumVectorIndexer
from backend.services.rag_service.retrieval import HybridRAGRetrievalEngine
from backend.services.rag_service.context_builder import ContextBuilder
from backend.models.user import User

router = APIRouter(prefix="/rag", tags=["Curriculum RAG"])

class RAGQueryRequest(BaseModel):
    query: str
    grade: Optional[int] = None
    subject: Optional[str] = None

@router.post("/index/{version_id}", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def index_curriculum_version(
    version_id: str,
    session: AsyncSession = Depends(get_db)
):
    try:
        count = await CurriculumVectorIndexer.index_curriculum_version(session, uuid.UUID(version_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "version_id": version_id,
            "indexed_nodes": count,
            "status": "success"
        },
        "error": None,
        "meta": {}
    }

@router.post("/query", response_model=dict)
async def query_curriculum_rag(
    req: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Execute Hybrid Retrieval with strict tenant isolation
    retrieval_result = await HybridRAGRetrievalEngine.retrieve_relevant_chunks(
        session=session,
        query_text=req.query,
        organization_id=current_user.organization_id,
        grade=req.grade,
        subject=req.subject
    )

    formatted_context = ContextBuilder.build_rag_prompt_context(retrieval_result)

    return {
        "data": {
            "has_context": retrieval_result["has_context"],
            "fallback_response": retrieval_result["fallback_response"],
            "confidence_score": retrieval_result["confidence_score"],
            "formatted_context": formatted_context,
            "sources": retrieval_result["chunks"]
        },
        "error": None,
        "meta": {"chunk_count": len(retrieval_result["chunks"])}
    }
