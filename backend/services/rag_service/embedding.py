import json
import hash_lib = None
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from backend.config import settings

class EmbeddingProvider(ABC):
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        pass

class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def generate_embedding(self, text: str) -> List[float]:
        # Generate deterministic vector based on text hash
        hash_digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(self.dimension):
            byte_val = hash_digest[i % len(hash_digest)]
            val = (float(byte_val) / 255.0) - 0.5
            vector.append(val)
        # Normalize vector length
        norm = sum(x*x for x in vector) ** 0.5
        return [x / (norm or 1.0) for x in vector]

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "embedding_model": "mock-embedding-v1",
            "embedding_dimension": self.dimension,
            "embedding_version": "v1.0"
        }

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "text-embedding-3-small", dimension: int = 1536):
        self.model_name = model_name
        self.dimension = dimension

    async def generate_embedding(self, text: str) -> List[float]:
        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == "your_openai_api_key_here":
            return await MockEmbeddingProvider(self.dimension).generate_embedding(text)

        import urllib.request
        url = "https://api.openai.com/v1/embeddings"
        payload = {"input": text, "model": self.model_name}
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                return resp_json["data"][0]["embedding"]
        except Exception:
            return await MockEmbeddingProvider(self.dimension).generate_embedding(text)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "embedding_model": self.model_name,
            "embedding_dimension": self.dimension,
            "embedding_version": "v1.0"
        }
