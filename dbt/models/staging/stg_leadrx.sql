SELECT
    agency_id,
    client_id,
    date,
    conversion_id,
    touchpoint_channel,
    touchpoint_source,
    attribution_model,
    attribution_weight,
    conversion_value
FROM {{ source('receptiviq', 'raw_leadrx') }}
