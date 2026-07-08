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

Los datos provienen del [Open Data Ajuntament de Barcelona](https://opendata-ajuntament.barcelona.cat) y se dividen en dos tipos:

### 🕐 Historial temporal — Estado de las estaciones

Archivos mensuales con el estado en tiempo real de cada estación, desde julio de **2020** hasta octubre de **2025**.

```
Datos/
└── Estado estaciones/
    ├── 2020/  · · · · 6 meses
    ├── 2021/  · · · · 12 meses
    ├── 2022/  · · · · 12 meses
    ├── 2023/  · · · · 12 meses
    ├── 2024/  · · · · 12 meses
    └── 2025/  · · · · 10 meses
```

> 📅 **~64 archivos mensuales** · más de **5 años** de historial

Cada registro contiene: `bicis disponibles`, `anclajes libres`, `tipo de bici` (mecánica / eléctrica), `estado operativo`, y `marca de tiempo`.

---

### 📍 Datos estáticos — Información de las estaciones

Un único archivo `Informacion_estaciones.csv` con las características fijas de cada estación: ubicación GPS, capacidad total, dirección y tipo de estación.

```
Informacion_estaciones.csv
 ├── station_id   ← clave de unión con el historial
 ├── lat / lon    ← coordenadas para calcular distancias
 ├── capacity     ← total de anclajes
 └── address      ← nombre y dirección
```

---

### 🔗 Relación entre datasets

```
Informacion_estaciones.csv     +     Estado estaciones (mensual)
      (dónde está y cómo es)              (cómo está en cada momento)
             │                                       │
             └─────────── station_id ────────────────┘
```

---

## 📁 Estructura del repositorio

```
📂 Proyecto-Master-DataScience-Evolve-JuanPabloDelzo/
│
├── 📄 README.md                   ← Estás aquí
├── 📄 01_idea-producto.md         ← Descripción del producto
├── 📄 02_datos-necesarios.md      ← Descripción de los datos
│
└── 📂 Datos/                      ← (ignorado en Git)
    ├── 📂 Estado estaciones/
    └── 📄 Informacion_estaciones.csv
```

---

## ✅ ¿Por qué es útil?

- ⏱️ **Ahorra tiempo** — no caminas hasta una estación vacía
- 😌 **Evita frustraciones** — sabes si hay anclajes antes de llegar
- 🔮 **Es predictivo** — anticipa la disponibilidad con series temporales
- 📊 **Basado en datos reales** — 5+ años de historial de Bicing Barcelona

---

<div align="center">

*Proyecto académico · Master en Data Science · Evolve*

</div>
