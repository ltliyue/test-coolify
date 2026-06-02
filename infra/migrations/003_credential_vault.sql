-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 003: credential vault
-- encrypted OAuth tokens + API keys, isolated per tenant
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE credential_type AS ENUM ('oauth', 'api_key', 'service_account');
CREATE TYPE credential_status AS ENUM ('valid', 'expired', 'error', 'revoked');

CREATE TABLE credentials (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID            NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id       UUID            REFERENCES clients(id) ON DELETE CASCADE,

    platform        TEXT            NOT NULL,   -- 'ga4' | 'meta_ads' | ...
    credential_type credential_type NOT NULL,
    status          credential_status NOT NULL DEFAULT 'valid',

    -- Fernet-encrypted JSON: { access_token, refresh_token, expires_at, ... }
    encrypted_data  TEXT            NOT NULL,

    -- Metadata (not encrypted)
    scopes          TEXT[],
    expires_at      TIMESTAMPTZ,        -- OAuth token expiry (plaintext, used by refresh scheduler)
    last_refreshed_at TIMESTAMPTZ,
    error_message   TEXT,

    created_by      UUID            REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    UNIQUE(agency_id, COALESCE(client_id, '00000000-0000-0000-0000-000000000000'::UUID), platform)
);

CREATE INDEX idx_credentials_agency   ON credentials(agency_id);
CREATE INDEX idx_credentials_platform ON credentials(agency_id, platform);
CREATE INDEX idx_credentials_expires  ON credentials(expires_at) WHERE status = 'valid';

CREATE TRIGGER credentials_updated_at
    BEFORE UPDATE ON credentials
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
