import hashlib
import json
import time
from typing import Optional, Dict, Any

class AICacheManager:
    """
    Tenant-isolated cache manager for static curriculum explanations,
    retrieval results, and teacher analytics summaries.
    Enforces strict isolation and prevents caching un-hashed personalized student data.
    """

    _IN_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}
    DEFAULT_TTL_SECONDS = 3600 # 1 hour

    @classmethod
    def generate_cache_key(
        cls,
        organization_id: str,
        task_type: str,
        prompt_version: str,
        content_payload: str
    ) -> str:
        """
        Generates tenant-scoped SHA256 cache key.
        """
        raw = f"{organization_id}:{task_type}:{prompt_version}:{content_payload}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @classmethod
    def get(cls, key: str) -> Optional[Dict[str, Any]]:
        record = cls._IN_MEMORY_CACHE.get(key)
        if not record:
            return None

        if time.time() > record["expires_at"]:
            del cls._IN_MEMORY_CACHE[key]
            return None

        return record["data"]

    @classmethod
    def set(
        cls,
        key: str,
        data: Dict[str, Any],
        ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> None:
        cls._IN_MEMORY_CACHE[key] = {
            "data": data,
            "expires_at": time.time() + ttl_seconds
        }

    @classmethod
    def clear(cls) -> None:
        cls._IN_MEMORY_CACHE.clear()
