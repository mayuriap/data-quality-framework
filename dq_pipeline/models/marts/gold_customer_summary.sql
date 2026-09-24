-- models/marts/gold_customer_summary.sql
-- Gold layer — customer level aggregations
-- Shows spending behaviour per customer
-- Materialised as table — full rebuild every run

{{
    config(
        materialized = 'table',
        schema       = 'gold'
    )
}}

SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.segment,

    -- Transaction counts
    COUNT(t.transaction_id)                     AS total_transactions,
    COUNT(CASE WHEN t.status = 'COMPLETED'
               THEN 1 END)                      AS completed_count,
    COUNT(CASE WHEN t.status = 'PENDING'
               THEN 1 END)                      AS pending_count,
    COUNT(CASE WHEN t.status = 'FAILED'
               THEN 1 END)                      AS failed_count,

    -- Amount metrics
    SUM(t.amount)                               AS total_spend,
    AVG(t.amount)                               AS avg_transaction,
    MIN(t.amount)                               AS min_transaction,
    MAX(t.amount)                               AS max_transaction,

    -- Currency breakdown
    COUNT(DISTINCT t.currency)                  AS currencies_used,

    -- Dates
    MIN(t.transaction_date)                     AS first_transaction,
    MAX(t.transaction_date)                     AS last_transaction,

    -- Audit
    CURRENT_TIMESTAMP                           AS created_at

FROM {{ ref('int_customers') }} c
LEFT JOIN {{ ref('int_transactions') }} t
    ON c.customer_id = t.customer_id

GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name,
    c.segment

ORDER BY
    total_spend DESC