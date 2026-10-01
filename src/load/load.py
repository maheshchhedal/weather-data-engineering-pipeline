import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"


def get_engine():
    DB_URL = (
        f"postgresql+psycopg2://"
        f"{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}"
        f"/{DB_NAME}"
    )
    return create_engine(DB_URL)


def get_latest_processed_file():
    csv_files = list(PROCESSED_DATA_DIR.glob("weather_processed_*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No processed CSV files found in {PROCESSED_DATA_DIR}")

    latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
    print(f"Latest processed file: {latest_file.name}")
    return latest_file


def load_data(file_path):
    engine = get_engine()
    df = pd.read_csv(file_path)
    print(f"Rows to load: {len(df)}")

    # 1. Insert unique cities into dim_cities (skip if already exists)
    cities = df[["city", "country"]].drop_duplicates()
    cities.columns = ["city_name", "country"]

    with engine.begin() as conn:
        for _, row in cities.iterrows():
            conn.execute(
                text("""
                    INSERT INTO dim_cities (city_name, country)
                    VALUES (:city_name, :country)
                    ON CONFLICT (city_name, country) DO NOTHING
                """),
                {"city_name": row["city_name"], "country": row["country"]},
            )
    print(f"Inserted/skipped {len(cities)} cities into dim_cities")

    # 2. Fetch city_id mapping
    with engine.connect() as conn:
        result = conn.execute(text("SELECT city_id, city_name, country FROM dim_cities"))
        city_map = {
            (r.city_name, r.country): r.city_id for r in result
        }

    # 3. Attach city_id to each weather row
    df["city_id"] = df.apply(
        lambda r: city_map.get((r["city"], r["country"])), axis=1
    )
    df = df.dropna(subset=["city_id"])
    df["city_id"] = df["city_id"].astype(int)

    # 4. Insert weather rows into fct_weather
    weather_rows = df[[
        "city_id", "temperature", "feels_like",
        "humidity", "pressure", "weather", "wind_speed"
    ]].to_dict(orient="records")

    with engine.begin() as conn:
        for row in weather_rows:
            conn.execute(
                text("""
                    INSERT INTO fct_weather
                    (city_id, temperature, feels_like, humidity,
                     pressure, weather, wind_speed)
                    VALUES
                    (:city_id, :temperature, :feels_like, :humidity,
                     :pressure, :weather, :wind_speed)
                """),
                row,
            )
    print(f"Inserted {len(weather_rows)} rows into fct_weather")


if __name__ == "__main__":
    latest = get_latest_processed_file()
    load_data(latest)
    print("Load completed successfully")