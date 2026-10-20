"""Victory Crest One - Argon2 Cryptography Tests
Validates Argon2 password hashing, salt randomization, and verification security.
"""

from backend.app.core.security import hash_password, verify_password


def test_argon2_hash_and_verify():
    password = "SuperSecretPassword2026!"
    hashed = hash_password(password)

    # Argon2 hashes start with $argon2id$ or $argon2i$
    assert hashed.startswith("$argon2")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_argon2_salt_randomization():
    password = "ConsistentPassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    # Different salts must yield different hashes
    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_argon2_empty_or_invalid():
    assert verify_password("", "somehash") is False
    assert verify_password("password", "") is False
    assert verify_password("password", "invalid_corrupted_hash") is False
