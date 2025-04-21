-- jour | ville | avg_temp | max_humidity | nb_points


SELECT
    TO_DATE(timestamp) AS day,
    city,
    ROUND(AVG(temperature), 2) AS avg_temp,
    ROUND(MAX(temperature), 2) AS max_temp,
    ROUND(MIN(temperature), 2) AS min_temp,
    -- Use the macro to convert Celsius to Fahrenheit
    
    ROUND(((AVG(temperature) * 9 / 5) + 32), 2)
 AS avg_temp_f,
    
    ROUND(((MAX(temperature) * 9 / 5) + 32), 2)
 AS max_temp_f,
    
    ROUND(((MIN(temperature) * 9 / 5) + 32), 2)
 AS min_temp_f,

    ROUND(AVG(humidity), 2) AS avg_humidity,
    ROUND(AVG(pressure), 2) AS avg_pressure,
    COUNT(*) AS nb_points
FROM DBT_DOCKER_DEMO.BASE.stg_weather_raw
GROUP BY 1, 2
ORDER BY 1, 2