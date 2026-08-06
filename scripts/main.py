import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# Pasos de 5 minutos entre cada fila (frecuencia fijada por bicis() en bikes.py).
STEP_MINUTES = 5
# Horizontes de predicción solicitados: 5 y 10 minutos vista.
HORIZONTES_MIN = (5, 10)
LOOKBACK = 24  # nº de pasos pasados (24 * 5min = 2 horas) usados como entrada de la LSTM
TARGET_COLS = ["nbm", "nbe"]


def _import_bicis():
    """Importa dinámicamente la función `bicis` desde scripts/gold/bikes.py."""
    module_path = Path(__file__).resolve().parent / "gold" / "bikes.py"
    spec = importlib.util.spec_from_file_location("bikes", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bikes"] = module
    spec.loader.exec_module(module)
    return module.bicis


def preparar_datos(df: pd.DataFrame):
    """Codifica variables categóricas/booleanas y separa features y targets.

    Returns:
        df_features: DataFrame con las columnas de entrada ya codificadas.
        feature_cols: nombres finales de columnas de entrada (incluye
            las dummies de `condicion`).
    """
    df = df.copy()
    df["is_holiday"] = df["is_holiday"].astype(int)

    time_cols = [
        "hour_sin",
        "hour_cos",
        "dow_sin",
        "dow_cos",
        "year_sin",
        "year_cos",
    ]
    lag_cols = ["lag_nbm", "lag_nbe"]
    weather_cols = [
        "temperature_c",
        "relative_humidity_2m",
        "rain",
        "cloud_cover",
        "wind_speed_10m",
    ]

    df_features = df[
        time_cols + lag_cols + weather_cols + ["is_holiday", "is_imputed"]
    ].astype(float)

    df_features = df_features.ffill().bfill()

    feature_cols = list(df_features.columns)
    return df_features, feature_cols


def construir_secuencias(features: np.ndarray, targets: np.ndarray, lookback: int, horizon_steps):
    """Construye secuencias (X) y salidas multi-horizonte (y) para la LSTM.

    Para cada instante `i`, `X` contiene la ventana `features[i-lookback:i]`
    e `y` contiene los valores de `targets` en `i + h - 1` para cada `h` en
    `horizon_steps` (h=1 -> 5 min vista, h=2 -> 10 min vista).
    """
    n_samples = len(features)
    max_h = max(horizon_steps)

    X, y = [], []
    for i in range(lookback, n_samples - max_h + 1):
        X.append(features[i - lookback:i])
        fila_y = []
        for h in horizon_steps:
            fila_y.append(targets[i + h - 1])
        y.append(np.concatenate(fila_y))

    return np.array(X), np.array(y)


def construir_modelo(input_shape, n_outputs):
    model = Sequential([
        Input(shape=input_shape),
        LSTM(64, activation="tanh", return_sequences=True),
        Dropout(0.2),
        LSTM(32, activation="tanh", return_sequences=False),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(n_outputs, activation="linear"),
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def entrenar_y_predecir(station_id: int):
    bicis = _import_bicis()
    df = bicis(station_id)

    df_features, feature_cols = preparar_datos(df)
    df_targets = df[TARGET_COLS].astype(float)

    horizon_steps = [h // STEP_MINUTES for h in HORIZONTES_MIN]

    # Escalado de entradas y salidas (fit solo con datos de entrenamiento).
    n_total = len(df_features)
    n_test = max(int(n_total * 0.1), max(horizon_steps) + LOOKBACK + 1)
    n_train = n_total - n_test

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()
    scaler_x.fit(df_features.iloc[:n_train])
    scaler_y.fit(df_targets.iloc[:n_train])

    features_scaled = scaler_x.transform(df_features)
    targets_scaled = scaler_y.transform(df_targets)

    X, y = construir_secuencias(features_scaled, targets_scaled, LOOKBACK, horizon_steps)

    split_idx = n_train - LOOKBACK
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    n_outputs = y.shape[1]
    model = construir_modelo(input_shape=(LOOKBACK, X.shape[2]), n_outputs=n_outputs)

    early_stopping = EarlyStopping(
        monitor="val_loss", patience=5, restore_best_weights=True
    )
    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=3,
        batch_size=64,
        callbacks=[early_stopping],
        verbose=1,
    )

    loss, mae = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nEvaluación en test -> loss(mse): {loss:.4f} | mae: {mae:.4f}")

    # Predicción a partir de la última ventana disponible (último valor de
    # tiempo en el índice de `df`).
    ultima_ventana = features_scaled[-LOOKBACK:].reshape(1, LOOKBACK, X.shape[2])
    pred_scaled = model.predict(ultima_ventana, verbose=0)[0]

    # pred_scaled = [mech_5min, mech_10min, ebike_5min, ebike_10min]
    n_targets = len(TARGET_COLS)
    n_horizons = len(horizon_steps)
    pred_matrix_scaled = pred_scaled.reshape(n_horizons, n_targets)
    pred_matrix = scaler_y.inverse_transform(pred_matrix_scaled)

    ultimo_timestamp = df.index[-1]
    print(f"\nÚltimo timestamp disponible: {ultimo_timestamp}")
    for h_min, fila in zip(HORIZONTES_MIN, pred_matrix):
        pred_dt = ultimo_timestamp + pd.Timedelta(minutes=h_min)
        mech_pred, ebike_pred = np.maximum(fila, 0)
        print(
            f"+{h_min} min ({pred_dt}): "
            f"nbm≈{mech_pred:.2f} | nbe≈{ebike_pred:.2f}"
        )

    return model, scaler_x, scaler_y


if __name__ == "__main__":
    entrenar_y_predecir(30)
