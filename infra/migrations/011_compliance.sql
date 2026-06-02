-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 011: compliance core tables
-- Covers: GDPR · CCPA · HIPAA
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Enum types ──────────────────────────────────────────────────────────────────
CREATE TYPE dsar_type      AS ENUM ('access', 'delete', 'export', 'rectify', 'restrict', 'portability');
CREATE TYPE dsar_status    AS ENUM ('pending', 'in_progress', 'completed', 'rejected', 'appealed');
CREATE TYPE regulation     AS ENUM ('gdpr', 'ccpa', 'hipaa');
CREATE TYPE consent_purpose AS ENUM ('analytics', 'marketing', 'cross_device', 'data_sharing', 'ai_processing');
CREATE TYPE breach_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE data_level     AS ENUM ('public', 'internal', 'confidential_pii', 'restricted_phi');
CREATE TYPE baa_status     AS ENUM ('active', 'expired', 'pending_renewal', 'terminated');

-- ── Consent records (GDPR core + CCPA Do Not Sell)──────────────────────────────────
CREATE TABLE consent_records (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id       UUID        REFERENCES clients(id) ON DELETE CASCADE,

    -- Data-subject identifier (pseudonymized: store hash, not raw value)
    subject_hash    TEXT        NOT NULL,   -- SHA-256(email + tenant_salt)
    subject_email   TEXT,                   -- Decrypted temporarily during DSAR handling; otherwise NULL

    purpose         consent_purpose NOT NULL,
    granted         BOOLEAN     NOT NULL,
    do_not_sell     BOOLEAN     NOT NULL DEFAULT false, -- CCPA-specific

    -- Evidence columns (GDPR requires proof of valid consent)
    consent_text    TEXT        NOT NULL,   -- Snapshot of the text shown at consent time
    consent_version TEXT        NOT NULL,   -- Privacy policy version
    ip_address      INET,                   -- IP at consent time (anonymized: only first 24 bits kept)
    user_agent      TEXT,
    source          TEXT,                   -- 'web_form' | 'api' | 'import'

    granted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    withdrawn_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,            -- Some consents have an expiry

    UNIQUE(agency_id, subject_hash, purpose)  -- Only one valid record per (subject, purpose)
);

CREATE INDEX idx_consent_agency     ON consent_records(agency_id, purpose, granted);
CREATE INDEX idx_consent_subject    ON consent_records(subject_hash);
CREATE INDEX idx_consent_donotsell  ON consent_records(agency_id, do_not_sell) WHERE do_not_sell = true;

