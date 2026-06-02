from __future__ import annotations
import logging
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_platform_db
from app.core.deps import get_current_user, bearer_scheme
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.models.agency import Agency

_log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory token blacklist (jti set). In production, use Redis.
_token_blacklist: set[str] = set()

# ── M-10: login throttling — brute-force defense ─────────────────────────
_LOGIN_MAX_ATTEMPTS = 5       # Max consecutive failed attempts per IP
_LOGIN_WINDOW_SECONDS = 300   # Window duration: 5 minutes
_LOGIN_LOCKOUT_SECONDS = 900  # Lockout duration: 15 minutes
_MAX_TRACKED_IPS = 50_000     # In-memory LRU upper bound


class _LoginRateLimiter:
    """In-memory per-IP rate limiter (recommended to upgrade to Redis in production)."""

    def __init__(self) -> None:
        # key=ip, value=(fail_count, first_fail_time, lockout_until)
        self._store: OrderedDict[str, tuple[int, float, float]] = OrderedDict()

    def _evict(self) -> None:
        while len(self._store) > _MAX_TRACKED_IPS:
            self._store.popitem(last=False)

    def check(self, ip: str) -> None:
        """Check whether the IP is rate-limited; raise 429 if currently locked out."""
        now = time.time()
        entry = self._store.get(ip)
        if not entry:
            return
        fail_count, first_fail, lockout_until = entry
        if lockout_until and now < lockout_until:
            remaining = int(lockout_until - now)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Try again in {remaining} seconds.",
            )
        # Window has elapsed; clear the record
        if now - first_fail > _LOGIN_WINDOW_SECONDS:
            del self._store[ip]

    def record_failure(self, ip: str) -> None:
        """Record a single failure."""
        now = time.time()
        entry = self._store.get(ip)
        if entry:
            fail_count, first_fail, _ = entry
            if now - first_fail > _LOGIN_WINDOW_SECONDS:
                # Window expired; reset count
                fail_count, first_fail = 0, now
            fail_count += 1
        else:
            fail_count, first_fail = 1, now

        lockout_until = 0.0
        if fail_count >= _LOGIN_MAX_ATTEMPTS:
            lockout_until = now + _LOGIN_LOCKOUT_SECONDS
            _log.warning("Login rate limit triggered for IP: %s (attempts=%d)", ip, fail_count)

        self._store[ip] = (fail_count, first_fail, lockout_until)
        self._store.move_to_end(ip)
        self._evict()

    def record_success(self, ip: str) -> None:
        """On successful login, clear the failure record for this IP."""
        self._store.pop(ip, None)


_login_limiter = _LoginRateLimiter()


def _get_client_ip(request: Request) -> str:
    """from the requestextractclient IP。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _build_token_pair(user: User) -> TokenResponse:
    # Platform users have agency_id=None; encode empty string in the JWT.
    token_data = {
        "sub": str(user.id),
        "agency_id": str(user.agency_id) if user.agency_id else "",
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def _reject_if_agency_suspended(db: AsyncSession, user: User) -> None:
    """Block login when the user's agency is suspended. Platform users (agency_id IS NULL) pass through."""
    if user.agency_id is None:
        return
    result = await db.execute(select(Agency).where(Agency.id == user.agency_id))
    agency = result.scalar_one_or_none()
    if agency is not None and agency.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agency suspended",
        )


def _slugify(name: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")
    return slug or "agency"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_platform_db),
) -> TokenResponse:
    """Self-service signup: creates a new agency + agency_admin user."""
    from app.core.pii_crypto import encrypt_pii, hash_email

    email_hash = hash_email(payload.email)
    existing = await db.execute(select(User).where(User.email_hash == email_hash))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Derive a unique slug
    base_slug = _slugify(payload.agency_name)
    slug = base_slug
    counter = 1
    while True:
        found = await db.execute(select(Agency).where(Agency.slug == slug))
        if found.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    from app.core.tenant_provisioner import provision_tenant_database

    # Legacy db_schema is preserved for the migration cutover (it's NOT NULL
    # in the platform DB). PR 2 routes every query through agency.db_dsn,
    # which is filled in by provision_tenant_database below.
    schema_name = "tenant_" + slug.replace("-", "_")
    agency = Agency(name=payload.agency_name, slug=slug, db_schema=schema_name)
    db.add(agency)
    await db.flush()
    # Provision the per-Agency physical Postgres database and persist the
    # encrypted DSN. Failure aborts the request so no orphaned row remains.
    agency.db_dsn = await provision_tenant_database(agency=agency, platform_db=db)

    user = User(
        agency_id=agency.id,
        email=encrypt_pii(payload.email),
        email_hash=email_hash,
        full_name=encrypt_pii(payload.full_name),
        hashed_password=get_password_hash(payload.password),
        role=UserRole.agency_admin,
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _build_token_pair(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_platform_db),
) -> TokenResponse:
    # M-10: loginrate limitcheck
    client_ip = _get_client_ip(request)
    _login_limiter.check(client_ip)

    # M-02: use email_hash lookupuser（no longer use plaintext email for WHERE）
    from app.core.pii_crypto import hash_email
    result = await db.execute(select(User).where(User.email_hash == hash_email(payload.email)))
    user = result.scalar_one_or_none()

    if user is None or user.hashed_password is None:
        _login_limiter.record_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(payload.password, user.hashed_password):
        _login_limiter.record_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    await _reject_if_agency_suspended(db, user)

    _login_limiter.record_success(client_ip)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return _build_token_pair(user)


