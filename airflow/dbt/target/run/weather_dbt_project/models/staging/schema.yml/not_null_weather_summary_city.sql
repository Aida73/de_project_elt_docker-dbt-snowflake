select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select city
from DBT_DOCKER_DEMO.BASE.weather_summary
where city is null



      
    ) dbt_internal_test