"""Tests for envault.crypto encryption/decryption utilities."""

import pytest

from envault.crypto import encrypt, decrypt


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db\nSECRET_KEY=abc123"


def test_encrypt_returns_string():
    result = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_produces_different_ciphertexts_each_call():
    """Each call should produce a unique ciphertext due to random salt/nonce."""
    ct1 = encrypt(PLAINTEXT, PASSPHRASE)
    ct2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert ct1 != ct2


def test_decrypt_roundtrip():
    """Encrypting then decrypting should return the original plaintext."""
    ciphertext = encrypt(PLAINTEXT, PASSPHRASE)
    recovered = decrypt(ciphertext, PASSPHRASE)
    assert recovered == PLAINTEXT


def test_decrypt_wrong_passphrase_raises():
    ciphertext = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(ciphertext, "wrong-passphrase")


def test_decrypt_corrupted_payload_raises():
    ciphertext = encrypt(PLAINTEXT, PASSPHRASE)
    # Flip some bytes in the middle of the payload
    corrupted = ciphertext[:-4] + "XXXX"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSPHRASE)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid payload encoding"):
        decrypt("!!!not-base64!!!", PASSPHRASE)


def test_decrypt_too_short_payload_raises():
    import base64
    short_payload = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short_payload, PASSPHRASE)


def test_encrypt_empty_string():
    """Empty plaintext should still encrypt and decrypt successfully."""
    ciphertext = encrypt("", PASSPHRASE)
    recovered = decrypt(ciphertext, PASSPHRASE)
    assert recovered == ""
