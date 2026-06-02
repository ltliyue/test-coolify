{{
  config(
    materialized = 'incremental',
    unique_key   = 'event_id',
    on_schema_change = 'sync_all_columns',
    tags = ['canonical', 'core']
  )
}}

/*
  Canonical Event Schema — all platformdata unifiedview
  This is the single source of truth for all Pillar queries; do NOT query staging tables directly.

  Data flow:
    Raw (Snowflake) → staging_{platform} → canonical_events → marts

  Key design principles:
  1. All platforms use a single semantic for "conversion" (normalized value)
  2. Cross-source attribution overlap is deduped here (user_id_hashed is the identity key)
  3. Each row represents a single marketing event
*/

with ga4 as (
    select * from {{ ref('stg_ga4') }}
    {% if is_incremental() %}
    where event_timestamp > (select max(event_timestamp) from {{ this }} where platform = 'ga4')
    {% endif %}
),

meta_ads as (
    select * from {{ ref('stg_meta_ads') }}
    {% if is_incremental() %}
    where event_timestamp > (select max(event_timestamp) from {{ this }} where platform = 'meta_ads')
    {% endif %}
),

hubspot as (
    select * from {{ ref('stg_hubspot') }}
    {% if is_incremental() %}
    where event_timestamp > (select max(event_timestamp) from {{ this }} where platform = 'hubspot')
    {% endif %}
),

unioned as (
    -- GA4 Events
    select
        {{ dbt_utils.generate_surrogate_key(['platform', 'source_event_id']) }} as event_id,
        event_timestamp,
        agency_id,
        client_id,
        'ga4'                   as platform,
        event_type,
        user_id_hashed,
        null::text              as campaign_id,
        null::text              as campaign_name,
        null::text              as ad_set_id,
        null::text              as ad_id,
        sessions                as impressions,
        clicks,
        conversions,
        0.0                     as spend_usd,
        channel,
        device_type,
        country                 as geography,
        source_event_id,
        raw_payload
    from ga4

    union all

    -- Meta Ads Events
    select
        {{ dbt_utils.generate_surrogate_key(['platform', 'source_event_id']) }} as event_id,
        event_timestamp,
        agency_id,
        client_id,
        'meta_ads'              as platform,
        'ad_impression'         as event_type,
        null::text              as user_id_hashed,
        campaign_id,
        campaign_name,
        ad_set_id,
        ad_id,
        impressions,
        link_clicks             as clicks,
        -- Normalize Meta conversions: purchase events → unified conversion
        purchase_conversions    as conversions,
        spend_usd,
        placement               as channel,
        null::text              as device_type,
        null::text              as geography,
        source_event_id,
        raw_payload
    from meta_ads

    union all

    -- HubSpot CRM Events
    select
        {{ dbt_utils.generate_surrogate_key(['platform', 'source_event_id']) }} as event_id,
        event_timestamp,
        agency_id,
        client_id,
        'hubspot'               as platform,
        deal_stage              as event_type,
        contact_id_hashed       as user_id_hashed,
        null::text              as campaign_id,
        null::text              as campaign_name,
        null::text              as ad_set_id,
        null::text              as ad_id,
        0                       as impressions,
        0                       as clicks,
        case when deal_stage = 'closedwon' then 1 else 0 end as conversions,
        deal_amount             as spend_usd,
        'crm'                   as channel,
        null::text              as device_type,
        null::text              as geography,
        source_event_id,
        raw_payload
    from hubspot
)

select * from unioned
