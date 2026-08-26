"""
API REST (Flask) que expone las predicciones de disponibilidad de bicis
(mecánicas y eléctricas) a 5 y 10 minutos para una estación Bicing dada.

Endpoint disponible:
    POST /api/predict
    Body JSON: { "station_id": <int> }

Respuesta JSON:
    {
        "station_id": <int>,
        "last_timestamp": <str ISO-8601>,
        "predictions": [
            {"horizon_minutes": 5, "timestamp": <str>, "nbm": <float>, "nbe": <float>},
            {"horizon_minutes": 10, "timestamp": <str>, "nbm": <float>, "nbe": <float>}
        ]
    }

El endpoint carga la clase LSTMbicis desde backend/scripts/main.py y ejecuta
entrenar_y_predecir() para la estación solicitada. El tiempo de respuesta
puede ser de ~1-2 minutos porque reentrena el modelo LSTM con los datos
históricos de la estación.
"""

import sys
import traceback
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Añadimos al path la carpeta que contiene main.py (backend/scripts).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from main import LSTMbicis

app = Flask(__name__)
CORS(app)  # Permite llamadas desde el frontend React


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
    app.run(host="0.0.0.0", port=5001, debug=True)
