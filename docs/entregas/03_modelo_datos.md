# 🗂️ Modelo de Datos y Capa Gold

Este documento describe el diseño técnico del modelo de datos del proyecto **Bicing Cerca de Mí**: desde la capa **Bronze** (fuentes originales sin procesar), pasando por la capa **Silver** en MySQL (datos limpios y modelados) hasta la capa **Gold**, que expone los resultados de predicción a través de una **API** para el frontend Angular.

---

## 1. Arquitectura de capas

```
Bronze (fuentes)      Silver (MySQL)            Gold (analítico)
    │                        │                          │
    ├── data/informacion/    │   ┌──────────────┐       │
    │        CSV             │   │  informacion │       │
    │          │             │   └──────────────┘       │
    ├── data/estado/         │          │               │
    │        CSV             │          ▼               │
    │          │             │   ┌──────────────┐       │
    │          └────────────►│   │    estado    │       │
    │                        │   └──────────────┘       │
    └── Open-Meteo API       │          │               │
             JSON            │          ▼               │
                             │   ┌──────────────┐       │
                             │   │    clima     │       │
                             │   └──────────────┘       │
                             │                          │
                             └──────────────────────────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │   API Gold   │
                                   │ predicciones │
                                   │   (DL/TS)    │
                                   └──────────────┘
```

| Capa | Descripción | Ubicación / implementación |
|---|---|---|
| **Bronze** | Datos originales sin transformar: CSV mensuales del Ajuntament y respuesta JSON de Open-Meteo. | `data/informacion/`, `data/estado/`, `scripts/silver/4.fetch_clima_bcn.py` |
| **Silver** | Datos limpios, validados y modelados en MySQL con PKs, FKs y tipos correctos. | Base de datos `Bicing` (`scripts/silver/1.create_db.py`, `scripts/silver/2.insert_informacion.py`, `scripts/silver/3.insert_estado.py`) |
| **Gold** | Resultados de predicción de bicicletas y anclajes mediante series temporales con deep learning, a partir de MySQL y el clima. | API REST que expone predicciones en JSON; consumida por el frontend Angular. |

---

## 2. Capa Bronze (fuentes originales)

Esta capa contiene los datos tal cual se reciben. No se aplica ninguna transformación de negocio; únicamente se describen los esquemas originales.

### 2.1 Datos de estaciones (`data/informacion/`)

Archivos CSV mensuales con el prefijo `*_BicingNou_INFORMACIO.csv`. Cada archivo describe las estaciones existentes en ese mes.

| Campo | Tipo en origen | Descripción |
|---|---|---|
| `station_id` | entero | Identificador único de la estación. |
| `physical_configuration` | texto | Tipo de estación (`ELECTRICBIKESTATION`, etc.). |
| `lat` / `lon` | float | Coordenadas geográficas. |
| `address` | texto | Dirección o nombre de la calle. |
| `post_code` | texto | Código postal (se normaliza a 5 dígitos). |
| `capacity` | entero | Número total de anclajes. |
| `last_updated` | entero (epoch s) | Última actualización del registro. |

### 2.2 Datos de estado (`data/estado/`)

Archivos CSV mensuales con el prefijo `*_BicingNou_ESTACIONS.csv`. Cada fila es una instantánea del estado de una estación.

| Campo | Tipo en origen | Descripción |
|---|---|---|
| `station_id` | entero | Identificador de la estación. |
| `num_bikes_available` | entero | Bicis disponibles. |
| `num_bikes_available_types.mechanical` | entero | Bicis mecánicas disponibles. |
| `num_bikes_available_types.ebike` | entero | Bicis eléctricas disponibles. |
| `num_docks_available` | entero | Anclajes libres. |
| `is_installed` / `is_renting` / `is_returning` | entero | Flags operativos (no se cargan en el modelo actual). |
| `status` | texto | Estado operativo (`IN_SERVICE`, etc.). |
| `last_reported` | entero (epoch s) | Marca de tiempo de la instantánea. |

