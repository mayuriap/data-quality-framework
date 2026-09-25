 -- tests/marts/assert_gold_customer_matches_silver.sql
-- Verifies every Silver customer appears in Gold customer summary
-- Test PASSES when ZERO rows returned

SELECT
    c.customer_id,
    'MISSING_FROM_GOLD' AS issue
FROM public_silver.int_customers c
LEFT JOIN public_gold.gold_customer_summary g
    ON c.customer_id = g.customer_id
WHERE g.customer_id IS NULL