
  create or replace   view DBT_DOCKER_DEMO.BASE.stg_weather_raw
  
   as (
    

-- This model is used to stage the raw weather data from the source

SELECT
    city,
    timestamp,
    temperature,
    humidity,
    pressure,
    description
FROM DBT_DOCKER_DEMO.STAGING.WEATHER_RAW
  );

