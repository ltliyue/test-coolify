-- HubSpot Staging Model

{{ config(materialized='view') }}

SELECT
    agency_id,
    client_id,
    contact_id,
    -- PII de-identified at the warehouse layer (email already anonymized in ETL)
    email,
    first_name,
    last_name,
    lifecycle_stage,
    lead_source,
    CAST(create_date AS DATE)   AS create_date,
    ingested_at
FROM {{ source('raw', 'raw_hubspot_contacts') }}
WHERE agency_id IS NOT NULL
