-- F-12: Attribution Agent — attribution report tables
CREATE TABLE IF NOT EXISTS attribution_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL DEFAULT 'multi_touch',  -- multi_touch, last_click, first_click, custom
    date_range_start DATE,
    date_range_end DATE,
    channels JSONB DEFAULT '[]',
    model_config JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    insights TEXT,
    model_used VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attribution_reports_agency ON attribution_reports(agency_id);
CREATE INDEX IF NOT EXISTS idx_attribution_reports_created ON attribution_reports(created_at DESC);
