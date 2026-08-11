# 🔍 Entrega 4 — Diseño del análisis y estrategia de modelado

---

## 1. Problema que se busca resolver

### 1.1 Qué ocurre actualmente y por qué supone un problema

Un usuario de Bicing que necesita **coger** o **devolver** una bicicleta solo puede consultar la disponibilidad **en el instante presente** (vía la app oficial o el propio panel de la estación). No existe ninguna forma de anticipar si, al llegar a la estación en los próximos minutos, seguirá habiendo bicis disponibles o anclajes libres.

Esto genera dos problemas concretos, ya descritos en `01_idea_producto.md`:

- **Desplazamientos en vano**: el usuario camina hasta una estación que, para cuando llega, se ha quedado sin bicis o sin anclajes, porque la disponibilidad cambia en cuestión de minutos (rotación alta en horas punta).
- **Decisiones subóptimas de planificación**: sin una estimación a corto plazo, el usuario no puede decidir con antelación si conviene esperar, cambiar de estación o salir unos minutos antes/después.

### 1.2 Quién utilizará el resultado y para qué decisión o acción

- **Usuario final de Bicing**: consulta la predicción de bicis mecánicas (`nbm`) y eléctricas (`nbe`) disponibles a **5 y 10 minutos vista** en la estación que le interesa, y decide si merece la pena desplazarse ahora, esperar o elegir otra estación cercana.
- **El propio equipo del proyecto** (en esta fase): usa el análisis exploratorio para validar qué variables aportan señal real al modelo antes de invertir tiempo de entrenamiento, y para detectar problemas de calidad de datos (huecos, outliers, estaciones con series demasiado cortas) que podrían sesgar la predicción.

### 1.3 Qué resultado concreto debería producir el proyecto para considerarse útil

- Una predicción numérica de `nbm` y `nbe` a **+5 min** y **+10 min** para una estación dada, con un error (MAE) claramente inferior al de una heurística naive (p. ej. "asumir que el valor no cambia respecto al último dato conocido").
- Evidencia, mediante el análisis de datos, de que las variables incorporadas al modelo (lags, hora, día de la semana, festivos, clima, anclajes libres) están justificadas por patrones reales observados en los datos y no añadidas de forma arbitraria.

---

## 2. Análisis de datos planteado y utilidad esperada

Este proyecto es, en esencia, un problema de **predicción de series temporales multivariante y multi-horizonte** (ver `03_modelo_datos.md`, sección 5.2: clase `LSTMbicis`). Por tanto, el análisis se centra en **tendencia, estacionalidad, autocorrelación y relación con variables exógenas**, no en técnicas propias de clasificación o de sistemas de recomendación.

### 2.1 Preguntas que queremos responder con los datos

1. ¿Cómo varía la disponibilidad de bicis mecánicas y eléctricas (`nbm`, `nbe`) a lo largo del día y de la semana en una estación? ¿Hay patrones horarios repetibles (p. ej. picos de salida por la mañana, de llegada por la tarde)?
2. ¿Cuánta información aporta el valor inmediatamente anterior (`lag_nbm`, `lag_nbe`) sobre el valor futuro? ¿A partir de qué horizonte deja de ser fiable como predictor por sí solo?
3. ¿Existe relación entre el clima (`temperature_c`, `rain`, `wind_speed_10m`, `cloud_cover`, `relative_humidity_2m`) y el uso de la estación (por ejemplo, menos rotación en días de lluvia)?
4. ¿Los días festivos (`is_holiday`) muestran un patrón de disponibilidad distinto al de un día laborable equivalente?
5. ¿Existe relación entre bicis disponibles (`nbm + nbe`) y anclajes libres (`nd`)? Dado que `capacity ≈ nbm + nbe + nd`, ¿aporta `nd` información adicional al modelo o es redundante?
6. ¿Cuántos huecos temporales existen en la serie de cada estación (instantes sin reporte) y qué proporción de las filas usadas para entrenar son en realidad **imputadas** (`is_imputed`) en lugar de observaciones reales?
7. ¿El comportamiento de la estación es estable a lo largo de los ~5 años de histórico, o ha cambiado (nuevas estaciones, cambios de capacidad, periodos sin datos)?

