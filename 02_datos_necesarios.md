# 📦 Datos Necesarios para el Proyecto

Para predecir la disponibilidad de bicicletas y anclajes en las estaciones Bicing, se utilizarán métodos de **predicción de series temporales**. Esto requiere dos tipos de datos bien diferenciados. 

>La información y los estados de las estaciones provienen de la página del Ayuntamiento de Barcelona:
- [Estado de las estaciones](https://opendata-ajuntament.barcelona.cat/data/es/dataset/estat-estacions-bicing)
- [Información de las estaciones](https://opendata-ajuntament.barcelona.cat/data/es/dataset/informacio-estacions-bicing)

---

## ¿Qué datos tenemos?

```
Datos/
├── Estado estaciones/          ← Historial temporal de cada estación
│   ├── 2020/  (6 meses)
│   ├── 2021/  (12 meses)
│   ├── 2022/  (12 meses)
│   ├── 2023/  (12 meses)
│   ├── 2024/  (12 meses)
│   └── 2025/  (10 meses)
│
└── Informacion_estaciones.csv  ← Características fijas de cada estación
```

---

## 1. 🕐 Estado de las Estaciones — Datos Temporales

Son archivos mensuales en formato `.csv`, organizados por año (desde julio de **2020** hasta **octubre de 2025**). Cada archivo captura el **estado en tiempo real** de todas las estaciones, registrando múltiples instantáneas a lo largo del mes.

**Nombre de archivo de ejemplo:**
```
2024_03_Marc_BicingNou_ESTACIONS.csv
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

> 📅 En total: **~64 archivos mensuales**, cubriendo **más de 5 años** de historial.

---

## 2. 📍 Información de las Estaciones — Datos Estáticos

Un único archivo `.csv` con las **características fijas** de cada estación. No cambia en el tiempo: describe dónde está cada estación y cómo es.

**Archivo:** `Informacion_estaciones.csv`

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

## ¿Por qué necesitamos estos datos?

| Necesidad | Dataset que lo resuelve |
|---|---|
| Saber **dónde** está cada estación | `Informacion_estaciones.csv` |
| Conocer la **capacidad** total de anclajes | `Informacion_estaciones.csv` |
| Ver el **historial** de disponibilidad | `Estado estaciones/` (mensual) |
| Entrenar un modelo de **predicción** | `Estado estaciones/` (serie temporal) |
| Filtrar por **tipo de bici** (mecánica / eléctrica) | `Estado estaciones/` |

---


