

-- This model is used to stage the raw weather data from the source

SELECT
    city,
    timestamp,
    temperature,
    humidity,
    pressure,
    description
FROM DBT_DOCKER_DEMO.STAGING.WEATHER_RAW