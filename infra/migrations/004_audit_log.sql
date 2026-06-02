-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 004: audit log
-- Record every data access, AI query and data-mutation operation
-- GDPR requirement: immutable (INSERT only, no UPDATE/DELETE privileges)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE audit_logs (
    id              BIGSERIAL   PRIMARY KEY,
    agency_id       UUID        REFERENCES agencies(id) ON DELETE SET NULL,
    client_id       UUID        REFERENCES clients(id) ON DELETE SET NULL,
    user_id         UUID        REFERENCES users(id) ON DELETE SET NULL,

    -- Operation info
    action          TEXT        NOT NULL,   -- 'read' | 'create' | 'update' | 'delete' | 'ai_query' | 'export' | 'dsar'
    resource_type   TEXT        NOT NULL,   -- 'credential' | 'persona' | 'creative' | 'report' | 'user_data' ...
    resource_id     TEXT,                   -- ID of the resource being operated on

    -- Request context
    ip_address      INET,
    user_agent      TEXT,
    request_path    TEXT,
    request_method  TEXT,

    -- Result
    status_code     INTEGER,
    success         BOOLEAN     NOT NULL DEFAULT true,
    error_message   TEXT,

    -- PHI/PII flags (HIPAA requires PHI-access marking)
    contains_phi    BOOLEAN     NOT NULL DEFAULT false,
    data_level      TEXT,       -- 'public' | 'internal' | 'confidential_pii' | 'restricted_phi'

    -- Metadata (extra context such as filter conditions)
    metadata        JSONB,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Forbid UPDATE and DELETE (enforced by DB role privileges; trigger added here as defence)
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable. Modification is not allowed.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- indexes
CREATE INDEX idx_audit_agency_time ON audit_logs(agency_id, created_at DESC);
CREATE INDEX idx_audit_user        ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_action      ON audit_logs(action, resource_type);
CREATE INDEX idx_audit_phi         ON audit_logs(agency_id, created_at) WHERE contains_phi = true;
