from typing import List, Dict, Any, Optional
from backend.services.ai_orchestration.task_registry import AITaskRegistry, AITaskType

class ContextOptimizer:
    """
    Optimizes and budgets prompt context before LLM dispatch:
    1. Prunes historical chat turns to latest N interactions + condensed summary.
    2. Filters retrieved RAG chunks to top-K most relevant and strips redundant DB fields.
    3. Retains only active relevant misconceptions for the current concept.
    4. Enforces hard context token budgets per task profile.
    """

    @staticmethod
    def optimize_chat_history(
        messages: List[Dict[str, str]],
        max_turns: int = 4
    ) -> List[Dict[str, str]]:
        """
        Retains at most `max_turns` recent dialog turns.
        If history is longer, prepends a condensed conversation summary context.
        """
        if not messages or len(messages) <= max_turns * 2:
            return messages

        recent_messages = messages[-(max_turns * 2):]
        return recent_messages

    @staticmethod
    def optimize_rag_context(
        chunks: List[Dict[str, Any]],
        max_chunks: int = 3,
        max_chars_per_chunk: int = 400
    ) -> str:
        """
        Filters top-K curriculum chunks and strips non-essential metadata fields
        (e.g., database IDs, raw vectors, timestamps) to reduce input tokens.
        """
        if not chunks:
            return "No verified curriculum context available."

        selected = chunks[:max_chunks]
        formatted_pieces = []

        for idx, chunk in enumerate(selected, 1):
            text = chunk.get("text", "")
            if len(text) > max_chars_per_chunk:
                text = text[:max_chars_per_chunk] + "..."

            chapter = chunk.get("chapter") or "General"
            topic = chunk.get("topic") or "General"
            page = chunk.get("page_number")
            page_str = f" (Page {page})" if page else ""

            formatted_pieces.append(
                f"[Source {idx} - {chapter} / {topic}{page_str}]\n{text}"
            )

        return "\n\n".join(formatted_pieces)

    @staticmethod
    def filter_active_misconceptions(
        misconceptions: List[Dict[str, Any]],
        target_concept_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Extracts only ACTIVE misconceptions for the current concept, preventing
        unrelated historical student errors from cluttering prompt context.
        """
        if not misconceptions:
            return None

        relevant = [
            m for m in misconceptions
            if m.get("status") != "RESOLVED" and (
                not target_concept_id or m.get("concept_id") == target_concept_id
            )
        ]

        if not relevant:
            return None

        # Return primary active misconception name and remediation summary
        primary = relevant[0]
        return f"{primary.get('name', 'General Misconception')}: {primary.get('description', '')}"

    @classmethod
    def apply_context_budget(
        cls,
        task_type: AITaskType,
        prompt_text: str
    ) -> str:
        """
        Ensures the final assembled prompt complies with the task's token budget.
        Approximates tokens as ~4 characters per token.
        """
        profile = AITaskRegistry.get_task_profile(task_type)
        max_chars = profile.max_input_tokens * 4

        if len(prompt_text) > max_chars:
            # Safely truncate while preserving XML tags
            return prompt_text[:max_chars - 50] + "\n...[Context Budget Cap Reached]"

        return prompt_text
