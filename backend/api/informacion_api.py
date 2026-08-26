"""
API REST (Flask) que expone la información de las estaciones Bicing y las
predicciones de disponibilidad de bicis (mecánicas y eléctricas) a 5 y
10 minutos para una estación dada.

Endpoints disponibles:
    GET /api/informacion  -> lista de estaciones con las columnas:
        station_id, latitud, longitud, address, post_code, capacity

    POST /api/predict
        Body JSON: { "station_id": <int> }
        Respuesta: { "station_id": ..., "last_timestamp": ..., "predictions": [...] }

Las credenciales de acceso a MySQL se leen desde el archivo `.env` en la
raíz del proyecto, a través de `backend/scripts/silver/db_config.py`.
"""

import sys
import traceback
from pathlib import Path

import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "silver"))
from db_config import get_connection_params, DB_NAME

# Añadimos al path la carpeta que contiene main.py (backend/scripts).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from main import LSTMbicis

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


@app.route("/api/predict", methods=["POST"])
def predict():
    """Recibe station_id y devuelve las predicciones de nbm y nbe a 5 y 10 min."""
    data = request.get_json(silent=True) or {}
    station_id = data.get("station_id")

    if station_id is None:
        return jsonify({"error": "station_id es obligatorio"}), 400

    try:
        station_id = int(station_id)
    except (ValueError, TypeError):
        return jsonify({"error": "station_id debe ser un número entero"}), 400

    try:
        modelo = LSTMbicis(station_id=station_id)
        modelo.entrenar_y_predecir()

        if not modelo.predictions:
            return jsonify({"error": "No se pudieron generar predicciones"}), 500

        return jsonify({
            "station_id": station_id,
            "last_timestamp": modelo.last_timestamp,
            "predictions": modelo.predictions,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
