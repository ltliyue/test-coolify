-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 002: authn / authz
-- users, user_sessions, token_blacklist
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('agency_admin', 'agency_ops', 'client_viewer');

CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id       UUID        REFERENCES clients(id) ON DELETE SET NULL,  -- NULL = agency staff

    email           TEXT        NOT NULL UNIQUE,
    hashed_password TEXT,                   -- NULL if Google-only login
    google_id       TEXT        UNIQUE,

    full_name       TEXT        NOT NULL,
    role            user_role   NOT NULL DEFAULT 'agency_ops',
    is_active       BOOLEAN     NOT NULL DEFAULT true,
    last_login_at   TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_agency  ON users(agency_id);
CREATE INDEX idx_users_email   ON users(email);
CREATE INDEX idx_users_google  ON users(google_id) WHERE google_id IS NOT NULL;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Token blocklist (used by logout / forced sign-out) ────────────────────────────────────
CREATE TABLE token_blacklist (
    jti         TEXT        PRIMARY KEY,   -- JWT ID (jti claim)
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Expired tokens can be cleaned up periodically
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);