### 2.2 Análisis descriptivos, temporales y de relación entre variables

| Tipo de análisis | Qué se estudia | Utilidad para el proyecto |
|---|---|---|
| **Descriptivo** | Distribución de `nbm`, `nbe`, `nd` por estación: mínimo, máximo, media, huecos. | Detectar estaciones con series demasiado cortas, con capacidad casi nula, o con demasiados valores imputados como para ser fiables. |
| **Temporal (tendencia)** | Evolución de la disponibilidad media a lo largo de los años/meses por estación. | Verificar si el histórico completo (2021–2025) es representativo o si conviene acotar el periodo de entrenamiento. |
| **Temporal (estacionalidad)** | Perfil horario medio (`hour_sin/cos`) y semanal (`dow_sin/cos`) de `nbm`/`nbe`. | Confirma que la codificación cíclica de hora y día de la semana (ya implementada en `gold/bikes.py`) captura un patrón real y no ruido. |
| **Autocorrelación** | ACF/PACF de `nbm` y `nbe` a distintos lags (5, 10, 15... minutos). | Justifica el uso de `lag_nbm`/`lag_nbe` como feature y ayuda a decidir si el `LOOKBACK` de 24 pasos (2 horas) es adecuado o excesivo/insuficiente. |
| **Relación entre variables** | Correlación entre clima (`rain`, `temperature_c`, `wind_speed_10m`...) y disponibilidad; comparación `is_holiday` vs. laborable. | Confirma (o descarta) que las variables meteorológicas y de festivos aportan señal real, antes de mantenerlas en el modelo final. |
| **Relación estructural** | Correlación entre `nd` y `(nbm + nbe)`; verificación de `capacity ≈ nbm + nbe + nd`. | Decide si `nd` debe mantenerse como feature independiente (ver cambio ya aplicado en `03_modelo_datos.md`, sección 5.2) o si su aporte es marginal. |
| **Calidad de datos** | % de filas con `is_imputed = True` por estación; huecos más largos detectados. | Cuantifica cuánto "ruido de imputación" está viendo el modelo, y permite filtrar estaciones poco fiables del conjunto de entrenamiento/evaluación. |

### 2.3 Hipótesis o patrones que queremos comprobar

- **H1**: La disponibilidad de bicis presenta un patrón horario bimodal en días laborables (bajada por la mañana en estaciones residenciales, subida por la tarde) y un patrón más plano en festivos.
- **H2**: El valor en `t-1` (`lag_nbm`/`lag_nbe`) es el predictor individual más fuerte para el horizonte de +5 min, pero pierde poder explicativo en el horizonte de +10 min, donde las variables cíclicas y de clima ganan peso relativo.
- **H3**: La lluvia (`rain > 0`) reduce la rotación de bicis (menos viajes), lo que se traduce en menor variabilidad de `nbm`/`nbe` durante esas horas.
- **H4**: `nd` no es completamente redundante con `nbm + nbe` porque `capacity` puede variar ligeramente entre snapshots (mantenimiento, bicis fuera de servicio no contabilizadas en ningún contador), por lo que aporta señal adicional.

### 2.4 Visualizaciones, indicadores o conclusiones para el MVP

- **Serie temporal con banda de predicción**: `nbm`/`nbe` reales vs. predichos a +5 y +10 min para una estación seleccionable, tal como ya imprime `scripts/main.py` (`entrenar_y_predecir`) por consola — candidato a gráfico en el MVP.
- **Heatmap hora × día de la semana** de disponibilidad media, para justificar visualmente la estacionalidad horaria/semanal.
- **Indicador de error del modelo**: MAE/MSE en test frente al MAE de la heurística naive (persistencia del último valor), como métrica de "utilidad mínima" del modelo.
- **Indicador de calidad de datos por estación**: % de `is_imputed`, usado como filtro para decidir qué estaciones se muestran como fiables en el MVP.

