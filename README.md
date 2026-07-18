<div align="center">

# 🚲 Bicing Cerca de Mí
### Predicción de disponibilidad en estaciones Bicing · Barcelona

![Barcelona](https://img.shields.io/badge/Ciudad-Barcelona-blue?style=for-the-badge&logo=mapbox)
![Data Science](https://img.shields.io/badge/Master-Data%20Science-orange?style=for-the-badge)
![Evolve](https://img.shields.io/badge/Escuela-Evolve-green?style=for-the-badge)
![Estado](https://img.shields.io/badge/Estado-En%20desarrollo-yellow?style=for-the-badge)

</div>

---

## 🎯 ¿Qué es este proyecto?

Una herramienta que localiza la **estación de Bicing más cercana** a un usuario en Barcelona, mostrando en tiempo real cuántas **bicicletas** puede coger y cuántos **anclajes** tiene libres para devolver una.

El sistema va un paso más allá: aplica **modelos de predicción de series temporales** para anticipar la disponibilidad futura en cada estación, evitando desplazamientos innecesarios.

---

## 🔍 El problema que resuelve

> Llegas a una estación Bicing y está vacía. O intentas devolver la bici y no hay anclajes libres.

Este proyecto resuelve exactamente eso:

| Necesidad | Lo que hace el sistema |
|---|---|
| 🚲 **Coger una bici** | Muestra estaciones cercanas con bicis disponibles ahora mismo |
| 🔒 **Devolver una bici** | Muestra estaciones cercanas con anclajes libres |
| 🔮 **Planificar** | Predice la disponibilidad futura mediante series temporales |

---

## ⚙️ ¿Cómo funciona?

```
📍 Tu ubicación
      │
      ▼
┌──────────────────────────────────────────┐
│         Estaciones cercanas              │
│                                          │
│  📍 Passeig de Gràcia  · 120m           │
│     🚲 Bicis: 5   🔒 Anclajes: 3        │
│                                          │
│  📍 Plaça Catalunya    · 340m           │
│     🚲 Bicis: 2   🔒 Anclajes: 8        │
│                                          │
│  📍 Eixample           · 480m           │
│     🚲 Bicis: 0   🔒 Anclajes: 12       │
└──────────────────────────────────────────┘
```

---

## 📦 Datos del proyecto

Los datos provienen del [Open Data Ajuntament de Barcelona](https://opendata-ajuntament.barcelona.cat) y del API de **Open-Meteo**, y se dividen en tres tipos:

### 🕐 Historial temporal — Estado de las estaciones

Archivos mensuales `.csv` con el estado en tiempo real de cada estación, ubicados en `docs/entregas/estado/`, desde julio de **2020** hasta septiembre de **2025**.

```
docs/data/
└── estado/
    ├── 2020_07_Juliol_BicingNou_ESTACIONS.csv
    ├── 2020_08_Agost_BicingNou_ESTACIONS.csv
    ├── ...
    └── 2025_09_Setembre_BicingNou_ESTACIONS.csv
```

> 📅 **63 archivos mensuales** · más de **5 años** de historial

Cada registro contiene: `station_id`, `num_bikes_available`, `num_bikes_available_types.mechanical`, `num_bikes_available_types.ebike`, `num_docks_available`, `is_installed`, `is_renting`, `is_returning`, `status` y `last_reported`.

---

### 📍 Datos estáticos — Información de las estaciones

Archivos `.csv` mensuales en `docs/entregas/informacion/` con las características fijas (o de cambio lento) de cada estación: ubicación GPS, capacidad total, dirección y tipo de estación.

```
docs/data/
└── informacion/
    ├── 2020_07_Juliol_BicingNou_INFORMACIO.csv
    ├── 2020_08_Agost_BicingNou_INFORMACIO.csv
    ├── ...
    └── 2025_09_Setembre_BicingNou_INFORMACIO.csv
```

| Campo | Descripción |
|---|---|
| `station_id` | Clave de unión con el historial |
| `lat` / `lon` | Coordenadas para calcular distancias |
| `capacity` | Total de anclajes |
| `address` | Nombre y dirección |
| `physical_configuration` | Tipo de estación |
| `is_charging_station` | Si dispone de carga para e-bikes |

---

### 🌤️ Datos meteorológicos — Open-Meteo

Datos horarios de Barcelona obtenidos de la API de **Open-Meteo** (`scripts/4.fetch_clima_barcelona.py`).

- **Coordenadas:** `41.3851`, `2.1734` (Barcelona)
- **Período:** `2020-07-01` a `2025-09-30`
- **Variables:** `temperature_2m`, `weather_code`
- **Zona horaria:** `Europe/Madrid`

| Campo | Descripción |
|---|---|
| `datetime` | Fecha y hora |
| `temperatura_c` | Temperatura a 2 m (°C) |
| `condicion` | Estado del tiempo traducido (`despejado`, `nublado`, `lluvia`, etc.) |

### 🔗 Relación entre datasets

```
Información de estaciones  +  Estado estaciones  +  Clima
      (dónde y cómo es)       (cómo está ahora)   (condiciones meteorológicas)
             │                        │                  │
             └────── station_id ──────┘                  │
                                    └────── datetime ────┘
```

> La clave `station_id` une las estaciones con su historial; `datetime` permite cruzar el estado de las estaciones con la información meteorológica.

---

## 📁 Estructura del repositorio

```
📂 Proyecto-Master-DataScience-Evolve-JuanPabloDelzo/
│
├── 📄 README.md                      ← Estás aquí
│
|── 📂 data/                          ← Datos raw (ignorado en Git)
│   |── 📂 estado/                    ← Historial mensual de estaciones
│   └── 📂 informacion/               ← Características de estaciones
|
├── 📂 docs/                          
│   └── 📂 entregas/ 
│       |── 📄 01_idea_producto.md    ← Descripción del producto
│       └── 📄 02_datos_necesarios.md ← Descripción de los datos
|
└── 📂 scripts/                       ← Scripts de carga y descarga
    |── 1.create_db.py
    |── 2.insert_informacion.py
    |── 3.insert_estado.py
    └── 4.fetch_clima_barcelona.py
```

---

## ✅ ¿Por qué es útil?

- ⏱️ **Ahorra tiempo** — no caminas hasta una estación vacía
- 😌 **Evita frustraciones** — sabes si hay anclajes antes de llegar
- 🔮 **Es predictivo** — anticipa la disponibilidad con series temporales
- 📊 **Basado en datos reales** — 5+ años de historial de Bicing Barcelona

---

<div align="center">

*Proyecto final · Máster en Data Science e IA · Evolve*

</div>
