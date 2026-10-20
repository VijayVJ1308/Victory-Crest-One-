"""Victory Crest One - JWT Token Lifecycle Tests
Validates token encoding, claim extraction, and expiration rejection.
"""

from datetime import timedelta
import time
from backend.app.core.security import create_access_token, decode_access_token


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "usr_test_123", "username": "testuser", "role": "Hotel Manager"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr_test_123"
    assert decoded["username"] == "testuser"
    assert decoded["role"] == "Hotel Manager"
    assert decoded["iss"] == "victory-crest-one"


def test_jwt_token_expiration():
    payload = {"sub": "usr_expired"}
    # Token that expired 5 seconds ago
    token = create_access_token(payload, expires_delta=timedelta(seconds=-5))
    decoded = decode_access_token(token)
    assert decoded is None


def test_jwt_token_tampering():
    payload = {"sub": "usr_valid"}
    token = create_access_token(payload)
    # Tamper with token string
    tampered = token[:-4] + "abcd"
    decoded = decode_access_token(tampered)
    assert decoded is None
