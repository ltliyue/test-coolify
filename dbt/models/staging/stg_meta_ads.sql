-- Meta Ads Staging Model

{{ config(materialized='view') }}

SELECT
    agency_id,
    client_id,
    CAST(date AS DATE)          AS date,
    account_id,
    'meta_ads'                  AS platform,
    campaign_id,
    campaign_name,
    ad_set_id,
    ad_set_name,
    ad_id,
    impressions,
    clicks,
    CAST(spend AS FLOAT)        AS spend,
    reach,
    CASE WHEN impressions > 0 THEN ROUND(clicks * 100.0 / impressions, 4) ELSE 0 END AS ctr,
    CASE WHEN clicks > 0 THEN ROUND(spend / clicks, 4) ELSE 0 END AS cpc,
    CASE WHEN impressions > 0 THEN ROUND(spend * 1000.0 / impressions, 4) ELSE 0 END AS cpm,
    conversions,
    conversion_value,
    CASE WHEN spend > 0 THEN ROUND(conversion_value / spend, 4) ELSE 0 END AS roas,
    ingested_at
FROM {{ source('raw', 'raw_meta_ads') }}
WHERE agency_id IS NOT NULL
  AND date IS NOT NULL
