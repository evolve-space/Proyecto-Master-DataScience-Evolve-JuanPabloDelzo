import sys
from pathlib import Path

import mysql.connector
import pandas as pd
from mysql.connector import Error

#Extrayendo los datos de hechos
ESTADO_DIR = Path(__file__).resolve().parent.parent / "docs" / "entregas" / "estado"
files = list(ESTADO_DIR.iterdir())
ATRIBUTOS = ["station_id", "num_bikes_available", 
             "num_bikes_available_types.mechanical", 
             "num_bikes_available_types.ebike", 
             "num_docks_available", 
             "last_reported"]

def load_information():
    hechos=pd.concat([pd.read_csv(file,usecols=ATRIBUTOS,low_memory=False).drop_duplicates() for file in files],
                      axis=0,ignore_index=True)
    
    #Eliminar valore nulos en id y el tiempo
    hechos=hechos.dropna(subset=["station_id","last_reported"])

    #Corrigiendo el formato de tipos de bicicletas
    hechos=hechos.rename(columns={
        'num_bikes_available_types.mechanical': 'num_bikes_available_mechanical',
        'num_bikes_available_types.ebike': 'num_bikes_available_ebike',
        'last_reported': 'datetime'
        }
        )

    #Corregir el formato
    hechos=hechos.assign(
        station_id=hechos['station_id'].astype(int),
        num_bikes_available=hechos['num_bikes_available'].astype(int),
        num_bikes_available_mechanical=hechos['num_bikes_available_mechanical'].astype(int),
        num_bikes_available_ebike=hechos['num_bikes_available_ebike'].astype(int),
        num_docks_available=hechos['num_docks_available'].astype(int),
        datetime=pd.to_datetime(hechos['datetime'], unit='s')
    )
    return hechos
# hechos = hechos[[
#     "station_id",
#     "num_bikes_available",
#     "num_bikes_available_mechanical",
#     "num_bikes_available_ebike",
#     "num_docks_available",
#     "datetime",
# ]]

INSERT_ESTADO = """
    INSERT INTO estado (
        station_id,
        num_bikes_available,
        num_bikes_available_mechanical,
        num_bikes_available_ebike,
        num_docks_available,
        datetime
    ) VALUES (%s, %s, %s, %s, %s, %s)
"""


def insert_estado(dataframe):
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            database="Bicing",
        )
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM informacion")
        if cursor.fetchone()[0] == 0:
            raise RuntimeError("La tabla informacion está vacía; carga sus estaciones antes de insertar estado.")

        batch_size = 10_000
        for start in range(0, len(dataframe), batch_size):
            batch = dataframe.iloc[start:start + batch_size]
            cursor.executemany(INSERT_ESTADO, list(batch.itertuples(index=False, name=None)))
            connection.commit()
        cursor.close()
        print(f"{len(dataframe)} registros insertados en estado.")
    except (Error, RuntimeError) as error:
        print(f"No se pudieron insertar los registros: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    insert_estado(load_information())
