SELECT
    agency_id,
    client_id,
    date,
    segment_id,
    segment_name,
    match_type,
    matched_count,
    total_count,
    match_rate
FROM {{ source('receptiviq', 'raw_liveramp') }}
