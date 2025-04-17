from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
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
    schedule_interval=timedelta(minutes=2),
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

    end = EmptyOperator(task_id='end')

    start >> extract_weather_data >> create_weather_raw >> end

