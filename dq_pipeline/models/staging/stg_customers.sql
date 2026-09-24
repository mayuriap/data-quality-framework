
-- models/staging/stg_customers.sql
-- Bronze layer — raw customers with DQ flags added
-- Materialised as VIEW — always shows latest raw data

{{
    config(
        materialized = 'view',
        schema       = 'bronze'
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

    -- DQ Flag 1: null email
    CASE
        WHEN email IS NULL THEN 'MISSING_EMAIL'
        WHEN email NOT LIKE '%@%.%' THEN 'INVALID_EMAIL'
        ELSE 'OK'
    END AS dq_email_flag,

    -- DQ Flag 2: null name
    CASE
        WHEN first_name IS NULL
          OR last_name IS NULL THEN 'MISSING_NAME'
        ELSE 'OK'
    END AS dq_name_flag,

    -- DQ Flag 3: invalid phone
    CASE
        WHEN phone IS NULL THEN 'MISSING_PHONE'
        WHEN phone NOT LIKE '+44%'
         AND phone NOT LIKE '07%' THEN 'INVALID_PHONE'
        ELSE 'OK'
    END AS dq_phone_flag,

    -- Audit columns
    CURRENT_TIMESTAMP AS ingestion_timestamp,
    'raw_customers'   AS source_table

FROM public.raw_customers