-- jour | ville | avg_temp | max_humidity | nb_points
{{ config(materialized='table') }}

SELECT
    DAY(timestamp) AS day,
    city,
    ROUND(AVG(temperature), 2) AS avg_temp,
    ROUND(MAX(temperature), 2) AS max_temp,
    ROUND(MIN(temperature), 2) AS min_temp,
    ROUND(AVG(humidity), 2) AS avg_humidity,
    ROUND(AVG(pressure), 2) AS avg_pressure,
    COUNT(*) AS nb_points
FROM {{ ref('stg_weather_raw') }}
GROUP BY 1, 2
ORDER BY 1, 2