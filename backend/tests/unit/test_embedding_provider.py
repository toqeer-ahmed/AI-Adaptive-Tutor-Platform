import pytest
from backend.services.rag_service.embedding import MockEmbeddingProvider, OpenAIEmbeddingProvider

@pytest.mark.asyncio
async def test_mock_embedding_provider_dimension_and_normalization():
    provider = MockEmbeddingProvider(dimension=1536)
    vector = await provider.generate_embedding("Grade 6 Fractions")

    assert len(vector) == 1536
    # Vector length norm should be ~1.0
    norm = sum(x*x for x in vector) ** 0.5
    assert abs(norm - 1.0) < 1e-4

def test_embedding_provider_metadata():
    provider = MockEmbeddingProvider(dimension=1536)
    meta = provider.get_metadata()
    assert meta["embedding_dimension"] == 1536
    assert meta["embedding_model"] == "mock-embedding-v1"
