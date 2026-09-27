{% macro test_settlement_after_trade(model, column_name, trade_date_col) %}

    SELECT 
        {{ column_name }}       AS settlement_date,
        {{ trade_date_col }}    AS transaction_date
    FROM {{ model }}
    WHERE {{ column_name }} < {{ trade_date_col }}

{% endmacro %}