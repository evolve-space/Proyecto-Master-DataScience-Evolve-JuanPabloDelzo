import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen

import holidays
import pandas as pd

LAT, LON = 41.3851, 2.1734
START = "2021-01-01"
END = "2025-09-30"

_ES_HOLIDAYS = holidays.ES(subdiv="CT", years=range(2021, 2026))


def condicion(code):
    if code is None:
        return ""
    if code == 0:
        return "despejado"
    if code in (1, 2, 3):
        return "nublado"
    if code in (45, 48):
        return "niebla"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "lluvia"
    if code in (71, 73, 75, 77, 85, 86):
        return "nieve"
    if code in (95, 96, 99):
        return "tormenta"
    return "desconocido"


def fetch_chunk(start, end):
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start,
        "end_date": end,
        "hourly": "temperature_2m,weather_code",
        "timezone": "Europe/Madrid",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urlencode(params)
    with urlopen(url, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_clima_barcelona(start=START, end=END):
    records = []
    current = datetime.strptime(start, "%Y-%m-%d")
    final = datetime.strptime(end, "%Y-%m-%d")

    while current <= final:
        chunk_end = min(datetime(current.year, 12, 31), final)
        start_str = current.strftime("%Y-%m-%d")
        end_str = chunk_end.strftime("%Y-%m-%d")
        print(f"Descargando {start_str} a {end_str}...")

        data = fetch_chunk(start_str, end_str)
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        codes = hourly.get("weather_code", [])

        for t, temp, code in zip(times, temps, codes):
            dt = datetime.fromisoformat(t)
            date_str = dt.strftime("%Y-%m-%d")
            records.append(
                {
                    "date": date_str,
                    "hour": dt.hour,
                    "temp_c": temp,
                    "condicion": condicion(code),
                    "is_holiday": date_str in _ES_HOLIDAYS,
                }
            )

        current = chunk_end + timedelta(days=1)
        

    return pd.DataFrame(
        records, columns=["date","is_holiday","hour", "temp_c", "condicion"]
    )


if __name__ == "__main__":
    df = fetch_clima_barcelona()
    print("\nViendo valores nulos:")
    print(df.isnull().sum())
    print(df.head(10))
    print(f"Total filas: {len(df)}")
