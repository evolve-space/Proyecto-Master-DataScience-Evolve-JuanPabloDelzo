import importlib.util
import sys
from pathlib import Path

import pandas as pd
import numpy as np
from sqlalchemy import create_engine


DB_URL = "mysql+mysqlconnector://root@localhost:3306/Bicing"


def _import_fetch_clima_bcn():
    """
    Importa la función fetch_clima_barcelona desde el script silver/4.fetch_clima_bcn.py.
    
    Returns:
        Función fetch_clima_barcelona
    """
    module_path = (
        Path(__file__).resolve().parent.parent / "silver" / "4.fetch_clima_bcn.py"
    )
    spec = importlib.util.spec_from_file_location("fetch_clima_bcn", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_clima_bcn"] = module
    spec.loader.exec_module(module)
    return module.fetch_clima_barcelona


def cargar_estado_station(station_id: int):
    """
    Carga el estado de una estación desde la base de datos.
    
    Args:
        station_id: ID de la estación a consultar
        
    Returns:
        DataFrame con el estado de la estación
    """
    query = """
          WITH aux_table AS (
          SELECT 
              num_bikes_available_mechanical AS n_bikes_mechanical,
              num_bikes_available_ebike AS n_bikes_ebike, 
              datetime,
              HOUR(datetime) AS hour,
              HOUR(datetime) + MINUTE(datetime)/60 AS h,
              dayofweek(datetime) AS day_week,
              DAYOFYEAR(datetime) AS day_year,
              CASE
                  WHEN DAYOFYEAR(CONCAT(YEAR(datetime), '-12-31')) = 366 THEN 366
                  ELSE 365
              END AS days_in_year
          FROM estado
          WHERE station_id = %s AND datetime >= '2021-01-01'
          ORDER BY datetime ASC)
          SELECT 
              datetime,
              n_bikes_mechanical,
              n_bikes_ebike,
              hour,
              ROUND(SIN(2*PI()*h/24),4) AS hour_sin, 
              ROUND(COS(2*PI()*h/24),4) AS hour_cos, 
              ROUND(SIN(2*PI()*day_week/7),4) AS dow_sin,
              ROUND(COS(2*PI()*day_week/7),4) AS dow_cos,
              ROUND(SIN(2*PI()*day_year/days_in_year),4) AS year_sin,
              ROUND(COS(2*PI()*day_year/days_in_year),4) AS year_cos
          FROM aux_table
          """
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=(station_id,))
    return df

###################################
#######  FUNCIÓN PRINCIPAL ########
###################################

def bicis(station_id: int):
    """
    Carga el estado de una estación y el clima de Barcelona,
    luego une ambos datasets por fecha y hora.
    
    Args:
        station_id: ID de la estación a consultar
        
    Returns:
        DataFrame con el estado de la estación y el clima
    """
    #1.Estado de las estación
    df_estado = cargar_estado_station(station_id)
    df_estado = df_estado.assign(
        datetime=pd.to_datetime(df_estado.datetime),
        date=df_estado.datetime.dt.strftime("%Y-%m-%d")
    )
    
    #2.Clima y festivos
    fetch_clima_barcelona = _import_fetch_clima_bcn()
    df_clima = fetch_clima_barcelona()
    
    #3.Unión de los dos datasets
    df_merged = pd.merge(
        df_estado,
        df_clima,
        on=["date", "hour"],
        how="left",
    )
    # Fijando datetime como índice con la opción inplace=True
    df_merged.set_index("datetime", inplace=True)
    # Eliminando las columnas no útiles para el análisis
    df_merged = df_merged.drop(columns=["date","hour"])

    # ÚLTIMO PASO: Reindexar a una frecuencia fija de 5 minutos, rellenando los huecos
    # (y los registros ya insertados por rellenar_huecos_tiempo) con el
    # último valor conocido (forward fill), de forma que las filas queden
    # equidistantes en el tiempo.
    df_merged_filled = df_merged.asfreq('5min', method='ffill')
    return df_merged_filled

###################################
#####  EJECUCIÓN MANUAL ###########
###################################
if __name__ == "__main__":
    id_est=2
    df = bicis(id_est)
    print(f"\nEstación {id_est}:")
    print(df.tail(10))
    print("\nValores nulos:")
    print(df.isnull().sum())
    print(f"Total filas: {len(df)}")

    