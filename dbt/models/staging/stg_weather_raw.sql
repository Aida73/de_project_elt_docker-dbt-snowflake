{{ config(materialized='view')}}

-- This model is used to stage the raw weather data from the source

SELECT
    city,
    timestamp,
    temperature,
    humidity,
    pressure,
    description
FROM {{ source('staging', 'WEATHER_RAW') }}