-- ── DSAR (Data Subject Access Request)─────────────────────────────────────────────────
CREATE TABLE dsar_requests (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    request_type    dsar_type   NOT NULL,
    regulation      regulation  NOT NULL,

    -- Requester info (temporarily stored during DSAR flow; cleared on completion)
    subject_email   TEXT        NOT NULL,
    subject_name    TEXT,
    verification_token TEXT,               -- Identity-verification token (48h TTL)
    verified_at     TIMESTAMPTZ,

    status          dsar_status NOT NULL DEFAULT 'pending',

    -- SLA: GDPR=30d, CCPA=45d, HIPAA=30d
    due_date        TIMESTAMPTZ NOT NULL,  -- Computed and written by the application layer
    extended_due_date TIMESTAMPTZ,         -- CCPA permits a 45-day extension (notification required)

    -- Processing record
    assigned_to     UUID,                  -- user_id of the assignee
    response_path   TEXT,                  -- MinIO path of the export file (encrypted at rest)
    rejection_reason TEXT,
    notes           TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dsar_agency_status ON dsar_requests(agency_id, status);
CREATE INDEX idx_dsar_due           ON dsar_requests(due_date) WHERE status NOT IN ('completed', 'rejected');

CREATE TRIGGER dsar_updated_at
    BEFORE UPDATE ON dsar_requests
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Data retention policies ───────────────────────────────────────────────────────────
CREATE TABLE retention_policies (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        REFERENCES agencies(id) ON DELETE CASCADE,  -- NULL = global default

    data_type       TEXT        NOT NULL,   -- 'session_logs' | 'pii' | 'phi' | 'audit_logs' | ...
    jurisdiction    TEXT        NOT NULL DEFAULT 'global',  -- 'eu' | 'us_ca' | 'us' | 'global'
    data_level      data_level  NOT NULL,
    retention_days  INTEGER     NOT NULL,   -- 0 = retain forever (use with caution)
    purge_strategy  TEXT        NOT NULL DEFAULT 'anonymize', -- 'delete' | 'anonymize' | 'archive'

    -- Compliance basis
    legal_basis     TEXT,                   -- GDPR lawful-basis
    regulation_ref  TEXT,                   -- Regulation clause reference

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(COALESCE(agency_id, '00000000-0000-0000-0000-000000000000'::UUID), data_type, jurisdiction)
);

-- Insert global default retention policy (the strictest across the three regulations)
INSERT INTO retention_policies (agency_id, data_type, jurisdiction, data_level, retention_days, purge_strategy, legal_basis) VALUES
(NULL, 'session_logs',      'global', 'confidential_pii',  90,   'anonymize', 'Legitimate interest'),
(NULL, 'audit_logs',        'global', 'internal',          2190, 'archive',   'Legal obligation (HIPAA 6yr, GDPR 3yr)'),
(NULL, 'pii_records',       'global', 'confidential_pii',  null, 'anonymize', 'Contract performance'),  -- contract term + 30 days (computed by the application layer)
(NULL, 'phi_records',       'global', 'restricted_phi',    2190, 'archive',   'HIPAA §164.530(j) - 6 year retention'),
(NULL, 'financial_records', 'global', 'confidential_pii',  2555, 'archive',   'Legal obligation (7 years)'),
(NULL, 'system_logs',       'global', 'internal',          365,  'delete',    'Operational necessity'),
(NULL, 'marketing_data',    'global', 'confidential_pii',  1095, 'anonymize', 'Legitimate interest');

-- ── Breach incident log ───────────────────────────────────────────────────────────
CREATE TABLE breach_incidents (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id           UUID        REFERENCES agencies(id) ON DELETE SET NULL,
    severity            breach_severity NOT NULL,
    description         TEXT        NOT NULL,

    -- Impact scope
    affected_records    INTEGER     NOT NULL DEFAULT 0,
    affected_users      INTEGER     NOT NULL DEFAULT 0,
    affected_data_types TEXT[]      NOT NULL DEFAULT '{}',  -- ['pii', 'phi', ...]
    data_levels         data_level[] NOT NULL DEFAULT '{}',

    -- Detection & notification timeline
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    contained_at        TIMESTAMPTZ,

    -- GDPR: notify supervisory authority (DPA) within 72 hours
    gdpr_notification_due   TIMESTAMPTZ GENERATED ALWAYS AS (detected_at + INTERVAL '72 hours') STORED,
    gdpr_dpa_notified_at    TIMESTAMPTZ,
    gdpr_subjects_notified_at TIMESTAMPTZ,

    -- CCPA: notify affected California residents
    ccpa_notified_at    TIMESTAMPTZ,

    -- HIPAA: notify HHS within 60 days; >500 affected requires media notification
    hipaa_notification_due  TIMESTAMPTZ GENERATED ALWAYS AS (detected_at + INTERVAL '60 days') STORED,
    hipaa_hhs_notified_at   TIMESTAMPTZ,
    hipaa_media_notified_at TIMESTAMPTZ,  -- Only when >500 individuals are affected

    status              TEXT        NOT NULL DEFAULT 'open',  -- 'open'|'contained'|'resolved'
    resolution_notes    TEXT,
    root_cause          TEXT,
    remediation_actions TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_breach_agency      ON breach_incidents(agency_id, detected_at);
CREATE INDEX idx_breach_open        ON breach_incidents(status) WHERE status != 'resolved';

-- ── BAA tracking (HIPAA mandatory)───────────────────────────────────────────────
CREATE TABLE business_associate_agreements (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    vendor_name     TEXT        NOT NULL,
    vendor_type     TEXT        NOT NULL,   -- 'cloud_storage' | 'analytics' | 'ai_provider' | 'etl'
    covers_phi      BOOLEAN     NOT NULL DEFAULT false,
    signed_at       TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ,
    document_path   TEXT,                   -- MinIO path (encrypted at rest)
    status          baa_status  NOT NULL DEFAULT 'active',
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── DPA (Data Processing Agreement) tracking (GDPR requirement)──────────────────────────────────
CREATE TABLE data_processing_agreements (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    processor_name  TEXT        NOT NULL,   -- Data processor name (e.g. Snowflake Inc.)
    processing_purposes TEXT[] NOT NULL DEFAULT '{}',
    transfer_mechanism TEXT,               -- 'scc' | 'dpf' | 'adequacy' | 'bcr'
    data_residency  TEXT[],               -- ['eu-west-1', 'us-east-1']
    signed_at       TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ,
    document_path   TEXT,
    status          TEXT        NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Data-flow map (input for GDPR DPIA)──────────────────────────────────────────
CREATE TABLE data_flow_mappings (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id       UUID        REFERENCES agencies(id) ON DELETE CASCADE,
    source_system   TEXT        NOT NULL,   -- 'ga4' | 'meta_ads' | ...
    destination     TEXT        NOT NULL,   -- 'snowflake' | 'postgresql' | ...
    data_types      TEXT[]      NOT NULL,
    data_level      data_level  NOT NULL,
    transfer_type   TEXT        NOT NULL,   -- 'internal' | 'cross_border' | 'third_party'
    encryption      TEXT        NOT NULL,   -- 'tls_1_3' | 'aes_256' | 'tls+aes'
    legal_basis     TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
