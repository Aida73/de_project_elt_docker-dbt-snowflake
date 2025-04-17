from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.decorators import dag, task
from airflow.models import Variable

from datetime import datetime
import json
import pandas as pd
import os

from minio import Minio
from io import BytesIO



def kelvin_to_fahrenheit(temp):
    return (temp - 273.15) * (9 / 5 )+ 32


@dag(
    start_date = datetime(2025, 2, 10),
    schedule=None,
    catchup=False
)
def weather_pipeline():
    API_KEY = Variable.get("OPENWEATHER_API_KEY")

    is_weather_api_ready = HttpSensor(
        task_id = 'is_weather_api_ready',
        http_conn_id = 'weathermap_api',
        endpoint = f'/data/2.5/weather?q=Portland&appid={API_KEY}'
        )

    extract_weather_data = SimpleHttpOperator(
        task_id = 'extract_weather_data',
        http_conn_id = 'weathermap_api',
        endpoint = f'/data/2.5/weather?q=Portland&appid={API_KEY}',
        method = 'GET',
        response_filter = lambda r: json.loads(r.text),
        log_response = True
    )

    @task()
    def transform(data):
        #data = task_instance.xcom_pull(task_ids="extract_weather_data")
        city = data["name"]
        weather_description = data["weather"][0]["description"]
        temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp"])
        feels_like_farenheit = kelvin_to_fahrenheit(data["main"]["feels_like"])
        min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
        max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
        pressure = data["main"]["pressure"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
        sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data["timezone"])
        sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data["timezone"])
        
        transformed_data = {
            "City": city,
            "Description": weather_description,
            "Temperature (F)": temp_farenheit,
            "Feels like (F)": feels_like_farenheit,
            "Minimum Temp (F)": min_temp_farenheit,
            "Maximum Temp (F)": max_temp_farenheit,
            "Pressure": pressure,
            "Humidity": humidity,
            "Wind Speed": wind_speed,
            "Time of Record": time_of_record,
            "Sunrise (Local Time)": sunrise_time,
            "Sunset (Local Time)": sunset_time
        }

        df_data = pd.DataFrame([transformed_data])
        print(f"transformed data: {df_data}")
        return df_data
        #task_instance.xcom_push(key="created_dataframe", value=df_data)
    
    @task()
    def load(transformed_data):

        MINIO_BUCKET_NAME = Variable.get('MINIO_BUCKET_NAME')#"weather-data-bucket" 
        MINIO_ACCESS_KEY = Variable.get('MINIO_ACCESS_KEY') #"5hiCch5E1iVQycoFwV5t"
        MINIO_SECRET_KEY = Variable.get('MINIO_SECRET_KEY')#"z4zcsnBv4VQeG7goPI4syQledd21XLDT1kaZEBEd"

        client = Minio("minio:9000", access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

        # Make MINIO_BUCKET_NAME if not exist.
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            client.make_bucket(MINIO_BUCKET_NAME)
            print(f"Bucket '{MINIO_BUCKET_NAME}' créé.")
        else:
            print(f"Bucket '{MINIO_BUCKET_NAME}' existe déjà.")

        #dataframe = task_instance.xcom_pull(task_ids='transform_load_weather_data', key='created_dataframe')
        if transformed_data is None:
            raise ValueError("Aucun DataFrame trouvé dans les XComs")
        
        dt_string = datetime.now().strftime("%d%m%Y%H%M%S")
        dt_string = "current_weather_data_portland_" + dt_string
        
        csv_buffer = BytesIO()
        transformed_data.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Put csv data in the bucket
        client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=f"{dt_string}.csv",
            data=csv_buffer,
            length=csv_buffer.getbuffer().nbytes,
            content_type="text/csv"
        )
        print("File uploaded successfully to MinIO!")
    

    is_weather_api_ready >> extract_weather_data 
    transformed_data = transform(extract_weather_data.output) 
    load(transformed_data)

weather_pipeline()
