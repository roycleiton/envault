"""Encryption and decryption utilities for envault.

Uses AES-GCM via the cryptography library to encrypt/decrypt
environment variable data with a user-supplied passphrase.
"""

import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256-bit AES key


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using Scrypt."""
    kdf = Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend(),
    )
    return kdf.derive(passphrase.encode())


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext with the given passphrase.

    Returns a base64-encoded string containing:
        salt (16 bytes) + nonce (12 bytes) + ciphertext
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt(encoded_payload: str, passphrase: str) -> str:
    """Decrypt a base64-encoded payload produced by :func:`encrypt`.

    Raises:
        ValueError: If decryption fails (wrong passphrase or corrupted data).
    """
    try:
        payload = base64.b64decode(encoded_payload.encode())
    except Exception as exc:
        raise ValueError("Invalid payload encoding.") from exc

    if len(payload) < SALT_SIZE + NONCE_SIZE + 1:
        raise ValueError("Payload is too short to be valid.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed. Wrong passphrase or corrupted data.") from exc

    return plaintext.decode()
