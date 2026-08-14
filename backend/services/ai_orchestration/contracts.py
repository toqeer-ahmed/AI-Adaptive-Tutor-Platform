from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AIRequest(BaseModel):
    task_type: str
    system_prompt: str
    user_prompt: str
    temperature: float = 0.2
    max_tokens: int = 4000
    response_schema: Optional[Dict[str, Any]] = None

class AIResponse(BaseModel):
    content_text: str
    content_json: Optional[Dict[str, Any]] = None
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float

    @property
    def raw_text(self) -> str:
        return self.content_text

    @property
    def structured_output(self) -> Optional[Dict[str, Any]]:
        return self.content_json
