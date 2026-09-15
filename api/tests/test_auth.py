# Ganymede API — Auth Tests

import os
import sys
import uuid
import pytest
import jwt as pyjwt
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.config import get_settings

settings = get_settings()


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        h = hash_password("testpassword123")
        assert isinstance(h, str)
        assert len(h) > 0

    def test_verify_password_correct(self):
        h = hash_password("testpassword123")
        assert verify_password("testpassword123", h) is True

    def test_verify_password_incorrect(self):
        h = hash_password("testpassword123")
        assert verify_password("wrongpassword", h) is False

    def test_verify_password_empty_hash(self):
        assert verify_password("testpassword123", "") is False

    def test_different_passwords_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self):
        token = create_access_token(
            user_id="test-user-id",
            role="attorney",
            expires_minutes=30,
        )
        assert isinstance(token, str)
        assert len(token) > 0

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-id"
        assert payload["role"] == "attorney"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_token_expiration(self):
        # Create token that expired 1 minute ago
        token = create_access_token(
            user_id="test-user-id",
            role="attorney",
            expires_minutes=-1,
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_token_contains_exp(self):
        token = create_access_token(
            user_id="test-user-id",
            role="attorney",
            expires_minutes=30,
        )
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload
        exp_dt = datetime.utcfromtimestamp(payload["exp"])
        assert exp_dt > datetime.utcnow()

    def test_token_with_uuid_user_id(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id=user_id, role="admin")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_token_with_all_roles(self):
        for role in ["administrator", "attorney", "paralegal", "reviewer", "it_operator"]:
            token = create_access_token(user_id="test-id", role=role)
            payload = decode_access_token(token)
            assert payload is not None
            assert payload["role"] == role


class TestSettings:
    def test_jwt_secret_key_exists(self):
        assert hasattr(settings, "JWT_SECRET_KEY")
        assert settings.JWT_SECRET_KEY is not None

    def test_access_token_expire_minutes(self):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
