"""
API REST (Flask) que expone la información de las estaciones Bicing.

Endpoint disponible:
    GET /api/informacion  -> lista de estaciones con las columnas:
        station_id, latitud, longitud, address, post_code, capacity

Las credenciales de acceso a MySQL se leen desde el archivo `.env` en la
raíz del proyecto, a través de `backend/scripts/silver/db_config.py`.
"""

import sys
from pathlib import Path

import mysql.connector
from flask import Flask, jsonify
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "silver"))
from db_config import get_connection_params, DB_NAME

app = Flask(__name__)
CORS(app)  # Permite que el frontend (React, otro origen) consuma esta API

COLUMNS = ["station_id", "latitud", "longitud", "address", "post_code", "capacity"]


@app.route("/api/informacion", methods=["GET"])
def obtener_informacion():
    """Devuelve, en formato JSON, las columnas seleccionadas de la tabla `informacion`."""
    query = f"SELECT {', '.join(COLUMNS)} FROM informacion"

    conn = mysql.connector.connect(**get_connection_params(DB_NAME))
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        filas = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()

    estaciones = {
        fila["station_id"]: {k: v for k, v in fila.items() if k != "station_id"}
        for fila in filas
    }

    return jsonify(estaciones)


if __name__ == "__main__":
    app.run(debug=True)
