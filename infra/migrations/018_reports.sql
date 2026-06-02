-- f22-pdf-reports: report schedules + generation history
CREATE TABLE IF NOT EXISTS report_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    schedule_name VARCHAR(255) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    recipients_encrypted TEXT,
    metrics_config JSONB,
    brand_config_override JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_sent_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_report_schedule_agency ON report_schedules(agency_id);
CREATE INDEX idx_report_schedule_active ON report_schedules(next_run_at) WHERE is_active = TRUE;

CREATE TABLE IF NOT EXISTS report_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    schedule_id UUID REFERENCES report_schedules(id) ON DELETE SET NULL,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    report_type VARCHAR(50) NOT NULL DEFAULT 'campaign_performance',
    file_path VARCHAR(500),
    file_size_bytes INTEGER,
    recipients_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_report_history_agency ON report_history(agency_id);
CREATE INDEX idx_report_history_status ON report_history(status) WHERE status IN ('pending', 'generating');
