SELECT
    CAST(transaction_id AS VARCHAR) AS record_id,
    CAST(amount AS VARCHAR)         AS value,
    'NEGATIVE_AMOUNT_IN_SILVER'     AS issue
FROM public_silver.int_transactions
WHERE amount < 0

UNION ALL

-- Check no invalid currencies
SELECT
    CAST(transaction_id AS VARCHAR) AS record_id,
    CAST(currency AS VARCHAR)       AS value,
    'INVALID_CURRENCY_IN_SILVER'    AS issue
FROM public_silver.int_transactions
WHERE currency NOT IN ('GBP','USD','EUR','JPY','CHF')

UNION ALL

-- Check no future dates
SELECT
    CAST(transaction_id AS VARCHAR)  AS record_id,
    CAST(transaction_date AS VARCHAR) AS value,
    'FUTURE_DATE_IN_SILVER'          AS issue
FROM public_silver.int_transactions
WHERE transaction_date > CURRENT_DATE

UNION ALL

-- Check no null amounts
SELECT
    CAST(transaction_id AS VARCHAR) AS record_id,
    CAST(amount AS VARCHAR)         AS value,
    'NULL_AMOUNT_IN_SILVER'         AS issue
FROM public_silver.int_transactions
WHERE amount IS NULL