"""Named staff identity primitives: password hashing, TOTP second factor, session tokens.

Standard library only, so the pilot does not inherit a credential dependency before
the deployment and identity-provider decisions in docs/BUILD_BACKLOG.md (B01c) are
made. Nothing here is a substitute for a reviewed production identity provider; it
exists so authorization can be designed and tested against named accounts instead of
a shared static key.
"""
from dataclasses import dataclass
import base64
import hashlib
import hmac
import secrets
import struct
import time

SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 64 * 1024 * 1024
TOTP_STEP = 30
TOTP_DIGITS = 6
TOTP_WINDOW = 1

ROLES = {'analyst', 'admin', 'pulse'}
# Reviewing evidence and reading aggregates are different jobs; admin additionally
# manages accounts within its own organization and never across organizations.
ROLE_CAPABILITIES = {
    'analyst': {'reports.read', 'reports.review', 'graph.read'},
    'admin': {'reports.read', 'reports.review', 'graph.read', 'pulse.read', 'staff.manage'},
    'pulse': {'pulse.read'},
}


def hash_password(password: str) -> str:
    """Return `salt:derived` hex. scrypt is memory-hard, unlike a bare SHA digest."""
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                             p=SCRYPT_P, dklen=32, maxmem=SCRYPT_MAXMEM)
    return f'{salt.hex()}:{derived.hex()}'


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, expected_hex = stored.split(':', 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, AttributeError):
        return False
    derived = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                             p=SCRYPT_P, dklen=32, maxmem=SCRYPT_MAXMEM)
    return hmac.compare_digest(derived.hex(), expected_hex)


def new_totp_secret() -> str:
    """Base32 secret compatible with standard authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode('ascii').rstrip('=')


def totp_at(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + '=' * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** TOTP_DIGITS)).zfill(TOTP_DIGITS)


def totp_now(secret: str, at: float | None = None) -> str:
    return totp_at(secret, int((at if at is not None else time.time()) // TOTP_STEP))


def verify_totp(secret: str, code: str, at: float | None = None) -> bool:
    """RFC 6238 verification with a +/-1 step tolerance for clock drift."""
    code = (code or '').strip().replace(' ', '')
    if not code.isdigit() or len(code) != TOTP_DIGITS:
        return False
    counter = int((at if at is not None else time.time()) // TOTP_STEP)
    return any(hmac.compare_digest(totp_at(secret, counter + drift), code)
               for drift in range(-TOTP_WINDOW, TOTP_WINDOW + 1))


def provisioning_uri(secret: str, email: str, issuer: str = 'Trust.kh') -> str:
    from urllib.parse import quote
    label = quote(f'{issuer}:{email}', safe='')
    return (f'otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}'
            f'&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_STEP}')


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_fingerprint(token: str) -> str:
    """Sessions are stored as digests so a database copy cannot be replayed."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Principal:
    """The authenticated caller. Authorization is decided from this, never from input."""
    staff_id: str
    org_id: str
    email: str
    display_name: str
    role: str
    mfa_satisfied: bool

    def can(self, capability: str) -> bool:
        return self.mfa_satisfied and capability in ROLE_CAPABILITIES.get(self.role, set())
