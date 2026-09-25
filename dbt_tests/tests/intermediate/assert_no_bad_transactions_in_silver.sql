-- tests/intermediate/assert_no_bad_transactions_in_silver.sql
-- Verifies bad transaction records flagged in Bronze
-- do NOT appear in Silver
-- Test PASSES when ZERO rows returned

SELECT
    b.transaction_id,
    b.dq_amount_flag,
    b.dq_currency_flag,
    b.dq_date_flag,
    b.dq_status_flag,
    'BAD_TRANSACTION_IN_SILVER' AS issue
FROM public_bronze.stg_transactions b
INNER JOIN public_silver.int_transactions s
    ON b.transaction_id = s.transaction_id
WHERE
    b.dq_amount_flag   != 'OK'
    OR b.dq_currency_flag != 'OK'
    OR b.dq_date_flag     != 'OK'
    OR b.dq_status_flag   != 'OK'