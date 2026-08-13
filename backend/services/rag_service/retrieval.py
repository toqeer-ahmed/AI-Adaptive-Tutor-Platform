import uuid
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.rag import CurriculumVectorEmbeddings
from backend.services.rag_service.embedding import EmbeddingProvider, MockEmbeddingProvider

NO_CONTEXT_FALLBACK_TEXT = "I couldn't find that in the approved course material. I can help with the material your teacher has provided."
CONFIDENCE_THRESHOLD = 0.015 # RRF threshold for relevance

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    return dot / ((norm_a * norm_b) or 1e-9)

class HybridRAGRetrievalEngine:
    @staticmethod
    async def retrieve_relevant_chunks(
        session: AsyncSession,
        query_text: str,
        organization_id: uuid.UUID,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes Hybrid RAG Retrieval (Semantic + Keyword + RRF Fusion)
        with STRICT pre-retrieval tenant filtering and approval_status='PUBLISHED'.
        """
        if embedding_provider is None:
            embedding_provider = MockEmbeddingProvider()

        # 1. Generate query embedding vector
        query_vector = await embedding_provider.generate_embedding(query_text)

        # 2. Pre-Retrieval Tenant & Approval Filtering Query (CRITICAL SECURITY RULE)
        # MUST filter organization_id and approval_status='PUBLISHED' BEFORE retrieving candidates!
        stmt = select(CurriculumVectorEmbeddings).where(
            CurriculumVectorEmbeddings.organization_id == organization_id,
            CurriculumVectorEmbeddings.approval_status == "PUBLISHED"
        )
        if grade is not None:
            stmt = stmt.where(CurriculumVectorEmbeddings.grade == grade)
        if subject is not None:
            stmt = stmt.where(CurriculumVectorEmbeddings.subject == subject)

        res = await session.execute(stmt)
        candidate_records = res.scalars().all()

        # If zero published records exist for tenant -> trigger no-context fallback
        if not candidate_records:
            return {
                "has_context": False,
                "fallback_response": NO_CONTEXT_FALLBACK_TEXT,
                "chunks": [],
                "confidence_score": 0.0
            }

        # 3. Semantic Retrieval (Cosine Distance Ranking)
        semantic_scores = []
        for rec in candidate_records:
            vec = rec.embedding_vector
            if isinstance(vec, list):
                score = cosine_similarity(query_vector, vec)
                semantic_scores.append((rec, score))

        semantic_scores.sort(key=lambda x: x[1], reverse=True)

        # 4. Keyword Retrieval (Full-Text Term Matching)
        query_terms = set(query_text.lower().split())
        keyword_scores = []
        for rec in candidate_records:
            doc_text = f"{rec.chapter or ''} {rec.topic or ''} {rec.concept or ''} {rec.text_content}".lower()
            match_count = sum(1 for term in query_terms if term in doc_text)
            keyword_scores.append((rec, float(match_count)))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)

        # 5. Hybrid Fusion: Reciprocal Rank Fusion (RRF)
        # RRF_score = (1 / (60 + rank_sem)) + (1 / (60 + rank_kw))
        sem_rank_map = {rec.id: rank for rank, (rec, _) in enumerate(semantic_scores)}
        kw_rank_map = {rec.id: rank for rank, (rec, _) in enumerate(keyword_scores)}

        rrf_results = []
        for rec in candidate_records:
            r_sem = sem_rank_map.get(rec.id, 999)
            r_kw = kw_rank_map.get(rec.id, 999)
            rrf_score = (1.0 / (60.0 + r_sem)) + (1.0 / (60.0 + r_kw))
            rrf_results.append((rec, rrf_score))

        rrf_results.sort(key=lambda x: x[1], reverse=True)
        top_fusion = rrf_results[:top_k]

        max_confidence = top_fusion[0][1] if top_fusion else 0.0

        # 6. Confidence Threshold Guard & No-Context Fallback
        if max_confidence < CONFIDENCE_THRESHOLD:
            return {
                "has_context": False,
                "fallback_response": NO_CONTEXT_FALLBACK_TEXT,
                "chunks": [],
                "confidence_score": max_confidence
            }

        retrieved_chunks = []
        for rec, score in top_fusion:
            retrieved_chunks.append({
                "chunk_id": str(rec.id),
                "text": rec.text_content,
                "grade": rec.grade,
                "subject": rec.subject,
                "chapter": rec.chapter,
                "topic": rec.topic,
                "concept": rec.concept,
                "learning_objective": rec.learning_objective,
                "document_id": str(rec.document_id) if rec.document_id else None,
                "page_number": rec.page_number,
                "section": rec.section,
                "fusion_score": score
            })

        return {
            "has_context": True,
            "fallback_response": None,
            "chunks": retrieved_chunks,
            "confidence_score": max_confidence
        }
