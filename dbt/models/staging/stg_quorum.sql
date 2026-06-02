SELECT
    agency_id,
    client_id,
    date,
    audience_id,
    audience_name,
    category,
    reach,
    engagement_score
FROM {{ source('receptiviq', 'raw_quorum') }}
