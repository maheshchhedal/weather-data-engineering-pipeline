import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from city_name import cities


load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Project root is 3 levels up: src/extract/extract.py -> src/extract -> src -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_weather():
    weather_data = []

    if not API_KEY:
        raise ValueError("WEATHER_API_KEY is not set in the .env file.")

    for city in cities:
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric",
        }

        try:
            response = requests.get(
                WEATHER_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            weather_data.append({
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "weather": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
            })

        except requests.RequestException as e:
            print(f"Failed to fetch weather for {city}: {e}")

    return weather_data


if __name__ == "__main__":
    weather_data = fetch_weather()
    df = pd.DataFrame(weather_data)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"weather_data_{timestamp}.csv"

    df.to_csv(RAW_DATA_DIR / filename, index=False)
    print(f"Saved {len(df)} rows to {RAW_DATA_DIR / filename}")