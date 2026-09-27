{% macro test_no_future_date(model, column_name) %}

    SELECT {{ column_name }}
    FROM {{ model }}
    WHERE {{ column_name }} > CURRENT_DATE

{% endmacro %}