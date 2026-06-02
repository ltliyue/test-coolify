SELECT
    agency_id,
    client_id,
    date,
    campaign_id,
    campaign_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(spend) AS spend,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
FROM {{ source('receptiviq', 'raw_dv360') }}
GROUP BY 1, 2, 3, 4, 5