### 2.3 Datos meteorológicos (Open-Meteo)

El script `scripts/silver/4.fetch_clima_bcn.py` consulta la API de Open-Meteo para Barcelona (lat=41.3851, lon=2.1734) en el rango 2021-01-01 a 2025-09-30.

| Campo generado | Tipo | Descripción |
|---|---|---|
| `date` | `str` | Fecha (`YYYY-MM-DD`). |
| `hour` | `int` | Hora (`HH`). |
| `temp_c` | float | Temperatura a 2 metros en °C. |
| `condicion` | texto | Clasificación textual del `weather_code` (`despejado`, `nublado`, `lluvia`, `nieve`, `tormenta`, `niebla`, `desconocido`). |
| `is_holiday` | bool | `True` si la fecha es festivo en Cataluña. |

---

## 3. Capa Silver: base de datos MySQL

La base de datos `Bicing` constituye la capa Silver. Aquí los datos ya han sido limpiados, tipados, deduplicados y relacionados mediante claves primarias y foráneas. Los scripts `2.insert_informacion.py` y `3.insert_estado.py` realizan la carga desde Bronze hasta esta capa.

La base de datos `Bicing` se crea con `scripts/silver/1.create_db.py` con codificación `utf8mb4_unicode_ci`.

### 3.1 Tabla `informacion`

```sql
CREATE TABLE IF NOT EXISTS informacion (
    station_id INT(3) NOT NULL,
    physical_configuration VARCHAR(30),
    latitud FLOAT,
    longitud FLOAT,
    address VARCHAR(100),
    post_code VARCHAR(5),
    capacity INT(2),
    last_update TIMESTAMP,
    PRIMARY KEY (station_id)
);
```

| Campo | Tipo | PK | Descripción |
|---|---|---|---|
| `station_id` | `INT(3)` | ✅ | Identificador único de estación. |
| `physical_configuration` | `VARCHAR(30)` | | Tipo de estación. |
| `latitud` | `FLOAT` | | Latitud (renombrado desde `lat`). |
| `longitud` | `FLOAT` | | Longitud (renombrado desde `lon`). |
| `address` | `VARCHAR(100)` | | Dirección. |
| `post_code` | `VARCHAR(5)` | | CP normalizado a 5 dígitos. |
| `capacity` | `INT(2)` | | Capacidad total de anclajes. |
| `last_update` | `TIMESTAMP` | | Fecha de última actualización (renombrado desde `last_updated`, convertido de epoch). |

### 3.2 Tabla `estado`

```sql
CREATE TABLE IF NOT EXISTS estado (
    station_id INT(3) NOT NULL,
    num_bikes_available INT(2),
    num_bikes_available_mechanical INT(2),
    num_bikes_available_ebike INT(2),
    num_docks_available INT(2),
    datetime TIMESTAMP,
    PRIMARY KEY (station_id, datetime),
    CONSTRAINT fk_estado_informacion
        FOREIGN KEY (station_id) REFERENCES informacion(station_id)
);
```

| Campo | Tipo | PK | Descripción |
|---|---|---|---|
| `station_id` | `INT(3)` | ✅ | Parte de la clave primaria; referencia a `informacion`. |
| `datetime` | `TIMESTAMP` | ✅ | Parte de la clave primaria; generado desde `last_reported` (epoch s). |
| `num_bikes_available` | `INT(2)` | | Bicis totales disponibles. |
| `num_bikes_available_mechanical` | `INT(2)` | | Bicis mecánicas disponibles. |
| `num_bikes_available_ebike` | `INT(2)` | | Bicis eléctricas disponibles. |
| `num_docks_available` | `INT(2)` | | Anclajes libres. |

> **Restricciones:** la clave primaria compuesta `(station_id, datetime)` impide duplicados de instantáneas. La FK garantiza que cada `station_id` de `estado` exista en `informacion`.

---

## 4. Pipeline Bronze → Silver (scripts de carga)

