-- f19-campaigns: budget configs & alerting rules
CREATE TABLE IF NOT EXISTS campaign_budget_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    platform VARCHAR(50) NOT NULL,
    external_campaign_id VARCHAR(255) NOT NULL,
    campaign_name VARCHAR(500),
    daily_budget NUMERIC(12, 2),
    total_budget NUMERIC(12, 2),
    pacing_alert_threshold FLOAT NOT NULL DEFAULT 0.15,
    alert_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_budget_config UNIQUE (agency_id, platform, external_campaign_id)
);

CREATE INDEX idx_budget_config_agency ON campaign_budget_configs(agency_id);
CREATE INDEX idx_budget_config_alert ON campaign_budget_configs(alert_enabled) WHERE alert_enabled = TRUE;
