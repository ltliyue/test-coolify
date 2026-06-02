-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 006: platform integrations
-- integrations + sync_logs
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TYPE integration_platform AS ENUM (
    'ga4', 'meta_ads', 'hubspot', 'tiktok_ads',
    'dv360', 'stackadapt', 'leadrx', 'liveramp', 'quorum',
    'canva', 'adobe_firefly', 'icon_app'
);
CREATE TYPE auth_type        AS ENUM ('oauth', 'api_key', 'service_account');
CREATE TYPE integration_status AS ENUM ('disconnected', 'connected', 'expired', 'error');
CREATE TYPE sync_status      AS ENUM ('pending', 'running', 'success', 'failed', 'cancelled');

CREATE TABLE integrations (
    id              UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID                NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id       UUID                REFERENCES clients(id) ON DELETE CASCADE,

    platform        integration_platform NOT NULL,
    auth_type       auth_type           NOT NULL,
    status          integration_status  NOT NULL DEFAULT 'disconnected',

    -- Credential ID (FK to credentials table; do not store token directly)
    credential_id   UUID                REFERENCES credentials(id) ON DELETE SET NULL,

    -- Sync config
    sync_schedule   JSONB,              -- {"type": "daily", "hour": 2}
    config          JSONB,              -- platform-specific config (e.g. GA4 property_id)

    last_sync_at    TIMESTAMPTZ,
    current_task_id TEXT,               -- Celery/Airflow task ID
    error_message   TEXT,
    connected_at    TIMESTAMPTZ,

    created_by      UUID                REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),

    UNIQUE(agency_id, COALESCE(client_id, '00000000-0000-0000-0000-000000000000'::UUID), platform)
);

CREATE INDEX idx_integrations_agency   ON integrations(agency_id);
CREATE INDEX idx_integrations_status   ON integrations(agency_id, status);
CREATE INDEX idx_integrations_platform ON integrations(platform);

CREATE TRIGGER integrations_updated_at
    BEFORE UPDATE ON integrations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Sync log ─────────────────────────────────────────────────────────────────
CREATE TABLE sync_logs (
    id              BIGSERIAL   PRIMARY KEY,
    integration_id  UUID        NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,

    task_id         TEXT,
    status          sync_status NOT NULL DEFAULT 'pending',
    triggered_by    TEXT        NOT NULL DEFAULT 'schedule',  -- 'schedule' | 'manual' | 'webhook'

    records_fetched INTEGER     NOT NULL DEFAULT 0,
    records_written INTEGER     NOT NULL DEFAULT 0,
    error_message   TEXT,
    metadata        JSONB,

    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_sync_logs_integration ON sync_logs(integration_id, started_at DESC);
CREATE INDEX idx_sync_logs_agency      ON sync_logs(agency_id, started_at DESC);
