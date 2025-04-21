select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select city
from DBT_DOCKER_DEMO.BASE.stg_weather_raw
where city is null



      
    ) dbt_internal_test