import pandas as pd
from pathlib import Path
from datetime import datetime


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_latest_raw_file():
    csv_files = list(RAW_DATA_DIR.glob("weather_data_*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DATA_DIR}")

    latest_file = max(csv_files, key=lambda file: file.stat().st_mtime)
    print(f"Latest raw file: {latest_file.name}")
    return latest_file


def transform_data(file_path):
    df = pd.read_csv(file_path)
    print(f"Initial rows: {len(df)}")
    print(f"Columns read: {list(df.columns)}")

    # 1. Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # 2. Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"Dropped {before - len(df)} duplicate rows")

    # 3. Drop rows with critical nulls
    before = len(df)
    df = df.dropna(subset=["city", "temperature", "humidity", "pressure"])
    print(f"Dropped {before - len(df)} rows with critical nulls")

    # 4. Enforce numeric types
    numeric_cols = ["temperature", "feels_like", "humidity", "pressure", "wind_speed"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5. Normalize string columns
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["country"] = df["country"].astype(str).str.strip().str.upper()
    df["weather"] = df["weather"].astype(str).str.strip().str.lower()

    # 6. Remove rows that became NaN after type coercion
    df = df.dropna(subset=numeric_cols)

    # 7. Reset index
    df = df.reset_index(drop=True)

    print(f"Final rows: {len(df)}")
    print(f"Final columns: {list(df.columns)}")
    return df


if __name__ == "__main__":
    latest_file = get_latest_raw_file()
    df = transform_data(latest_file)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = PROCESSED_DATA_DIR / f"weather_processed_{timestamp}.csv"

    df.to_csv(output_file, index=False)
    print(f"Saved processed data to {output_file}")