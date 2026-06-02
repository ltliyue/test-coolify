-- mart_campaign_unified: cross-platform unified campaign aggregate view
-- Supports Meta Ads / DV360 / StackAdapt

SELECT
    agency_id,
    client_id,
    date,
    'meta_ads' AS platform,
    campaign_id,
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    SUM(reach) AS reach,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
FROM {{ ref('stg_meta_ads') }}
GROUP BY 1, 2, 3, 4, 5, 6

UNION ALL

SELECT
    agency_id,
    client_id,
    date,
    'dv360' AS platform,
    campaign_id,
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    0 AS reach,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
FROM {{ ref('stg_dv360') }}
GROUP BY 1, 2, 3, 4, 5, 6

UNION ALL

SELECT
    agency_id,
    client_id,
    date,
    'stackadapt' AS platform,
    campaign_id,
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    0 AS reach,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
FROM {{ ref('stg_stackadapt') }}
GROUP BY 1, 2, 3, 4, 5, 6
