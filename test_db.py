import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Lade die Passwörter und Infos aus der .env-Datei
load_dotenv()

# 2. Hole die Werte aus den Variablen
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

# 3. Baue den "Connection String" (die Adresse zur Datenbank)
# Format: postgresql://user:password@host:port/dbname
db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# 4. Erstelle den Motor (Engine), der die Verbindung verwaltet
engine = create_engine(db_url)

# 5. Versuche eine Test-Abfrage an die Datenbank zu senden
try:
    with engine.connect() as connection:
        # Wir fragen die Datenbank einfach nach ihrer Version
        result = connection.execute(text("SELECT version();"))
        db_version = result.fetchone()[0]
        print("\n✅ Verbindung erfolgreich!")
        print(f"Datenbank antwortet: {db_version}\n")
except Exception as e:
    print(f"\n❌ Fehler bei der Verbindung:\n{repr(e)}\n")