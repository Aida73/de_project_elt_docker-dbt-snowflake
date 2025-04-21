from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow import DAG
from airflow.models import Variable
from datetime import datetime, timedelta
import requests
import snowflake.connector
import os
import json



DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 4, 15),
    'retries': 1,
    'retry_delay': timedelta(days=1)
}

def fetch_weather_data(**context):
    API_KEY = Variable.get("OPENWEATHER_API_KEY")
    CITY = "Paris"
    CITIES = {
        "Paris": (48.85, 2.35),
        "London": (51.50, -0.12),
        "New York": (40.71, -74.01),
    }
    all_sql_statements = [
        """
            CREATE TABLE IF NOT EXISTS STAGING.WEATHER_RAW (
                    city STRING,
                    timestamp TIMESTAMP,
                    temperature FLOAT,
                    humidity FLOAT,
                    pressure FLOAT,
                    description STRING
            );
        """
    ]


    for city, (lat, lon) in CITIES.items():
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        context['ti'].xcom_push(key='weather_data', value=data)
        all_sql_statements.append(
            f"""
                INSERT INTO STAGING.WEATHER_RAW (
                    city, timestamp, temperature, humidity, pressure, description
                )
                VALUES (
                    '{data["name"]}',
                    CURRENT_TIMESTAMP,
                    {data["main"]["temp"]},
                    {data["main"]["humidity"]},
                    {data["main"]["pressure"]},
                    '{data["weather"][0]["description"]}'
                );
            """
        )
    context['ti'].xcom_push(key='weather_table_sql_query', value="\n".join(all_sql_statements))




with DAG(
    dag_id='weather_api_to_snowflake',
    default_args=DEFAULT_ARGS,
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 4, 16),
    catchup=False,
    tags=['weather', 'snowflake', 'dbt']
) as dag:

    start = EmptyOperator(task_id='start')
    extract_weather_data = PythonOperator(
            task_id='extract_weather',
            python_callable=fetch_weather_data,
            provide_context=True
        )
        # Create weather raw data table into Snowflake
    create_weather_raw =  SnowflakeOperator(
        task_id = "load_weather_raw_to_snowflake",
        snowflake_conn_id = "snowflake_conn",
        sql="{{ ti.xcom_pull(task_ids='extract_weather', key='weather_table_sql_query') }}"
    )

    # Create a task group for dbt tasks
    with TaskGroup("dbt_tasks", tooltip="DBT Tasks") as dbt_tasks:
        env = {
            "SNOWFLAKE_ACCOUNT": Variable.get("SNOWFLAKE_ACCOUNT"),
            "SNOWFLAKE_USER": Variable.get("SNOWFLAKE_USER"),
            "SNOWFLAKE_PASSWORD": Variable.get("SNOWFLAKE_PASSWORD"),
            "SNOWFLAKE_WAREHOUSE": Variable.get("SNOWFLAKE_WAREHOUSE"),
            
        }
        DBT_BIN = Variable.get("DBT_BIN")
       
        # Task to run dbt debug
        dbt_debug = BashOperator(
            task_id='dbt_debug',
            bash_command=f'{DBT_BIN} debug --project-dir /opt/dbt --profiles-dir /opt/dbt || true',
            env=env
        )
        # Task to run dbt run
        dbt_run = BashOperator(
            task_id='dbt_run',
            bash_command=f'{DBT_BIN} run --project-dir /opt/dbt --profiles-dir /opt/dbt', 
            env=env
        )
        # Task to run dbt test
        dbt_test = BashOperator(
            task_id='dbt_test',
            bash_command=f'{DBT_BIN} test --project-dir /opt/dbt --profiles-dir /opt/dbt',
            env=env
        )
        # Task to run dbt docs generate
        dbt_docs_generate = BashOperator(
            task_id='dbt_docs_generate',
            bash_command=f'{DBT_BIN} docs generate --project-dir /opt/dbt --profiles-dir /opt/dbt',
            env=env
        )
        # Task to run dbt docs serve
        dbt_docs_serve = BashOperator(
            task_id='dbt_docs_serve',
            bash_command=f'{DBT_BIN} docs serve --port 8086 --project-dir /opt/dbt --profiles-dir /opt/dbt',
            env=env
        )
        dbt_debug >> dbt_run >> dbt_test >> dbt_docs_generate >> dbt_docs_serve

    end = EmptyOperator(task_id='end')

    start >> extract_weather_data >> create_weather_raw >> dbt_tasks >> end

