import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.rag_service.retrieval import HybridRAGRetrievalEngine, NO_CONTEXT_FALLBACK_TEXT
from backend.services.organization_service.service import OrganizationService

@pytest.mark.asyncio
async def test_no_context_fallback_when_no_records_exist(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Empty RAG Org", "EMPTYRAG")

    # Query RAG when database contains 0 vector records
    result = await HybridRAGRetrievalEngine.retrieve_relevant_chunks(
        session=db_session,
        query_text="Quantum mechanics string theory",
        organization_id=org.id,
        grade=6,
        subject="Mathematics"
    )

    assert result["has_context"] is False
    assert result["fallback_response"] == NO_CONTEXT_FALLBACK_TEXT
    assert len(result["chunks"]) == 0
