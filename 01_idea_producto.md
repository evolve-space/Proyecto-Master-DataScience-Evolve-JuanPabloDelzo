# 🚲 Bicing Cerca de Mí 

## ¿Qué es?

Una herramienta sencilla que te ayuda a encontrar **la estación de Bicing más cercana** a tu ubicación en Barcelona, tanto si quieres **coger una bicicleta** como si quieres **devolver una**.

---

## ¿Para qué sirve?

Cuando usas el servicio público de bicicletas `Bicing` en Barcelona, tienes dos necesidades principales:

1. **Coger una bici** → necesitas saber qué estación cercana tiene bicis disponibles.
2. **Devolver una bici** → necesitas saber qué estación cercana tiene anclajes libres.

Este producto resuelve ambas situaciones de forma rápida y clara.

---

## ¿Cómo funciona?

1. El usuario indica su ubicación (o se detecta automáticamente).
2. El sistema localiza las estaciones de Bicing más cercanas.
3. Se muestra para cada estación:
   - 🚲 **Bicicletas disponibles** para coger.
   - 🔒 **Anclajes libres** para devolver.

---

## Ejemplo visual del flujo

```
📍 Tu ubicación
      │
      ▼
┌─────────────────────────────────────┐
│  Estaciones cercanas                │
│                                     │
│  📍 Estación Passeig de Gràcia     │
│     🚲 Bicis disponibles: 5        │
│     🔒 Anclajes libres: 3          │
│                                     │
│  📍 Estación Plaça Catalunya       │
│     🚲 Bicis disponibles: 2        │
│     🔒 Anclajes libres: 8          │
│                                     │
│  📍 Estación Eixample              │
│     🚲 Bicis disponibles: 0        │
│     🔒 Anclajes libres: 12         │
└─────────────────────────────────────┘
```

---

## ¿Qué información muestra?

| Información | Descripción |
|---|---|
| 📍 Nombre de la estación | Identificación de la parada Bicing |
| 📏 Distancia | Metros desde tu posición actual |
| 🚲 Bicis disponibles | Cuántas bicicletas puedes coger ahora mismo |
| 🔒 Anclajes libres | Cuántos sitios tienes para devolver la bici |

---

## ¿Por qué es útil?

- **Ahorra tiempo**: no caminas hasta una estación vacía.
- **Evita frustraciones**: sabes de antemano si hay anclajes libres para devolver.
- **Es simple**: la información es directa, sin tecnicismos.
- **Datos en tiempo real**: refleja la disponibilidad actual de cada estación.

---

## Tecnología base

Los datos provienen del [Ajuntament de Barcelona](https://opendata-ajuntament.barcelona.cat) que ofrece información actualizada sobre el estado de todas las estaciones de la red.

---


