from typing import List, Dict, Any

class ContextBuilder:
    @staticmethod
    def build_rag_prompt_context(retrieval_result: Dict[str, Any]) -> str:
        """
        Formats retrieved vector chunks into RAG prompt context with explicit source citations.
        """
        if not retrieval_result.get("has_context", False):
            return retrieval_result.get("fallback_response", "")

        chunks = retrieval_result.get("chunks", [])
        context_blocks = []

        for idx, chunk in enumerate(chunks, 1):
            citation_str = (
                f"[Source Citation #{idx}]: Grade {chunk['grade']} {chunk['subject']} | "
                f"Chapter: {chunk['chapter'] or 'N/A'} | Topic: {chunk['topic'] or 'N/A'} | "
                f"Concept: {chunk['concept'] or 'N/A'} (Page {chunk['page_number'] or 'N/A'})"
            )
            block = f"{citation_str}\nContent: \"{chunk['text']}\""
            context_blocks.append(block)

        return "\n\n---\n\n".join(context_blocks)
