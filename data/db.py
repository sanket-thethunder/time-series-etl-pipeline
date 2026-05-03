import sqlite3, pandas as pd
conn = sqlite3.connect("weather.db")
df = pd.read_sql("SELECT * FROM weather_hourly LIMIT 10", conn)
print(df)