-- f21-persona-audience-export: persona → ad-platform audience export records
CREATE TABLE IF NOT EXISTS audience_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    external_audience_id VARCHAR(255),
    targeting_spec JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_audience_export_agency ON audience_exports(agency_id);
CREATE INDEX idx_audience_export_persona ON audience_exports(persona_id);
CREATE INDEX idx_audience_export_status ON audience_exports(status) WHERE status IN ('pending', 'processing');
