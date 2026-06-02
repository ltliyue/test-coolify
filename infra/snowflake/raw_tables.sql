-- Snowflake RAW-tier table definitions
-- Schema parity with the DuckDB dev mode
USE DATABASE RECEPTIVIQ;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS raw_ga4_events (
    agency_id       VARCHAR     NOT NULL,
    client_id       VARCHAR,
    date            DATE        NOT NULL,
    property_id     VARCHAR     NOT NULL,
    session_id      VARCHAR,
    event_name      VARCHAR,
    user_pseudo_id  VARCHAR,    -- Note: anonymized via hash_identifier before entering the warehouse
    sessions        INTEGER,
    users           INTEGER,
    new_users       INTEGER,
    page_views      INTEGER,
    bounce_rate     FLOAT,
    avg_session_duration FLOAT,
    goal_completions INTEGER,
    raw_json        VARIANT,
    ingested_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS raw_meta_ads (
    agency_id       VARCHAR     NOT NULL,
    client_id       VARCHAR,
    date            DATE        NOT NULL,
    account_id      VARCHAR     NOT NULL,
    campaign_id     VARCHAR,
    campaign_name   VARCHAR,
    ad_set_id       VARCHAR,
    ad_set_name     VARCHAR,
    ad_id           VARCHAR,
    impressions     INTEGER,
    clicks          INTEGER,
    spend           FLOAT,
    reach           INTEGER,
    conversions     INTEGER,
    conversion_value FLOAT,
    raw_json        VARIANT,
    ingested_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS raw_hubspot_contacts (
    agency_id       VARCHAR     NOT NULL,
    client_id       VARCHAR,
    contact_id      VARCHAR     NOT NULL,
    email           VARCHAR,    -- Note: anonymized via hash_identifier before entering the warehouse
    first_name      VARCHAR,    -- Note: anonymized via hash_identifier before entering the warehouse
    last_name       VARCHAR,    -- Note: anonymized via hash_identifier before entering the warehouse
    lifecycle_stage VARCHAR,
    lead_source     VARCHAR,
    create_date     DATE,
    raw_json        VARIANT,
    ingested_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS etl_sync_state (
    agency_id       VARCHAR     NOT NULL,
    integration_id  VARCHAR     NOT NULL,
    platform        VARCHAR     NOT NULL,
    last_sync_at    TIMESTAMP_NTZ,
    last_cursor     VARCHAR,
    records_written INTEGER     DEFAULT 0,
    PRIMARY KEY (agency_id, integration_id)
);

-- Compliance: data-classification labels
COMMENT ON TABLE raw_ga4_events IS 'Data Level: L1 (Internal) — Anonymized GA4 behavioral data';
COMMENT ON TABLE raw_meta_ads IS 'Data Level: L0 (Public) — Ad-delivery aggregates, no PII';
COMMENT ON TABLE raw_hubspot_contacts IS 'Data Level: L1 (Internal) — Contact data anonymized via hash_identifier';
