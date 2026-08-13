import pytest
from backend.services.user_service.auth import create_access_token, decode_token

def test_jwt_token_creation_and_decoding():
    token, jti = create_access_token(
        user_id="11111111-1111-1111-1111-111111111111",
        organization_id="22222222-2222-2222-2222-222222222222",
        roles=["Teacher"]
    )
    
    payload = decode_token(token)
    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["org_id"] == "22222222-2222-2222-2222-222222222222"
    assert "Teacher" in payload["roles"]

def test_invalid_token_decoding():
    with pytest.raises(ValueError):
        decode_token("invalid.jwt.token")
