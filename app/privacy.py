import re

from cryptography.fernet import Fernet, InvalidToken

from .config import settings


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
IDENTIFIER_RE = re.compile(r"(?i)\b(?:patient\s*name|mrn|medical record(?:\s|_)?number|national id)\s*[:=#-]?\s*[^\n,;]+")


def _fernet() -> Fernet:
    key = settings.patient_field_encryption_key
    if not key:
        raise RuntimeError("Patient identity encryption is not configured")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("PATIENT_FIELD_ENCRYPTION_KEY must be a Fernet key") from exc


def encrypt_patient_identity(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_patient_identity(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Patient identity could not be decrypted") from exc


def strip_identifiers(value: str) -> str:
    value = IDENTIFIER_RE.sub("[REDACTED IDENTIFIER]", value)
    value = EMAIL_RE.sub("[REDACTED EMAIL]", value)
    return PHONE_RE.sub("[REDACTED PHONE]", value)
