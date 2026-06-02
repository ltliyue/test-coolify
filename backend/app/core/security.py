from __future__ import annotations
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Set

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_log = logging.getLogger(__name__)

# C-04: JWT blocklist — Redis first, in-memory fallback
_token_blacklist: Set[str] = set()  # In-memory fallback
_redis_blacklist = None  # type: ignore

try:
    import redis as _sync_redis
    _redis_blacklist = _sync_redis.from_url(settings.REDIS_URL, decode_responses=True)
    _redis_blacklist.ping()
    _log.info("JWT blacklist: Redis connected")
except Exception:
    _redis_blacklist = None
    _log.info("JWT blacklist: Redis unavailable, using in-memory fallback")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["jti"] = str(uuid.uuid4())  # C-2: unique token ID for revocation
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["exp"] = expire
    to_encode["type"] = "refresh"
    to_encode["jti"] = str(uuid.uuid4())  # C-2: unique token ID for revocation
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _is_jti_revoked(jti: str) -> bool:
    """Check whether jti is blocklisted (Redis first, in-memory fallback)."""
    if _redis_blacklist:
        try:
            return _redis_blacklist.exists(f"jwt:revoked:{jti}") > 0
        except Exception:
            pass
    return jti in _token_blacklist


def decode_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    jti = payload.get("jti")
    if jti and _is_jti_revoked(jti):
        raise ValueError("Token has been revoked")
    return payload


def revoke_token(token: str) -> None:
    """Blocklist a token jti (Redis first with TTL auto-cleanup, in-memory fallback)."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        jti = payload.get("jti")
        if not jti:
            return
        # Compute remaining TTL
        exp = payload.get("exp", 0)
        remaining = max(int(exp - datetime.now(timezone.utc).timestamp()), 60)
        # Redis storage (with TTL auto-cleanup)
        if _redis_blacklist:
            try:
                _redis_blacklist.setex(f"jwt:revoked:{jti}", remaining, "1")
                return
            except Exception:
                pass
        # In-memory fallback
        _token_blacklist.add(jti)
    except Exception:
        pass


def is_token_revoked(jti: str) -> bool:
    """Check whether jti is blocklisted."""
    return _is_jti_revoked(jti)
