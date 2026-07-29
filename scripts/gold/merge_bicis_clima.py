import importlib.util
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


DB_URL = "mysql+mysqlconnector://root@localhost:3306/Bicing"


def _import_fetch_clima_bcn():
    module_path = (
        Path(__file__).resolve().parent.parent / "silver" / "4.fetch_clima_bcn.py"
    )
    spec = importlib.util.spec_from_file_location("fetch_clima_bcn", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_clima_bcn"] = module
    spec.loader.exec_module(module)
    return module.fetch_clima_barcelona


def cargar_estado_station(station_id: int):
    query = """
        SELECT
            *,
            num_bikes_available + num_bikes_available_mechanical + num_bikes_available_ebike + num_docks_available as capacity,
            DATE(datetime) as date,
            HOUR(datetime) as hour
        FROM estado
        WHERE station_id = %s AND datetime >= '2021-01-01'
        ORDER BY datetime ASC
    """
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=(station_id,))
    return df


def merge_bicis_clima(station_id: int):
    fetch_clima_barcelona = _import_fetch_clima_bcn()

    df_estado = cargar_estado_station(station_id)
    df_estado = df_estado.assign(
        datetime=pd.to_datetime(df_estado["datetime"]),
        date=df_estado["datetime"].dt.strftime("%Y-%m-%d")
    )

    df_clima = fetch_clima_barcelona()

    df_merged = pd.merge(
        df_estado,
        df_clima,
        on=["date", "hour"],
        how="left",
    )
    df_merged = df_merged.drop(columns=["date", "hour"])
    return df_merged


if __name__ == "__main__":
    df = merge_bicis_clima(10)
    print(df.head())
    print("\nValores nulos:")
    print(df.isnull().sum())
    print(f"Total filas: {len(df)}")
