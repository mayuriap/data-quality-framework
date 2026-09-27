-- tests/staging/assert_customer_bronze_matches_raw.sql
-- Verifies customer Bronze count matches raw count
-- Bronze is a view so should always equal raw count
-- Test PASSES when ZERO rows returned

WITH raw_count AS (
    SELECT COUNT(*) AS cnt
    FROM public.raw_customers
),
bronze_count AS (
    SELECT COUNT(*) AS cnt
    FROM public_bronze.stg_customers
)
SELECT
    raw_count.cnt    AS raw_count,
    bronze_count.cnt AS bronze_count,
    'CUSTOMER_COUNT_MISMATCH' AS issue
FROM raw_count, bronze_count
WHERE raw_count.cnt != bronze_count.cnt