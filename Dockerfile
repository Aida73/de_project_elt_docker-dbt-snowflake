FROM apache/airflow:2.10.4-python3.11

RUN pip install --no-cache-dir \
    dbt-core \
    dbt-snowflake \
    requests \
    snowflake-connector-python \
    apache-airflow-providers-snowflake \
    snowflake-sqlalchemy
