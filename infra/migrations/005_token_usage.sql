-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 005: token usage tracking
-- Track each LLM call's token consumption per tenant; enables future billing models
-- Source: ReceptivIQ Agent Service design
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE token_usage (
    id                  BIGSERIAL   PRIMARY KEY,
    agency_id           UUID        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    client_id           UUID        REFERENCES clients(id) ON DELETE SET NULL,
    user_id             UUID        REFERENCES users(id) ON DELETE SET NULL,
    request_id          TEXT,
    agent_name          TEXT,
    agent_type          TEXT,
    model               TEXT        NOT NULL,
    prompt_tokens       INTEGER     NOT NULL DEFAULT 0,
    completion_tokens   INTEGER     NOT NULL DEFAULT 0,
    total_tokens        INTEGER     NOT NULL DEFAULT 0,
    estimated_cost_usd  NUMERIC(10,6),
    cost_usd            NUMERIC(10,6),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Aggregate by (agency, month) for billing reports
CREATE INDEX idx_token_usage_agency_month
    ON token_usage(agency_id, date_trunc('month', created_at));

-- Per-client queries
CREATE INDEX idx_token_usage_client
    ON token_usage(client_id, created_at);

-- ── Monthly usage view (fast queries) ───────────────────────────────────────────────────
CREATE VIEW v_token_usage_monthly AS
SELECT
    agency_id,
    client_id,
    agent_name,
    model,
    date_trunc('month', created_at)     AS month,
    SUM(prompt_tokens)                  AS total_prompt_tokens,
    SUM(completion_tokens)              AS total_completion_tokens,
    SUM(total_tokens)                   AS total_tokens,
    SUM(COALESCE(cost_usd, estimated_cost_usd, 0)) AS total_cost_usd,
    COUNT(*)                            AS request_count
FROM token_usage
GROUP BY 1, 2, 3, 4, 5;
