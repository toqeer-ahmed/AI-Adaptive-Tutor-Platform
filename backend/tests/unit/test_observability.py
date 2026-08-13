import pytest
from httpx import AsyncClient
from backend.config.logging import mask_sensitive_data

@pytest.mark.asyncio
async def test_correlation_header_injection_and_latency(async_client: AsyncClient):
    # Send request with custom Correlation-ID
    custom_corr_id = "test-correlation-12345"
    response = await async_client.get("/health", headers={"X-Correlation-ID": custom_corr_id})

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == custom_corr_id
    assert "X-Response-Time-Ms" in response.headers

@pytest.mark.asyncio
async def test_sensitive_data_and_secret_masking():
    sensitive_payload = {
        "user_email": "student@school.edu",
        "api_key": "sk-proj-secret-12345",
        "password": "SuperSecretPassword123!",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "nested": {
            "token": "secret-token-xyz"
        }
    }

    masked = mask_sensitive_data(sensitive_payload)

    assert masked["user_email"] == "student@school.edu"
    assert masked["api_key"] == "***REDACTED***"
    assert masked["password"] == "***REDACTED***"
    assert masked["authorization"] == "***REDACTED***"
    assert masked["nested"]["token"] == "***REDACTED***"

    raw_string = "Authorization: Bearer my-secret-jwt-token-val"
    masked_str = mask_sensitive_data(raw_string)
    assert "my-secret-jwt-token-val" not in masked_str
    assert "***REDACTED***" in masked_str
