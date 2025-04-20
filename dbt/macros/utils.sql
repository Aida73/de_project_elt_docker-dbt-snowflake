{% macro to_fahrenheit(celsus_column) %}
    ROUND((({{ celsus_column }} * 9 / 5) + 32), 2)
{% endmacro %}