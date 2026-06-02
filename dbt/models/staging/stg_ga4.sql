-- GA4 Staging Model
-- Normalize raw_ga4_events to canonical fields

{{ config(materialized='view') }}

SELECT
    agency_id,
    client_id,
    CAST(date AS DATE)              AS date,
    property_id                     AS account_id,
    'ga4'                           AS platform,
    NULL                            AS campaign_id,
    NULL                            AS campaign_name,
    sessions                        AS impressions,  -- GA4 uses sessions as a proxy for impressions
    users                           AS users,
    new_users,
    page_views,
    ROUND(bounce_rate * 100, 2)     AS bounce_rate_pct,
    avg_session_duration,
    goal_completions                AS conversions,
    0.0                             AS spend,
    ingested_at
FROM {{ source('raw', 'raw_ga4_events') }}
WHERE agency_id IS NOT NULL
  AND date IS NOT NULL
