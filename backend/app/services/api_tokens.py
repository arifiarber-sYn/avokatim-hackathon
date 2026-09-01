"""Public API tokens (personal access tokens) for external integrations.

Format: ``avk_`` + 40 hex chars. Only the SHA-256 of the full plaintext is
stored (``ApiToken.token_hash``); the plaintext is shown once at creation.
A token authenticates as its creating user with that user's permissions and
tenant scoping; ``scope="read"`` tokens are rejected on any mutating verb.
"""
import hashlib
import secrets

TOKEN_PREFIX = "avk_"
# Displayed identification prefix, e.g. "avk_ab12cd34" (fits ApiToken.prefix)
DISPLAY_PREFIX_LEN = 12
MAX_ACTIVE_TOKENS_PER_USER = 10
SCOPES = ("read", "read_write")
# Verbs a read-only token may use
READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_hex(20)


def hash_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def display_prefix(plaintext: str) -> str:
    return plaintext[:DISPLAY_PREFIX_LEN]


def is_api_token(credential: str) -> bool:
    return credential.startswith(TOKEN_PREFIX)


def scope_allows(scope: str, method: str) -> bool:
    return scope == "read_write" or method.upper() in READ_METHODS
