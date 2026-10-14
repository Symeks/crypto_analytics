import requests
import polars as pl
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("crypto_pipeline.log"),
        logging.StreamHandler()
    ]   
)
logging.info("Starte die Crypto-Daten-Pipeline...")

#EXTRACT
url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1&sparkline=false"
headers = {
    "User-Agent": "CryptoAnalyticsProject/1.0"
}

logging.info(f"Rufe Daten von CoinGecko ab: {url}")
response = requests.get(url, headers)
data = response.json()

if response.status_code == 200:
    logging.info("Daten erfolgreich abgerufen.")
else:
    logging.error(f"API-Fehler: Statuscode {response.status_code}")

crypto_df = pl.DataFrame(data)

#TRANSFORM
logging.info("Starte Datentransformation mit Polars...")

transformed_df = crypto_df.with_columns(
    pl.lit(datetime.now()).dt.to_string("%Y-%m-%d %H:%M:%S").alias("fetch_timestamp"),
    pl.col("symbol").str.to_uppercase(),
    (pl.col("current_price").round(2).cast(pl.String) + " $").alias("price_formatted"),
    pl.when(pl.col("price_change_percentage_24h") > 0)
    .then(pl.lit("Bullish"))
    .otherwise(pl.lit("Bearish"))
    .alias("price_trend")
)

logging.info(f"Transformation abgeschlossen. Shape: {transformed_df.shape}")

#LOAD
logging.info("Verbinde mit PostgreSQL-Datenbank...")

db_password = os.getenv("DB_PASSWORD")
db_user = os.getenv("DB_USER")
connection_url = f"postgresql://{db_user}:{db_password}@localhost:5432/crypto_data"

db_df = transformed_df.select(
    pl.col("fetch_timestamp"),
    pl.col("symbol"),
    pl.col("current_price"),
    pl.col("price_trend")
)

# --- DATABASE SETUP (Einmalig den Primary Key setzen) ---
logging.info("Überprüfe/Setze Primary Key in der Datenbank...")
engine = create_engine(connection_url)
with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE crypto_data ADD PRIMARY KEY (fetch_timestamp, symbol);"))
        logging.info("Primary Key erfolgreich gesetzt.")
    except Exception as e:
        # Wenn der Primary Key schon existiert, wirft SQLAlchemy einen Fehler
        logging.info("Primary Key existiert bereits oder konnte nicht gesetzt werden.")

# --- LOAD PHASE (Idempotent mit Upsert) ---
logging.info("Starte idempotenten Ladevorgang (Upsert)...")

temp_table_name = "crypto_data_temp"
logging.info(f"Schreibe Daten in temporäre Tabelle '{temp_table_name}'...")

pandas_df = db_df.to_pandas()
pandas_df.to_sql(name=temp_table_name, con=engine, if_exists='replace', index=False)

upsert_query = text(f"""
    INSERT INTO crypto_data (fetch_timestamp, symbol, current_price, price_trend)
    SELECT fetch_timestamp, symbol, current_price, price_trend FROM {temp_table_name}
    ON CONFLICT (fetch_timestamp, symbol) 
    DO UPDATE SET 
        current_price = EXCLUDED.current_price,
        price_trend = EXCLUDED.price_trend;
""")

with engine.begin() as conn:
    logging.info("Führe PostgreSQL UPSERT aus...")
    conn.execute(upsert_query)
    
    logging.info("Lösche temporäre Tabelle...")
    conn.execute(text(f"DROP TABLE {temp_table_name};"))

logging.info(f"Erfolgreich {len(db_df)} Zeilen in die Datenbank hochgeladen/aktualisiert!")

# Alt ohne Upsert (nur Append)
# db_df.write_database(
#     table_name="crypto_data",
#     connection=connection_url,
#     if_table_exists="append"
# )

logging.info(f"Erfolgreich {len(db_df)} Zeilen in die Datenbank geladen!")

#READ
print("\n--- Lese Daten aus der PostgreSQL-Datenbank ---")

query = "SELECT * FROM crypto_data;"

df_from_db = pl.read_database_uri(query=query, uri=connection_url)

print(df_from_db)