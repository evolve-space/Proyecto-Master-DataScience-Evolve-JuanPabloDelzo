import sys
from pathlib import Path
import mysql.connector
import pandas as pd
import numpy as np
from mysql.connector import Error

INFORMACION_DIR = Path(__file__).resolve().parent.parent / "docs" / "entregas" / "informacion"
files = sorted(INFORMACION_DIR.iterdir())
ATRIBUTOS = [
    "station_id",
    "physical_configuration",
    "lat",
    "lon",
    "address",
    "post_code",
    "capacity",
    "last_updated"
]
INSERT_INFORMACION = """
    INSERT INTO informacion (
        station_id,
        physical_configuration,
        latitud,
        longitud,
        address,
        post_code,
        capacity,
        last_update
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        physical_configuration = VALUES(physical_configuration),
        latitud = VALUES(latitud),
        longitud = VALUES(longitud),
        address = VALUES(address),
        post_code = VALUES(post_code),
        capacity = VALUES(capacity),
        last_update = VALUES(last_update)
"""
def formato_cp(cp):
    """
    Formatea el código postal para que tenga 5 dígitos.
    Si no es un string numérico, devuelve np.nan.
    """
    return np.nan if not isinstance(cp, str) else cp.zfill(5)

def load_informacion():
    dimension = pd.concat([pd.read_csv(file, usecols=ATRIBUTOS, dtype={"post_code": str}, encoding="latin-1", low_memory=False) for file in files], 
                          axis=0, ignore_index=True)
    dimension = dimension.dropna(subset=["station_id"])
    dimension = dimension.drop_duplicates(subset=["station_id"], keep="last")
    dimension = dimension.rename(columns={"lat": "latitud", 
                                          "lon": "longitud",
                                          "last_updated": "last_update"})
    dimension = dimension.assign(
        station_id=dimension['station_id'].astype(int),
        capacity=dimension['capacity'].astype(int),
        last_update=pd.to_datetime(dimension['last_update'], unit='s'),
        post_code=dimension["post_code"].apply(formato_cp)
    )
    
    return dimension


def insert_informacion(dataframe):
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            database="Bicing",
        )
        cursor = connection.cursor()
        batch_size = 10_000
        for start in range(0, len(dataframe), batch_size):
            batch = dataframe.iloc[start:start + batch_size]
            rows = [
                tuple(None if pd.isna(value) else value for value in row)
                for row in batch.itertuples(index=False, name=None)
            ]
            cursor.executemany(INSERT_INFORMACION, rows)
            connection.commit()
        cursor.close()
        print(f"{len(dataframe)} estaciones insertadas en informacion.")
    except Error as error:
        print(f"No se pudieron insertar las estaciones: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    insert_informacion(load_informacion())
