from abc import ABC, abstractmethod
from backend.services.ai_orchestration.contracts import AIRequest, AIResponse

class LLMProviderAdapter(ABC):
    @abstractmethod
    async def generate_structured(self, request: AIRequest) -> AIResponse:
        """
        Executes an AI call expecting structured output.
        """
        pass
