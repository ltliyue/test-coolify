-- Campaign Performance Mart
-- Aggregate performance metrics by campaign, consumed by Attribution Agent

{{ config(materialized='table') }}

SELECT
    agency_id,
    client_id,
    platform,
    campaign_id,
    campaign_name,
    DATE_TRUNC('month', date)   AS month,
    SUM(impressions)            AS total_impressions,
    SUM(clicks)                 AS total_clicks,
    SUM(spend)                  AS total_spend,
    SUM(conversions)            AS total_conversions,
    SUM(conversion_value)       AS total_conversion_value,
    CASE WHEN SUM(impressions) > 0
         THEN ROUND(SUM(clicks) * 100.0 / SUM(impressions), 4)
         ELSE 0 END             AS avg_ctr,
    CASE WHEN SUM(clicks) > 0
         THEN ROUND(SUM(spend) / SUM(clicks), 4)
         ELSE 0 END             AS avg_cpc,
    CASE WHEN SUM(spend) > 0
         THEN ROUND(SUM(conversion_value) / SUM(spend), 4)
         ELSE 0 END             AS avg_roas
FROM {{ ref('canonical_events') }}
WHERE campaign_id IS NOT NULL
GROUP BY 1, 2, 3, 4, 5, 6
