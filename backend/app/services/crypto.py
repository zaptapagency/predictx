"""
Symmetric encryption for third-party credentials at rest.

Connector credentials and integration configs hold OAuth tokens, database
passwords and Slack webhook URLs. Anyone who reads those rows can act as the
customer, so they are encrypted before they touch the database.

`EncryptedJSON` is a SQLAlchemy TypeDecorator: call sites keep assigning and
reading plain dicts, and there is no write path that can forget to encrypt.
"""

import base64
import hashlib
import json
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.config import settings

# Marks a column value as ciphertext. Anything without it is treated as a
# legacy plaintext row (see decrypt_value).
_PREFIX = "fernet:v1:"


def _derive_key() -> bytes:
    """
    Return the Fernet key, preferring an explicit ENCRYPTION_KEY.

    When ENCRYPTION_KEY is unset we derive one from JWT_SECRET_KEY instead of
    disabling encryption, so existing deploys keep working without a new env
    var. The tradeoff: rotating JWT_SECRET_KEY then makes stored credentials
    undecryptable (they degrade to "unreadable", not "leaked"), and the two
    secrets share a blast radius. Set ENCRYPTION_KEY in production.
    """
    explicit = (getattr(settings, "ENCRYPTION_KEY", "") or "").strip()
    if explicit:
        try:
            # Accept a real Fernet key verbatim so operators can generate one
            # with Fernet.generate_key().
            Fernet(explicit.encode())
            return explicit.encode()
        except (ValueError, TypeError):
            return base64.urlsafe_b64encode(hashlib.sha256(explicit.encode()).digest())

    return base64.urlsafe_b64encode(
        hashlib.sha256(f"forecastx-credentials:{settings.JWT_SECRET_KEY}".encode()).digest()
    )


_fernet: Optional[Fernet] = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_derive_key())
    return _fernet


def reset_cache() -> None:
    """Drop the cached key. Only useful for tests that change settings."""
    global _fernet
    _fernet = None


def encrypt_value(value: Any) -> Optional[str]:
    """Serialize a JSON-able value and return prefixed ciphertext."""
    if value is None:
        return None
    token = get_fernet().encrypt(json.dumps(value).encode())
    return _PREFIX + token.decode()


def decrypt_value(stored: Optional[str]) -> Any:
    """
    Reverse of encrypt_value, tolerating rows written before encryption existed.

    Production already holds plaintext JSON in these columns. Failing to decrypt
    would lock customers out of their own connections, so an unprefixed value is
    parsed as JSON and returned as-is; the next write re-encrypts it.
    """
    if stored is None:
        return None
    if isinstance(stored, (dict, list)):
        return stored
    if not isinstance(stored, str):
        return stored

    if stored.startswith(_PREFIX):
        try:
            return json.loads(get_fernet().decrypt(stored[len(_PREFIX):].encode()).decode())
        except (InvalidToken, ValueError):
            # Wrong/rotated key. Surfacing None keeps the app up; the connection
            # simply reads as unconfigured until re-entered.
            return None

    try:
        return json.loads(stored)
    except (ValueError, TypeError):
        return stored


class EncryptedJSON(TypeDecorator):
    """JSON column whose contents are Fernet-encrypted at rest."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        return decrypt_value(value)