### 2.5 Cómo ayuda este análisis a comprender el problema y apoyar el modelado

- Los análisis de **tendencia y estacionalidad** confirman (o corrigen) las variables temporales cíclicas ya incorporadas en `gold/bikes.py`, evitando incluir features sin justificación empírica.
- El análisis de **autocorrelación** valida la elección del `LOOKBACK` (24 pasos) y de los horizontes de predicción (5 y 10 min) definidos en `scripts/main.py`, o motiva su ajuste si los datos muestran otro comportamiento.
- El análisis de **relación con clima y festivos** decide qué variables exógenas merece la pena mantener en el vector de features, evitando sobreajustar el modelo con variables sin aporte real.
- El análisis de **calidad de datos** (huecos e imputación) es imprescindible antes de confiar en las métricas de evaluación del modelo: un MAE bajo en una estación con muchos valores imputados puede ser engañoso.

### 2.6 Justificación de la arquitectura de modelado: LSTM frente a ARIMA y RNN simple

Antes de implementar la clase `LSTMbicis` (`scripts/main.py`) se valoraron dos alternativas: el enfoque estadístico clásico **ARIMA/SARIMA(X)** y una **RNN simple** (recurrente "vanilla", sin puertas). Ambas se descartaron por motivos distintos, directamente relacionados con la naturaleza del problema y de los datos descritos en las secciones anteriores:

| Criterio | ARIMA / SARIMAX | RNN simple | LSTM (elegido) |
|---|---|---|---|
| **Nº de variables de entrada** | Modelo fundamentalmente **univariante**; SARIMAX admite regresores exógenos, pero de forma **lineal** y limitada en número. | Multivariante (igual que LSTM): acepta un vector de features por paso temporal. | **Multivariante** de forma natural: admite en un mismo vector de entrada los lags, las 6 variables cíclicas temporales, `nd`, 5 variables de clima e `is_holiday` sin transformar el problema. |
| **Nº de salidas (multi-horizonte)** | Requiere un modelo (o una reestimación) por cada horizonte de predicción (+5 min, +10 min), o iterar la predicción paso a paso acumulando error. | Multi-salida posible (igual que LSTM), vía capa `Dense` final. | Predice **ambos horizontes y ambos targets (`nbm`, `nbe`) en una sola pasada**, gracias a la capa `Dense(n_outputs)` final. |
| **Relaciones no lineales** | Asume relaciones lineales entre la serie, sus rezagos y los regresores exógenos. La relación entre clima, hora del día y disponibilidad de bicis es marcadamente **no lineal** (ver hipótesis H1–H3, sección 2.3). | Captura no linealidades (activación `tanh`), igual que LSTM, pero con menor capacidad práctica de aprenderlas en secuencias largas (ver fila siguiente). | Las capas `LSTM`/`Dense` con activaciones no lineales (`tanh`, `relu`) capturan interacciones complejas (p. ej. "lluvia solo reduce la rotación en horas punta") sin necesidad de especificarlas a mano. |
| **Dependencias a largo plazo (gradiente)** | No aplica (no es una red recurrente). | Sufre el problema del **gradiente desvanecente/explosivo** al retropropagar a través de muchos pasos temporales; con `LOOKBACK = 24` pasos (2 horas a 5 min) tiende a "olvidar" la información de los primeros pasos de la ventana. | Las puertas de olvido/entrada/salida (`forget/input/output gate`) mantienen un estado de celda (`cell state`) diseñado explícitamente para propagar gradiente e información a lo largo de las 24 posiciones de la ventana sin degradarse. |
| **Estacionariedad** | Exige (o transforma mediante diferenciación) series estacionarias; hay que decidir manualmente el orden de diferenciación e identificar `(p,d,q)(P,D,Q)` por estación. | No requiere estacionariedad explícita (comparte esta ventaja con LSTM). | No requiere estacionariedad explícita: el escalado (`MinMaxScaler`) y las ventanas de `LOOKBACK` bastan para que la red aprenda la dinámica directamente de los datos. |
| **Escalabilidad a múltiples estaciones** | Habría que **ajustar y mantener un modelo ARIMA independiente por cada estación** (cientos de estaciones en Bicing), con sus propios órdenes e hiperparámetros. | Igual de escalable que LSTM en diseño, pero con peor rendimiento esperado en la práctica (ver dependencias a largo plazo). | El mismo diseño de `LSTMbicis` se reutiliza para cualquier `station_id` sin reajuste manual de hiperparámetros estructurales; en el futuro es viable entrenar un único modelo compartido entre estaciones similares. |
| **Frecuencia y ruido de imputación** | Sensible a huecos e imputaciones (`is_imputed`); la diferenciación amplifica el ruido de los tramos rellenados por forward-fill. | Puede usar `is_imputed` como feature (igual que LSTM), pero el olvido temprano de información limita su aprovechamiento a lo largo de toda la ventana. | La red puede usar `is_imputed` como una feature más, dejando que el propio modelo aprenda a ponderar la fiabilidad del dato en lugar de asumir que toda la serie es igualmente fiable. |

