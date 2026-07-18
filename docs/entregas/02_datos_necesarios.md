# 📦 Datos Necesarios para el Proyecto

Para predecir la disponibilidad de bicicletas y anclajes en las estaciones, se requerirán dos tipos de datos bien diferenciados. Dichos datos están disponibles en la página web del ayuntamiento de Barcelona y se han descargado en la carpeta `docs/entregas/`:  

- [Información de las estaciones Bicing](https://opendata-ajuntament.barcelona.cat/data/es/dataset/informacio-estacions-bicing)
- [Estado de las estaciones Bicing](https://opendata-ajuntament.barcelona.cat/data/es/dataset/estat-estacions-bicing)

Además, se enriquece el dataset con datos meteorológicos históricos de Barcelona obtenidos de la API de **Open-Meteo** (`scripts/4.fetch_clima_barcelona.py`).

---

## ¿Qué datos tenemos?

```
docs/data/
├── estado/                     ← Historial temporal de cada estación (CSV mensuales)
│   ├── 2020_07_Juliol_BicingNou_ESTACIONS.csv
│   ├── 2020_08_Agost_BicingNou_ESTACIONS.csv
│   ├── ...
│   └── 2025_09_Setembre_BicingNou_ESTACIONS.csv
│
└── informacion/                ← Características de cada estación (CSV mensuales)
    ├── 2020_07_Juliol_BicingNou_INFORMACIO.csv
    ├── 2020_08_Agost_BicingNou_INFORMACIO.csv
    ├── ...
    └── 2025_09_Setembre_BicingNou_INFORMACIO.csv
```

---

## 1. 🕐 Estado de las Estaciones — Datos Temporales

Son archivos mensuales en formato `.csv` ubicados en `docs/entregas/estado/`, organizados por año y mes (desde julio de **2020** hasta septiembre de **2025**). Cada archivo captura el **estado en tiempo real** de todas las estaciones, registrando múltiples instantáneas a lo largo del mes.

**Nombre de archivo de ejemplo:**
```
docs/entregas/estado/2024_03_Marc_BicingNou_ESTACIONS.csv
```

### ¿Qué contiene cada registro?

| Campo | Descripción |
|---|---|
| `station_id` | Identificador único de la estación |
| `num_bikes_available` | Total de bicis disponibles para coger |
| `num_bikes_available_types.mechanical` | Bicis mecánicas disponibles |
| `num_bikes_available_types.ebike` | Bicis eléctricas disponibles |
| `num_docks_available` | Anclajes libres para devolver |
| `is_installed` | Si la estación está instalada (1 = sí) |
| `is_renting` | Si está activa para alquiler (1 = sí) |
| `is_returning` | Si acepta devoluciones (1 = sí) |
| `status` | Estado operativo (`IN_SERVICE`, etc.) |
| `last_reported` | Marca de tiempo del último reporte (Unix) |

### ¿Cómo se ve la dimensión temporal?

```
Tiempo ──────────────────────────────────────────────────────────►

 Jul    Dic    Ene    Dic    Ene    Dic    Ene    Dic    Ene    Oct
 2020   2020   2021   2021   2022   2022   2023   2023   2024   2025
  │      │      │      │      │      │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
 [==== 2020 ====][======= 2021 =======][======= 2022 =======] ...
```

> 📅 En total: **63 archivos mensuales** en `docs/entregas/estado/`, cubriendo **más de 5 años** de historial.

---

## 2. 📍 Información de las Estaciones — Datos Estáticos

Archivos `.csv` mensuales en `docs/entregas/informacion/` con las **características fijas** de cada estación (aunque pueden existir pequeñas variaciones mensuales, como cambios de capacidad o dirección). Describen dónde está cada estación y cómo es.

**Archivo de ejemplo:** `docs/entregas/informacion/2024_03_Marc_BicingNou_INFORMACIO.csv`

### ¿Qué contiene?

| Campo | Descripción |
|---|---|
| `station_id` | Identificador único (clave de unión con el otro dataset) |
| `name` | Nombre o dirección de la estación |
| `lat` / `lon` | Coordenadas geográficas |
| `altitude` | Altitud en metros |
| `address` | Dirección postal |
| `capacity` | Número total de anclajes de la estación |
| `is_charging_station` | Si tiene carga para e-bikes |
| `physical_configuration` | Tipo de estación (ej. `ELECTRICBIKESTATION`) |

### ¿Cómo se relacionan los dos datasets?

```
Informacion_estaciones.csv          Estado estaciones (mensual)
┌──────────────────────┐            ┌────────────────────────────┐
│ station_id  │ lat/lon│            │ station_id │ num_bikes_... │
│ station_id  │ capacit│  ◄──────►  │ station_id │ num_docks_... │
│ station_id  │ address│  station_id│ station_id │ last_reported │
└──────────────────────┘            └────────────────────────────┘
       (dónde está y cómo es)              (cómo está en cada momento)
```

---

## 3. 🌤️ Datos Meteorológicos — Open-Meteo

Para enriquecer el modelo y analizar la relación entre el clima y el uso de Bicing, se descargan datos horarios de Barcelona mediante la API de **Open-Meteo** (`scripts/4.fetch_clima_barcelona.py`).

- **Coordenadas:** latitud `41.3851`, longitud `2.1734` (Barcelona)
- **Período:** `2020-07-01` a `2025-09-30`
- **Variables horarias:** `temperature_2m`, `weather_code`
- **Zona horaria:** `Europe/Madrid`

**Campos que genera el script:**

| Campo | Descripción |
|---|---|
| `datetime` | Fecha y hora del registro (`YYYY-MM-DD HH:MM:00`) |
| `temperatura_c` | Temperatura a 2 metros en grados Celsius |
| `condicion` | Condición meteorológica traducida a partir de `weather_code`: `despejado`, `nublado`, `niebla`, `lluvia`, `nieve`, `tormenta` o `desconocido` |

---

## ¿Por qué necesitamos estos datos?

| Necesidad | Dataset / fuente que lo resuelve |
|---|---|
| Saber **dónde** está cada estación | `docs/entregas/informacion/` |
| Conocer la **capacidad** total de anclajes | `docs/entregas/informacion/` |
| Ver el **historial** de disponibilidad | `docs/entregas/estado/` (mensual) |
| Entrenar un modelo de **predicción** | `docs/entregas/estado/` (serie temporal) |
| Filtrar por **tipo de bici** (mecánica / eléctrica) | `docs/entregas/estado/` |
| Incorporar el impacto del **clima** | API Open-Meteo → `scripts/4.fetch_clima_barcelona.py` |

---


