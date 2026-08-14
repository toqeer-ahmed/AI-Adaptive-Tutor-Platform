import time
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

class LatencyTracker:
    """
    Instruments AI execution pipeline latency breakdown:
    - retrieval_latency_ms
    - embedding_latency_ms
    - time_to_first_token_ms (TTFT)
    - llm_generation_latency_ms
    - total_latency_ms
    """
    def __init__(self):
        self.start_time = time.perf_counter()
        self.ttft_time: Optional[float] = None
        self.retrieval_ms: float = 0.0
        self.embedding_ms: float = 0.0
        self.llm_ms: float = 0.0

    def mark_retrieval_done(self, elapsed_ms: float):
        self.retrieval_ms = elapsed_ms

    def mark_first_token(self):
        if self.ttft_time is None:
            self.ttft_time = (time.perf_counter() - self.start_time) * 1000.0

    def get_summary(self) -> Dict[str, float]:
        total_ms = (time.perf_counter() - self.start_time) * 1000.0
        return {
            "retrieval_latency_ms": round(self.retrieval_ms, 2),
            "time_to_first_token_ms": round(self.ttft_time or total_ms, 2),
            "llm_latency_ms": round(self.llm_ms or total_ms, 2),
            "total_latency_ms": round(total_ms, 2)
        }

async def stream_tutor_tokens(
    full_text: str,
    chunk_delay_sec: float = 0.03
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Yields token chunks with TTFT tracking for interactive Socratic tutoring sessions.
    """
    tracker = LatencyTracker()
    words = full_text.split(" ")

    for idx, word in enumerate(words):
        if idx == 0:
            tracker.mark_first_token()

        yield {
            "token": word + (" " if idx < len(words) - 1 else ""),
            "index": idx,
            "is_complete": idx == len(words) - 1
        }
        await asyncio.sleep(chunk_delay_sec)