Los scripts de la carpeta `scripts/silver/` leen los archivos CSV de la capa Bronze, aplican limpieza y normalización, e insertan el resultado en la capa Silver de MySQL.

### 4.1 `scripts/silver/2.insert_informacion.py`

- Lectura con **Polars** probando codificaciones `utf8`, `windows-1252` y `utf8-lossy`.
- Selección de columnas presentes en cada CSV.
- Conversión de `station_id` a entero.
- Renombrado de `lat` / `lon` a `latitud` / `longitud`.
- Conversión de `last_updated` (epoch s) a `last_update` tipo `datetime`.
- Normalización de `post_code` a 5 dígitos con relleno de ceros.
- Deduplicación por `station_id` conservando el último registro.
- Inserción por lotes de 10.000 con `ON DUPLICATE KEY UPDATE` para mantener la información más reciente.

### 4.2 `scripts/silver/3.insert_estado.py`

- Lectura por lotes con `pl.scan_csv().collect_batches()` (`chunk_size=200_000`) para reducir uso de memoria.
- Schema override a `Float64` en columnas numéricas y a `Utf8` para `status`, para evitar errores de parseo.
- Filtrado de registros donde `status == "IN_SERVICE"`.
- Renombrado de `num_bikes_available_types.mechanical` / `.ebike` y conversión de `last_reported` a `datetime`.
- Deduplicación dentro de cada lote por `(station_id, datetime)`.
- Inserción por lotes de 5.000 filas con `INSERT IGNORE` para evitar bloqueos por duplicados.

### 4.3 `scripts/silver/4.fetch_clima_bcn.py`

- Consulta anual a `https://archive-api.open-meteo.com/v1/archive`.
- Variables `temperature_2m` y `weather_code`.
- Mapea los códigos WMO a etiquetas textuales en `condicion`.
- Devuelve un `DataFrame` con una fila por hora.

---

## 5. Capa Gold — Predicción vía API

La capa Gold **no persiste las predicciones en la base de datos**. El modelo de *deep learning* de series temporales se ejecuta a demanda (o mediante un job programado), genera las predicciones y un servicio **API REST** las expone en formato **JSON** para que el frontend Angular las consuma directamente.

### 5.1 Entrada del modelo (features)

El modelo consume los siguientes datos de la capa Silver:

- **Histórico de disponibilidad** (`estado`): ventanas temporales de `num_bikes_available`, `num_docks_available`, mecánicas, eléctricas y anclajes libres.
- **Metadatos de estación** (`informacion`): `latitud`, `longitud`, `capacity`, `physical_configuration`, `post_code`.
- **Meteorología** (`clima` o el `DataFrame` generado por `scripts/silver/4.fetch_clima_bcn.py`): `date`, `hour`, `temp_c`, `condicion` e `is_holiday`.
- **Características temporales**: hora, día de la semana, mes, festivo/puente, etc.

### 5.2 Arquitectura del modelo (propuesta)

- **Enfoque**: predicción multivariante y multistep de series temporales.
- **Arquitectura**: red neuronal profunda (LSTM, GRU, Transformer o Temporal Fusion Transformer) que recibe secuencias de histórico y variables exógenas (clima + estáticas).
- **Salidas**:
  - Número estimado de bicis disponibles (`predicted_num_bikes_available`, mecánicas y eléctricas).
  - Número estimado de anclajes libres (`predicted_num_docks_available`).
- **Frecuencia**: predicción a corto plazo, p. ej. próximos 15–60 minutos por estación.
- **Inferencia**: el modelo se carga en el servicio API; cada petición ejecuta una predicción o recupera un caché reciente (p. ej. Redis/memoria), sin necesidad de tablas `gold.*` en MySQL.

### 5.3 API de predicciones (contrato propuesto)

#### `GET /api/predictions/{station_id}?horizon=60`

Devuelve la predicción para una estación concreta en el horizonte solicitado (minutos).

**Respuesta 200:**

