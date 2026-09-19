# Revisión del exportador de fundamentals

## Objetivo

Revisar `scripts/download_fundamentals.py` contra los problemas detectados en la descarga histórica de ForexFactory. La revisión debe distinguir entre hechos verificados, supuestos y problemas todavía abiertos.

## Cambios ya aplicados

- `Time` acepta `DD/MM/YYYY HH:MM`, además de formatos cortos.
- Las horas programadas se convierten explícitamente desde `America/New_York` a UTC.
- La consolidación genera `calendar.parquet` también en ejecuciones parciales.
- Se conserva el ID original como `source_event_id`.
- `n/a` se normaliza a raw vacío y valor numérico `None`.
- Impacto `n/a` se normaliza como `holiday`.
- Valores numéricos como `1,234K` aceptan separadores de miles.
- Hay tests focalizados en `tests/test_download_fundamentals.py`.

## Resultados verificados

La revisión funcional confirmó:

- La suite completa pasa: `7 passed`.
- Cada día realiza una única petición HTTP.
- `raw/YYYY-MM-DD.html`, JSON, staging, progreso y Parquet se escriben en una descarga real.
- Los festivos reales quedan como `time_kind = all_day` e `impact = holiday`.
- `12:00am` real sigue siendo `scheduled`, correctamente separado de `All Day`.
- Las celdas vacías heredan la hora del grupo y todos los IDs revisados reciben `raw_time`.
- La zona horaria del sistema no cambia los epochs UTC del Parquet.
- La deduplicación usa `source_event_id` y cae al hash si falta.
- Los errores HTTP y fallos de descarga no marcan el día como completado.

## Puntos para conservar bajo vigilancia

### 1. Formato real de hora y fecha

Usar registros reales devueltos por `forex-pytory`, no solo registros sintéticos:

- Confirmar si `Time` llega como `DD/MM/YYYY HH:MM`.
- Confirmar si existe o no la clave `Date`.
- Verificar que `30/01/2015 01:30` produce `scheduled` y no `all_day`.
- Verificar que la fecha usada para `release_at` sale de `Time` cuando `Date` está ausente.

### 2. `All Day` y `Tentative`

Determinar si `forex-pytory` conserva estas etiquetas o las destruye antes de entregar el registro:

- Celda vacía o heredada de la fila anterior.
- `Tentative`.
- `All Day`.
- Primera fila del día sin hora.

El exportador descarga el HTML una sola vez, lo guarda en `raw/YYYY-MM-DD.html`
y extrae `td.calendar__time` por `data-event-id`. Verificar que esa fuente
original clasifica `All Day`, `Tentative` y `Day N`, sin hacer una segunda
petición HTTP. No asumir semántica a partir de la hora ya transformada por la
librería.

### 3. Identidad de eventos

- Confirmar que `source_event_id` proviene de `ID`/`id`.
- Revisar si el hash actual `event_id` puede colisionar con eventos del mismo nombre, moneda y hora.
- Recomendar una clave estable compuesta o conservar ambos IDs.

### 4. Valores e impacto

Verificar con datos reales:

- `n/a`, vacío y `na`.
- `1,234K`, porcentajes y signos.
- Impactos `high`, `medium`, `low`, `n/a`.
- Que `actual_raw`, `forecast_raw` y `previous_raw` mantengan valores útiles sin convertir `n/a` en texto operativo.

### 5. Parquet y reanudación

- Confirmar que el esquema incluye `source_event_id`.
- Confirmar `release_at` como `TIMESTAMP WITH TIME ZONE` UTC.
- Ejecutar una prueba con `--max-days 1` y verificar que se crea `calendar.parquet`.
- Confirmar que `progress.json` permite reanudar sin repetir días completados.
- Confirmar que un fallo HTTP antes de completar un día no lo marca como completado.

### 6. HTTP y operación en VPS

- Revisar el cierre de conexiones de `forex-pytory`.
- Probar con `ulimit -n` bajo y alto.
- Revisar tratamiento de `403`, `429`, errores TLS y `Too many open files`.
- Verificar que los reintentos no mantienen sesiones o descriptores abiertos.
- Usar pausas suficientemente largas para evitar bloqueo de ForexFactory.
- Confirmar que cada día realiza una sola descarga HTTP y conserva el HTML.

### 7. Zona horaria y backend

- Verificar las fechas de cambio horario de Nueva York.
- Confirmar que la zona horaria del VPS no modifica `release_at`.
- Revisar que consultas DuckDB/backend comparen timestamps usando `TIMESTAMPTZ` o epoch, no literales `TIMESTAMP` sin zona.
- Añadir una prueba de anclaje con un evento conocido solo si la fuente y la hora esperada están verificadas.

## Evidencia de referencia

La revisión de referencia incluyó:

1. Casos reproducidos con registros reales de `forex-pytory`.
2. Resultado de `python -m pytest tests/test_download_fundamentals.py tests/test_app.py -q`.
3. Un ejemplo de fila final de `calendar.parquet` con `release_at`, `time_kind`, `source_event_id` e impacto.
4. Lista separada de problemas confirmados, supuestos no demostrados y limitaciones de la librería.

## Almacenamiento

El HTML es el crudo auditable y el JSON es redundante pero útil para
inspección rápida. Cada página ocupa aproximadamente 110-160 KB; el rango
completo puede ocupar unos 600 MB sin comprimir. Se puede comprimir `raw/`
después de finalizar la descarga si el VPS tiene poco espacio.
