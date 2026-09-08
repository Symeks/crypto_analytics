# Crypto Market ETL Pipeline

An end-to-end data engineering pipeline built to ingest live cryptocurrency market data, perform high-performance transformations using **Polars**, and persist structured time-series data into a **PostgreSQL** data warehouse containerized via **Docker**.

---

## Architecture & Workflow

1. **Extract**: Pulls live payload data from the CoinGecko REST API with customized request headers.
2. **Transform**: Processes the raw dataset using Polars vectorization:
   - Normalizes and formats UTC timestamps (`fetch_timestamp`).
   - Standardizes ticker symbols to uppercase.
   - Computes conditional business logic (`price_trend`: Bullish/Bearish).
   - Preserves raw numeric float types (`f64`) for analytical calculations alongside formatted display strings.
3. **Load**: Interfaces with PostgreSQL via SQLAlchemy, appending time-series snapshots natively without data loss.

---

## Tech Stack

- **Language**: Python 3.10+
- **Data Manipulation**: Polars, Pandas, PyArrow
- **Database & Infrastructure**: PostgreSQL, Docker, SQLAlchemy, ConnectorX
- **API**: CoinGecko v3 Markets
