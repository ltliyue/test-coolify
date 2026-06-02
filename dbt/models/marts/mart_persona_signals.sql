-- Persona Signals Mart
-- Aggregate audience signals, consumed by Persona Agent

{{ config(materialized='table') }}

SELECT
    agency_id,
    client_id,
    platform,
    DATE_TRUNC('week', date)    AS week,
    SUM(impressions)            AS weekly_impressions,
    SUM(clicks)                 AS weekly_clicks,
    SUM(conversions)            AS weekly_conversions,
    SUM(spend)                  AS weekly_spend,
    CASE WHEN SUM(impressions) > 0
         THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 4)
         ELSE 0 END             AS engagement_rate
FROM {{ ref('canonical_events') }}
GROUP BY 1, 2, 3, 4
