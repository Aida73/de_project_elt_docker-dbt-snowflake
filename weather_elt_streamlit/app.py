import streamlit as st
import snowflake.connector
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

st.title("Weather Summary Dashboard")
st.markdown("This dashboard provides a summary of the weather data provided by the OpenWeather API.")
st.markdown("The data is fetched from the OpenWeather API and stored in a Snowflake database. The data is then transformed using DBT and visualized using Streamlit.")

conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
    role=os.getenv("SNOWFLAKE_ROLE"),
)

query = """
SELECT 
    DAY, CITY, AVG_TEMP, MAX_TEMP, MIN_TEMP, AVG_HUMIDITY, AVG_PRESSURE, NB_POINTS
FROM WEATHER_SUMMARY
ORDER BY DAY, CITY
"""

df = pd.read_sql(query, conn)
st.dataframe(df)

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
map_df["LAT"] = map_df["CITY"].map(lambda x: cities[x][0])
map_df["LON"] = map_df["CITY"].map(lambda x: cities[x][1])
st.map(map_df.rename(columns={"LAT": "Latitude", "LON": "Longitude"}))


# temperature moyenne par ville sur plusieurs jours
st.subheader("Average Temperature by City Over Multiple Days")
avg_temp_by_city = df.groupby("CITY")[["AVG_TEMP"]].mean().reset_index()    
avg_temp_by_city = avg_temp_by_city.sort_values("AVG_TEMP", ascending=False)
st.bar_chart(avg_temp_by_city.set_index("CITY"))



conn.close()