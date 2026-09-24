-- models/intermediate/int_transactions.sql
-- Silver layer — cleaned transactions
-- Only records with all DQ flags = OK pass through
-- Orphan transactions removed — no matching customer
-- Materialised as incremental table

{{
    config(
        materialized = 'incremental',
        schema       = 'silver',
        unique_key   = 'transaction_id'
    )
}}

SELECT
    t.transaction_id,
    t.customer_id,
    t.amount,
    t.currency,
    t.status,
    t.transaction_date,
    t.settlement_date,
    t.ingestion_timestamp

FROM {{ ref('stg_transactions') }} t

-- Remove orphan transactions
-- Only keep transactions with valid customer
INNER JOIN {{ ref('stg_customers') }} c
    ON t.customer_id = c.customer_id

WHERE
    t.dq_amount_flag   = 'OK'
    AND t.dq_currency_flag = 'OK'
    AND t.dq_date_flag     = 'OK'
    AND t.dq_status_flag   = 'OK'
    AND c.dq_email_flag    = 'OK'
    AND c.dq_name_flag     = 'OK'
    AND c.dq_phone_flag    = 'OK'

{% if is_incremental() %}
    AND t.ingestion_timestamp > (
        SELECT MAX(ingestion_timestamp)
        FROM {{ this }}
    )
{% endif %}