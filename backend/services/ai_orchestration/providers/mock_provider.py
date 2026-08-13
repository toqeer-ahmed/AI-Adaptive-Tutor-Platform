import json
import time
from backend.services.ai_orchestration.providers.base import LLMProviderAdapter
from backend.services.ai_orchestration.contracts import AIRequest, AIResponse

class MockLLMProvider(LLMProviderAdapter):
    async def generate_structured(self, request: AIRequest) -> AIResponse:
        start_time = time.time()
        
        # Deterministic proposed curriculum structure
        mock_extraction = {
            "grade_level": 6,
            "subject_name": "Mathematics",
            "chapters": [
                {
                    "name": "Fractions and Decimals",
                    "description": "Fundamental operations on fractional and decimal numbers",
                    "sequence_order": 1,
                    "source_page": 1,
                    "source_section": "Chapter 1",
                    "topics": [
                        {
                            "name": "Adding and Subtracting Fractions",
                            "description": "Methods for adding fractions with common and uncommon denominators",
                            "sequence_order": 1,
                            "source_page": 1,
                            "source_section": "Section 1.1",
                            "concepts": [
                                {
                                    "name": "Common Denominator",
                                    "description": "Finding the least common multiple of denominators to perform addition",
                                    "difficulty_level": 3,
                                    "sequence_order": 1,
                                    "source_page": 1,
                                    "source_section": "Section 1.1.1",
                                    "skills": ["Find LCM", "Convert equivalent fractions"],
                                    "learning_objectives": [
                                        {
                                            "code": "MATH-G6-FRAC-001",
                                            "description": "Find least common denominator to add two fractions",
                                            "bloom_taxonomy_level": "Apply",
                                            "source_page": 1,
                                            "source_section": "Section 1.1.1"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        latency = int((time.time() - start_time) * 1000) + 50
        content_str = json.dumps(mock_extraction)

        return AIResponse(
            content_text=content_str,
            content_json=mock_extraction,
            provider="mock",
            model="mock-v1",
            prompt_tokens=150,
            completion_tokens=250,
            total_tokens=400,
            latency_ms=latency,
            cost_usd=0.0
        )
