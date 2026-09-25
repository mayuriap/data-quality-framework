-- Verifies transaction Bronze count matches raw
WITH raw_count AS (
    SELECT COUNT(*) AS cnt
    FROM public.raw_transactions
),
bronze_count AS (
    SELECT COUNT(*) AS cnt
    FROM public_bronze.stg_transactions
)
SELECT
    raw_count.cnt    AS raw_count,
    bronze_count.cnt AS bronze_count,
    'TRANSACTION_COUNT_MISMATCH' AS issue
FROM raw_count, bronze_count
WHERE raw_count.cnt != bronze_count.cnt