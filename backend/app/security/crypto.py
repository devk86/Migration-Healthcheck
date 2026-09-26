from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings
from app.errors import StorageFailed


def _fernet() -> Fernet:
    key = get_settings().credential_key
    if not key:
        raise StorageFailed("Credential encryption key is not configured.")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise StorageFailed("Credential encryption key is invalid.") from exc


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise StorageFailed("Stored credential could not be decrypted.") from exc