```json
{
  "station_id": 1,
  "address": "Passeig de Gràcia, 1",
  "latitud": 41.3925,
  "longitud": 2.1651,
  "horizon_minutes": 60,
  "forecast": [
    {
      "forecast_datetime": "2025-10-01 09:00:00",
      "predicted_num_bikes_available": 5,
      "predicted_num_bikes_available_mechanical": 2,
      "predicted_num_bikes_available_ebike": 3,
      "predicted_num_docks_available": 8,
    }
  ],
  "model_version": "lstm-v1.2",
  "generated_at": "2025-09-30 20:00:00"
}
```

#### `GET /api/predictions/nearby?lat=41.3851&lon=2.1734&radius=500&horizon=60`

Devuelve predicciones para todas las estaciones dentro de un radio (metros).

#### `POST /api/predictions/refresh` *(admin/training)*

Fuerza la recarga del modelo o un nuevo entrenamiento. No se recomienda exponer sin autenticación.

### 5.4 Flujo de la capa Gold

```
Silver (MySQL)                         Gold (API)
   │                                          │
   ├── estado  ─────┐                         │
   ├── informacion ─┼─►  Modelo DL series     ├──► GET /api/predictions/{id}
   └── clima    ────┘      temporales         ├──► GET /api/predictions/nearby
                                              │
                                              ▼
                                       Frontend Angular
```

### 5.5 Relación capa Gold con el resto

- El modelo consume `estado`, `informacion` y `clima` de la capa Silver.
- Las predicciones se generan y se sirven directamente por la API; no se almacenan en MySQL.
- El frontend Angular puede enriquecer la predicción con datos estáticos de `informacion` (dirección, capacidad, coordenadas) y del clima.

### 5.6 Ejemplo de consumo desde Angular

```typescript
// Servicio Angular
getPrediction(stationId: number, horizon: number = 60): Observable<PredictionResponse> {
  return this.http.get<PredictionResponse>(
    `${this.apiUrl}/predictions/${stationId}?horizon=${horizon}`
  );
}
```

---

## 6. Diagrama entidad-relación (capa Silver)

```
┌─────────────────┐         ┌────────────────────┐
│   informacion   │         │       estado       │
│   (dimensión)   │         │      (hechos)      │
├─────────────────┤         ├────────────────────┤
│ PK station_id   │◄────────│ PK/FK station_id   │
│    latitud      │    1:N  │ PK datetime        │
│    longitud     │         │    num_bikes_...   │
│    capacity     │         │    num_docks_...   │
│    address      │         └────────────────────┘
│    post_code    │                   │
│    physical_... │                   │ N:1
└─────────────────┘                   ▼
                            ┌────────────────────┐
                            │       clima        │
                            │    (dimensión)     │
                            ├────────────────────┤
                            │ PK datetime        │
                            │    temperatura_c   │
                            │    condicion       │
                            └────────────────────┘
```

---

## 7. Consideraciones técnicas

- **Codificación:** toda la base de datos usa `utf8mb4_unicode_ci` para soportar caracteres catalanes y espacios.
- **Batching:** las inserciones se hacen en lotes (10.000 para `informacion`, 5.000 para `estado`) para evitar problemas de memoria y `max_allowed_packet`.
- **Idempotencia:** `informacion` usa `ON DUPLICATE KEY UPDATE`; `estado` usa `INSERT IGNORE` para evitar bloqueos por duplicados.
- **Memoria:** el script `3.insert_estado.py` lee CSV en lotes con Polars (`scan_csv().collect_batches()`) para poder procesar los ~63 archivos sin cargarlos enteros en RAM.
- **Clima:** actualmente `scripts/silver/4.fetch_clima_bcn.py` devuelve un DataFrame con `date`, `hour`, `temp_c` y `condicion`. El script `scripts/gold/merge_bicis_clima.py` une este DataFrame con la tabla `estado` de MySQL a partir de `date` y `hour` para construir el dataset de entrenamiento de la capa Gold.
