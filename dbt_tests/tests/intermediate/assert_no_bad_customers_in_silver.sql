-- tests/intermediate/assert_no_bad_customers_in_silver.sql
-- Verifies bad customer records flagged in Bronze
-- do NOT appear in Silver
-- Test PASSES when ZERO rows returned

SELECT
    b.customer_id,
    b.dq_email_flag,
    b.dq_name_flag,
    b.dq_phone_flag,
    'BAD_CUSTOMER_IN_SILVER' AS issue
FROM public_bronze.stg_customers b
INNER JOIN public_silver.int_customers s
    ON b.customer_id = s.customer_id
WHERE
    b.dq_email_flag != 'OK'
    OR b.dq_name_flag  != 'OK'
    OR b.dq_phone_flag != 'OK'