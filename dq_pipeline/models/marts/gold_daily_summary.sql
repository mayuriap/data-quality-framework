-- models/marts/gold_daily_summary.sql
-- Gold layer — daily aggregations
-- Business metrics ready for reporting
-- Materialised as table — full rebuild every run

{{
    config(
        materialized = 'table',
        schema       = 'gold'
    )
}}

SELECT
    t.transaction_date,
    t.currency,

    -- Transaction counts
    COUNT(*)                                    AS total_transactions,
    COUNT(CASE WHEN t.status = 'COMPLETED'
               THEN 1 END)                      AS completed_count,
    COUNT(CASE WHEN t.status = 'PENDING'
               THEN 1 END)                      AS pending_count,
    COUNT(CASE WHEN t.status = 'FAILED'
               THEN 1 END)                      AS failed_count,

    -- Amount metrics
    SUM(t.amount)                               AS total_amount,
    AVG(t.amount)                               AS avg_amount,
    MIN(t.amount)                               AS min_amount,
    MAX(t.amount)                               AS max_amount,

    -- Customer metrics
    COUNT(DISTINCT t.customer_id)               AS unique_customers,

    -- Audit
    CURRENT_TIMESTAMP                           AS created_at

FROM {{ ref('int_transactions') }} t

GROUP BY
    t.transaction_date,
    t.currency

ORDER BY
    t.transaction_date,
    t.currency