**Por qué se descarta la RNN simple frente a LSTM en concreto**: la arquitectura de `LSTMbicis` usa una ventana de `LOOKBACK = 24` pasos (2 horas de histórico a resolución de 5 minutos) para predecir hasta 2 pasos por delante. Una RNN "vanilla" retropropaga el error a través de esas 24 posiciones sin ningún mecanismo de control del gradiente, por lo que en la práctica le cuesta aprender relaciones entre el inicio de la ventana (p. ej. la disponibilidad hace 2 horas) y el instante actual, especialmente cuando se combinan con las 6 variables cíclicas y las 5 variables de clima en cada paso. La LSTM resuelve esto mediante sus puertas y el estado de celda, manteniendo memoria selectiva a lo largo de toda la ventana, lo que encaja mejor con el `LOOKBACK` ya elegido para este problema.

**Conclusión**: dado que el problema es multivariante (clima + calendario + lags + `nd`), multi-salida (`nbm` y `nbe`), multi-horizonte (+5 y +10 min), con relaciones no lineales esperadas y con una ventana de entrada de 24 pasos donde interesa retener información de todo el histórico reciente, un modelo **LSTM** encaja mejor que ARIMA/SARIMAX (por su linealidad y falta de soporte multivariante nativo) y mejor que una **RNN simple** (por su dificultad para aprender dependencias a lo largo de toda la ventana de `LOOKBACK`). ARIMA y la RNN simple seguirían siendo razonables como **baselines** (junto con la heurística naive de la sección 1.3) para cuantificar cuánto mejora realmente la LSTM, pero no como arquitectura final del sistema.

---

## Trazabilidad con entregas anteriores

- **Respecto a `02_datos_necesarios.md`**: se confirma que las variables meteorológicas ya redefinidas en esa entrega (`temperature_c`, `relative_humidity_2m`, `rain`, `cloud_cover`, `wind_speed_10m`) son precisamente las que este análisis evaluará por su relación con la disponibilidad; no se añaden ni eliminan fuentes de datos nuevas.
- **Respecto a `03_modelo_datos.md`**: la inclusión de `nd` (anclajes libres) como feature de entrada, ya documentada en la sección 5.2 de esa entrega, se somete aquí a verificación empírica (hipótesis H4) en lugar de asumirse sin más. Si el análisis mostrara que `nd` es completamente redundante, se actualizaría `03_modelo_datos.md` para reflejar su exclusión, dejando constancia del motivo.

