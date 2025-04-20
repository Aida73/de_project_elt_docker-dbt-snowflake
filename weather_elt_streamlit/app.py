import streamlit as st
import snowflake.connector
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

load_dotenv()
print("User:", os.getenv("SNOWFLAKE_USER"))
print("Password present:", "Yes" if os.getenv("SNOWFLAKE_PASSWORD") else "No")
print("Account:", os.getenv("SNOWFLAKE_ACCOUNT"))

account=os.getenv("SNOWFLAKE_ACCOUNT")
user=os.getenv("SNOWFLAKE_USER")
password=os.getenv("SNOWFLAKE_PASSWORD")
warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
database=os.getenv("SNOWFLAKE_DATABASE")
schema=os.getenv("SNOWFLAKE_SCHEMA")
role=os.getenv("SNOWFLAKE_ROLE")

conn = snowflake.connector.connect(
    user=user,
    password=password,
    account=account,
    warehouse=warehouse,
    database=database,
    schema=schema,
    role=role
)
print("Connection successful")

# conn_str = f"snowflake://{user}:{password}@{account}/{database}/{schema}?warehouse={warehouse}&role={role}" 
# engine = create_engine(conn_str)

st.set_page_config(page_title="Weather Dashboard", layout="wide")
st.title("Weather Summary Dashboard")
st.markdown("This dashboard provides a summary of the weather data provided by the OpenWeather API.")
st.markdown("The data is fetched from the OpenWeather API and stored in a Snowflake database. The data is then transformed using DBT and visualized using Streamlit.")


query = """
SELECT 
    DAY, CITY, AVG_TEMP, MAX_TEMP, MIN_TEMP, AVG_HUMIDITY, AVG_PRESSURE, NB_POINTS
FROM WEATHER_SUMMARY
ORDER BY DAY, CITY
"""

try:
    #engine.connect()
    df = pd.read_sql(query, conn)
    if df.empty:
        print("No data available")
        st.write("No data available")
    else:
        st.dataframe(df)
        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)
        # filtered_by_day the KPI
        date_range = st.slider("Select a date range", min_value=df["DAY"].min(), max_value=df["DAY"].max(), value=(df["DAY"].min(), df["DAY"].max()))
        filtered_df = df[(df["DAY"] >= date_range[0]) & (df["DAY"] <= date_range[1])]
        with col1:
            st.metric("Average Temperature", f"{filtered_df['AVG_TEMP'].mean():.2f} °C")
        with col2:
            hottest = filtered_df.loc[filtered_df['AVG_TEMP'].idxmax()]
            st.metric("Hottest City", f"{hottest['CITY']}, ({hottest['AVG_TEMP']:.1f} °C)")
        with col3:
            humidest = filtered_df.loc[filtered_df['AVG_HUMIDITY'].idxmax()]
            st.metric("Most Humid City", f"{humidest['CITY']}, ({humidest['AVG_HUMIDITY']:.1f} %)")
        

    city = st.selectbox("Select a city", df["CITY"].unique())
    st.markdown(f"### Weather Temperature Summary for {city}")
    st.bar_chart(df[df["CITY"] == city].set_index("DAY")[["AVG_TEMP", "MAX_TEMP", "MIN_TEMP"]])

    # distribution des 
    st.subheader("Distribution of Weather Data")
    fig, ax = plt.subplots()
    df['AVG_TEMP'].hist(bins=20, edgecolor='black', ax=ax)
    ax.set_title("Distribution of Average Temperature")
    ax.set_xlabel("Average Temperature (C-elsius)")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)


    # Carte des temperatures par ville
    st.subheader("Map of Temperatures by City")
    cities = {
        "Paris": (48.8566, 2.3522),
        "London": (51.5074, -0.1278),
        "New York": (40.7128, -74.0060)
    }
    map_df = df[["CITY", "AVG_TEMP"]].drop_duplicates("CITY")
    map_df["Latitude"] = map_df["CITY"].map(lambda x: cities[x][0])
    map_df["Longitude"] = map_df["CITY"].map(lambda x: cities[x][1])
    st.map(map_df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))


    # temperature moyenne par ville sur plusieurs jours
    st.subheader("Average Temperature by City Over Multiple Days")
    avg_temp_by_city = df.groupby("CITY")[["AVG_TEMP"]].mean().reset_index()    
    avg_temp_by_city = avg_temp_by_city.sort_values("AVG_TEMP", ascending=False)
    st.bar_chart(avg_temp_by_city.set_index("CITY"))

except Exception as e:
    print("Connexion échouée, arrêt de la tentative.")
    st.write("Error:", e)
finally:
    conn.close()
    print("Connexion fermée.")
