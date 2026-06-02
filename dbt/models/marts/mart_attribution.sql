-- Attribution Mart
-- Multi-touch attribution aggregate table, consumed by Attribution Agent
-- Aggregate by (channel, campaign) and compute per-channel contribution

{{ config(materialized='table') }}

WITH channel_metrics AS (
    SELECT
        agency_id,
        client_id,
        platform                    AS channel,
        campaign_id,
        campaign_name,
        DATE_TRUNC('week', date)    AS week,
        SUM(impressions)            AS impressions,
        SUM(clicks)                 AS clicks,
        SUM(spend)                  AS spend,
        SUM(conversions)            AS conversions,
        SUM(conversion_value)       AS conversion_value
    FROM {{ ref('canonical_events') }}
    WHERE date >= DATEADD('day', -90, CURRENT_DATE)
    GROUP BY 1, 2, 3, 4, 5, 6
),

channel_totals AS (
    SELECT
        agency_id,
        client_id,
        week,
        SUM(conversions)        AS total_conversions,
        SUM(spend)              AS total_spend,
        SUM(conversion_value)   AS total_value
    FROM channel_metrics
    GROUP BY 1, 2, 3
)

SELECT
    cm.agency_id,
    cm.client_id,
    cm.channel,
    cm.campaign_id,
    cm.campaign_name,
    cm.week,
    cm.impressions,
    cm.clicks,
    cm.spend,
    cm.conversions,
    cm.conversion_value,
    -- Attribution metrics
    CASE WHEN cm.clicks > 0
         THEN ROUND(cm.spend / cm.clicks, 4)
         ELSE 0 END                             AS cpc,
    CASE WHEN cm.spend > 0
         THEN ROUND(cm.conversion_value / cm.spend, 4)
         ELSE 0 END                             AS roas,
    CASE WHEN cm.impressions > 0
         THEN ROUND(cm.conversions * 1.0 / cm.impressions * 1000, 4)
         ELSE 0 END                             AS conv_per_mille,
    -- Channel contribution (simplified last-touch by conversion share)
    CASE WHEN ct.total_conversions > 0
         THEN ROUND(cm.conversions * 100.0 / ct.total_conversions, 2)
         ELSE 0 END                             AS conversion_share_pct,
    CASE WHEN ct.total_spend > 0
         THEN ROUND(cm.spend * 100.0 / ct.total_spend, 2)
         ELSE 0 END                             AS spend_share_pct
FROM channel_metrics cm
LEFT JOIN channel_totals ct
    ON cm.agency_id = ct.agency_id
    AND cm.client_id = ct.client_id
    AND cm.week = ct.week
