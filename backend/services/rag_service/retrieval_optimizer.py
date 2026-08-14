import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class RetrievalQualityMetrics:
    precision: float
    recall: float
    grounding_score: float
    citation_accuracy: float
    irrelevant_context_rate: float
    avg_fusion_score: float

class RetrievalOptimizer:
    """
    Implements Hybrid Dense/Sparse Retrieval (RRF), Cross-Encoder Reranking heuristic,
    metadata filtering, and RAG evaluation metric computations.
    """

    @staticmethod
    def hybrid_reciprocal_rank_fusion(
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        k: int = 60,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Combines dense vector rank and BM25 sparse keyword rank using Reciprocal Rank Fusion (RRF).
        RRF Score = sum(1 / (k + rank_i))
        """
        scores: Dict[str, float] = {}
        items_map: Dict[str, Dict[str, Any]] = {}

        # Process vector ranks
        for rank, item in enumerate(vector_results, 1):
            item_id = item.get("chunk_id", str(rank))
            scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (k + rank))
            items_map[item_id] = item

        # Process keyword ranks
        for rank, item in enumerate(keyword_results, 1):
            item_id = item.get("chunk_id", str(rank))
            scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (k + rank))
            if item_id not in items_map:
                items_map[item_id] = item

        # Sort by RRF score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        fused_results = []
        for i_id in sorted_ids[:top_n]:
            item = items_map[i_id].copy()
            item["fusion_score"] = round(scores[i_id], 4)
            fused_results.append(item)

        return fused_results

    @staticmethod
    def rerank_by_pedagogical_relevance(
        chunks: List[Dict[str, Any]],
        target_grade: int,
        target_subject: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Cross-Reranker heuristic prioritizing exact grade alignment, subject match,
        and concept terminology overlap.
        """
        query_terms = set(re.findall(r'\w+', query.lower()))

        def compute_rerank_score(chunk: Dict[str, Any]) -> float:
            score = chunk.get("fusion_score", 0.5)

            # Exact Grade match boost
            if chunk.get("grade") == target_grade:
                score += 0.25
            elif abs(chunk.get("grade", target_grade) - target_grade) > 1:
                score -= 0.30 # Penalize out-of-band grade material

            # Subject match boost
            if (chunk.get("subject") or "").lower() == target_subject.lower():
                score += 0.20

            # Term overlap in chunk text
            chunk_terms = set(re.findall(r'\w+', (chunk.get("text") or "").lower()))
            overlap = len(query_terms.intersection(chunk_terms))
            score += min(overlap * 0.05, 0.30)

            return score

        reranked = sorted(chunks, key=compute_rerank_score, reverse=True)
        return reranked

    @staticmethod
    def calculate_rag_metrics(
        retrieved_chunks: List[Dict[str, Any]],
        ground_truth_concept_ids: List[str],
        generated_response: str
    ) -> RetrievalQualityMetrics:
        """
        Calculates precision, recall, grounding, and citation accuracy for RAG evaluations.
        """
        if not retrieved_chunks:
            return RetrievalQualityMetrics(0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        # 1. Precision & Recall
        retrieved_concept_ids = [
            c.get("concept_id") or c.get("chunk_id") for c in retrieved_chunks if (c.get("concept_id") or c.get("chunk_id"))
        ]
        relevant_retrieved = set(retrieved_concept_ids).intersection(set(ground_truth_concept_ids))
        precision = len(relevant_retrieved) / len(retrieved_chunks) if retrieved_chunks else 0.0
        recall = len(relevant_retrieved) / len(ground_truth_concept_ids) if ground_truth_concept_ids else 1.0

        # 2. Grounding Score (overlap of key curriculum facts in generated response)
        total_chunks_text = " ".join([c.get("text", "") for c in retrieved_chunks]).lower()
        response_words = set(re.findall(r'\w{4,}', generated_response.lower()))
        grounded_words = [w for w in response_words if w in total_chunks_text]
        grounding_score = len(grounded_words) / len(response_words) if response_words else 1.0

        # 3. Citation Accuracy (checks if citation tags [Source X] exist and are valid)
        citations_found = re.findall(r'\[(?:Source|Citation)\s*#?(\d+)\]', generated_response, re.IGNORECASE)
        if citations_found:
            valid_citations = [c for c in citations_found if 1 <= int(c) <= len(retrieved_chunks)]
            citation_accuracy = len(valid_citations) / len(citations_found)
        else:
            citation_accuracy = 1.0 if not ground_truth_concept_ids else 0.85

        irrelevant_rate = 1.0 - precision
        avg_fusion = sum([c.get("fusion_score", 0.8) for c in retrieved_chunks]) / len(retrieved_chunks)

        return RetrievalQualityMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            grounding_score=round(grounding_score, 4),
            citation_accuracy=round(citation_accuracy, 4),
            irrelevant_context_rate=round(irrelevant_rate, 4),
            avg_fusion_score=round(avg_fusion, 4)
        )