@router.post("/login/google", response_model=TokenResponse)
async def login_google(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_platform_db),
) -> TokenResponse:
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Google OAuth failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",  # H-1: do not leak internal exception
        )

    email: str = idinfo.get("email", "")
    google_id: str = idinfo.get("sub", "")
    full_name: str = idinfo.get("name", email)

    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token missing required fields",
        )

    # M-02: use email_hash lookup
    from app.core.pii_crypto import hash_email as _hash_email
    result = await db.execute(select(User).where(User.email_hash == _hash_email(email)))
    user = result.scalar_one_or_none()

    if user is None:
        # Auto-registration: requires a default agency to exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for this Google account. Please contact your administrator.",
        )

    if user.google_id is None:
        user.google_id = google_id
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    await _reject_if_agency_suspended(db, user)

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return _build_token_pair(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_platform_db),
) -> TokenResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        token_data = decode_token(payload.refresh_token)
    except JWTError:
        raise credentials_exception

    if token_data.get("type") != "refresh":
        raise credentials_exception

    jti = token_data.get("jti")
    if jti and jti in _token_blacklist:
        raise credentials_exception

    user_id_str: str | None = token_data.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return _build_token_pair(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
) -> None:
    """C-2 compliancefix：logout  when convertcurrent token add to blocklist，make itimmediatelyexpire。"""
    from app.core.security import revoke_token
    revoke_token(credentials.credentials)


from pydantic import BaseModel, Field  # noqa: E402


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)


@router.post("/accept-invite", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def accept_invite(
    payload: AcceptInviteRequest,
    db: AsyncSession = Depends(get_platform_db),
) -> TokenResponse:
    """Public endpoint: consume an invitation token and create the invited user."""
    import hashlib
    from app.core.pii_crypto import decrypt_pii, encrypt_pii, hash_email
    from app.models.invitation import UserInvitation

    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UserInvitation).where(UserInvitation.token_hash == token_hash)
    )
    invitation = result.scalar_one_or_none()
    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation",
        )

    email_plain = decrypt_pii(invitation.email_encrypted)
    email_hash = hash_email(email_plain)

    # Ensure no concurrent registration consumed this email.
    existing = await db.execute(select(User).where(User.email_hash == email_hash))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        agency_id=invitation.agency_id,
        client_id=invitation.client_id,
        email=encrypt_pii(email_plain),
        email_hash=email_hash,
        full_name=encrypt_pii(payload.full_name),
        hashed_password=get_password_hash(payload.password),
        role=invitation.role,
        is_active=True,
        last_login_at=now,
    )
    db.add(user)
    invitation.accepted_at = now
    await db.commit()
    await db.refresh(user)
    return _build_token_pair(user)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
    platform_db: AsyncSession = Depends(get_platform_db),
) -> UserResponse:
    # PR 3: include the user's effective permission codes so the
    # frontend can hide nav items / pages the user cannot access.
    from app.core.permissions import resolver
    from app.models.role import Role

    perms = await resolver.effective_permissions(
        platform_db, current_user.agency_id, current_user.role
    )
    role_row = (
        await platform_db.execute(
            select(Role.rank, Role.label).where(Role.code == current_user.role)
        )
    ).first()
    role_rank = int(role_row[0]) if role_row else 0
    role_label = str(role_row[1]) if role_row else current_user.role
    return UserResponse.from_user(
        current_user,
        permissions=list(perms),
        role_rank=role_rank,
        role_label=role_label,
    )
