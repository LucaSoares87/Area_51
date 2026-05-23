from datetime import timedelta

from src.auth.config import auth_settings
from src.auth.tokens import create_access_token, create_refresh_token, decode_token


class TestCreateAccessToken:
    def test_creates_valid_token(self):
        token = create_access_token("user1", "viewer")
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == "user1"
        assert payload.role == "viewer"
        assert payload.token_type == "access"

    def test_custom_expiry(self):
        token = create_access_token("user1", "admin", expires_delta=timedelta(minutes=5))
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == "user1"


class TestCreateRefreshToken:
    def test_creates_valid_refresh(self):
        token = create_refresh_token("user1", "analyst")
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == "user1"
        assert payload.role == "analyst"
        assert payload.token_type == "refresh"


class TestDecodeToken:
    def test_invalid_token_returns_none(self):
        result = decode_token("invalid.token.here")
        assert result is None

    def test_tampered_token_returns_none(self):
        token = create_access_token("user1", "viewer")
        tampered = token[:-5] + "XXXXX"
        result = decode_token(tampered)
        assert result is None
