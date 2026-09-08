import requests
import polars as pl
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

#EXTRACT
url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1&sparkline=false"
headers = {
    "User-Agent": "CryptoAnalyticsProject/1.0"
}

response = requests.get(url, headers)
data = response.json()

crypto_df = pl.DataFrame(data)

#TRANSFORM
transformed_df = crypto_df.with_columns(
    pl.lit(datetime.now()).dt.to_string("%Y-%m-%d %H:%M:%S").alias("fetch_timestamp"),
    pl.col("symbol").str.to_uppercase(),
    (pl.col("current_price").round(2).cast(pl.String) + " $").alias("price_formatted"),
    pl.when(pl.col("price_change_percentage_24h") > 0)
    .then(pl.lit("Bullish"))
    .otherwise(pl.lit("Bearish"))
    .alias("price_trend")
)

#LOAD
db_password = os.getenv("DB_PASSWORD")
db_user = os.getenv("DB_USER")
connection_url = f"postgresql://{db_user}:{db_password}@localhost:5432/crypto_data"

db_df = transformed_df.select(
    pl.col("fetch_timestamp"),
    pl.col("symbol"),
    pl.col("current_price"),
    pl.col("price_trend")
)

db_df.write_database(
    table_name="crypto_data",
    connection=connection_url,
    if_table_exists="append"
)

#READ
print("\n--- Lese Daten aus der PostgreSQL-Datenbank ---")

query = "SELECT * FROM crypto_data;"

df_from_db = pl.read_database_uri(query=query, uri=connection_url)

print(df_from_db)