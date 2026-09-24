-- models/staging/stg_transactions.sql
-- Bronze layer — raw transactions with DQ flags added
-- Materialised as VIEW — always shows latest raw data

{{
    config(
        materialized = 'view',
        schema       = 'bronze'
    )
}}

SELECT
    transaction_id,
    customer_id,
    amount,
    currency,
    status,
    transaction_date,
    settlement_date,

    -- DQ Flag 1: amount issues
    CASE
        WHEN amount IS NULL        THEN 'MISSING_AMOUNT'
        WHEN amount < 0            THEN 'NEGATIVE_AMOUNT'
        WHEN amount > 999999.99    THEN 'AMOUNT_TOO_LARGE'
        ELSE 'OK'
    END AS dq_amount_flag,

    -- DQ Flag 2: invalid currency
    CASE
        WHEN currency IS NULL THEN 'MISSING_CURRENCY'
        WHEN currency NOT IN (
            'GBP','USD','EUR','JPY','CHF'
        ) THEN 'INVALID_CURRENCY'
        ELSE 'OK'
    END AS dq_currency_flag,

    -- DQ Flag 3: future date
    CASE
        WHEN transaction_date > CURRENT_DATE THEN 'FUTURE_DATE'
        ELSE 'OK'
    END AS dq_date_flag,

    -- DQ Flag 4: invalid status
    CASE
        WHEN status NOT IN (
            'COMPLETED','PENDING','FAILED'
        ) THEN 'INVALID_STATUS'
        ELSE 'OK'
    END AS dq_status_flag,

    -- Audit columns
    CURRENT_TIMESTAMP AS ingestion_timestamp,
    'raw_transactions' AS source_table

FROM public.raw_transactions