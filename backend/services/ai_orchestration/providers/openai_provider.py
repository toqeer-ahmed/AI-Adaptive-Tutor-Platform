import os
import json
import time
import urllib.request
import urllib.error
from backend.services.ai_orchestration.providers.base import LLMProviderAdapter
from backend.services.ai_orchestration.contracts import AIRequest, AIResponse
from backend.config import settings

class OpenAIProvider(LLMProviderAdapter):
    async def generate_structured(self, request: AIRequest) -> AIResponse:
        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == "your_openai_api_key_here":
            # Fallback to Mock provider response if API key is not configured
            from backend.services.ai_orchestration.providers.mock_provider import MockLLMProvider
            return await MockLLMProvider().generate_structured(request)

        start_time = time.time()
        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt}
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_format": {"type": "json_object"}
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_bytes = resp.read()
                resp_json = json.loads(resp_bytes.decode("utf-8"))

                content_str = resp_json["choices"][0]["message"]["content"]
                parsed_json = json.loads(content_str)
                usage = resp_json.get("usage", {})

                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                cost = (prompt_tokens * 0.000005) + (completion_tokens * 0.000015)
                latency = int((time.time() - start_time) * 1000)

                return AIResponse(
                    content_text=content_str,
                    content_json=parsed_json,
                    provider="openai",
                    model=settings.OPENAI_MODEL,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency,
                    cost_usd=cost
                )
        except Exception as e:
            # Fallback to mock on network error
            from backend.services.ai_orchestration.providers.mock_provider import MockLLMProvider
            return await MockLLMProvider().generate_structured(request)
