-- tests/marts/assert_gold_matches_silver_totals.sql
-- Verifies Gold daily summary totals match Silver source
-- This catches aggregation bugs like FX double conversion
-- Test PASSES when ZERO rows returned

WITH silver_totals AS (
    SELECT
        transaction_date,
        currency,
        COUNT(*)    AS tx_count,
        SUM(amount) AS total_amount
    FROM public_silver.int_transactions
    GROUP BY transaction_date, currency
),
gold_totals AS (
    SELECT
        transaction_date,
        currency,
        total_transactions AS tx_count,
        total_amount
    FROM public_gold.gold_daily_summary
)
SELECT
    s.transaction_date,
    s.currency,
    s.total_amount       AS silver_total,
    g.total_amount       AS gold_total,
    'GOLD_SILVER_MISMATCH' AS issue
FROM silver_totals s
JOIN gold_totals g
    ON s.transaction_date = g.transaction_date
    AND s.currency        = g.currency
WHERE
    ABS(s.total_amount - g.total_amount) > 0.01
    OR s.tx_count != g.tx_count