-- models/intermediate/int_customers.sql
-- Silver layer — cleaned customers
-- Only records with all DQ flags = OK pass through
-- Materialised as incremental table

{{
    config(
        materialized = 'incremental',
        schema       = 'silver',
        unique_key   = 'customer_id'
    )
}}

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    segment,
    created_date,
    ingestion_timestamp

FROM {{ ref('stg_customers') }}

WHERE
    dq_email_flag = 'OK'
    AND dq_name_flag  = 'OK'
    AND dq_phone_flag = 'OK'

{% if is_incremental() %}
    AND ingestion_timestamp > (
        SELECT MAX(ingestion_timestamp)
        FROM {{ this }}
    )
{% endif %}