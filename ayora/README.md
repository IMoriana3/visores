# Visor Ayora — geometría as-built y backtracking 3D

> Visor offline de la geometría real de los seguidores de la PSFV Ayora (24025, Valencia), levantada en campo en febrero de 2026. Sirve para configurar el backtracking corregido por terreno.

## Qué es
Aplicación web de una sola página que expone la **geometría as-built** de las 754 bifilas (1.508 filas) de Ayora, obtenida de 3.069 puntos de levantamiento topográfico. A diferencia del visor de San José —que era un editor de asignación— aquí la asignación ya está cerrada y verificada: lo que se consulta es la geometría y los parámetros de backtracking.

## Funcionalidades
- **Backtracking 3D**: pendiente longitudinal del eje y, para cada lado, pendiente transversal hacia la fila vecina, pendiente resultante y azimut de máxima pendiente. Al amanecer sombrea la vecina del este; al atardecer, la del oeste.
- **Articuladas**: las 17 bifilas con quiebro medido en el motor, con la pendiente de cada ala por separado y el desplazamiento del motor respecto a la recta.
- **As-built vs proyecto**: desviación de pendiente frente a la geometría de los `.cdt`, estado por tolerancia y sector anómalo.
- **Puntos**: los 3.069 puntos con su fila, extremo y si están en junta compartida.
- Filtros por zona y tipo, capas de motores y puntos, ficha por fila y **exportación a CSV** (formato Excel español).

## Geometría de la planta
- **754 bifilas · 1.508 filas · 2 alas por fila**, separadas por el motor.
- Tipos: **2TTx56** (28 módulos/ala, 74,63 m), **2TTx42** (21, 56,17 m), **2TTx28** (14, 37,72 m).
- Módulo de paso **1,324 m** a lo largo del tubo; cuerda **2,384 m**. Giro **±55°**.
- **Pitch uniforme de 6,00 m** entre filas vecinas, medido — el `.cdt` lo sitúa en 5,82/6,18.
- Eje **norte-sur puro** (azimut +0,0014°).
- **17 bifilas articuladas** (34 filas), con cota de motor medida. El resto son vigas rígidas: dos puntos por fila bastan.

## Notas sobre los datos
- Las cotas `Z eje` son la cota medida sobre módulo menos **0,829 m**. Esa constante es empírica y está **pendiente de confirmar** con el detalle de montaje; no afecta a pendientes ni azimutes, que se calculan restando cotas dentro de una misma fila.
- El azimut se mide desde el norte en sentido horario, en la dirección de máxima pendiente descendente.
- Precisión del levantamiento: **±5 cm** en cota, deducida de la continuidad en las 630 juntas y de la discrepancia entre las dos filas de cada bifila.

## Uso
1. Abre `index.html` (o el despliegue) en el navegador — sin servidor.
2. Elige vista y magnitud de coloreado; filtra por zona o tipo.
3. Haz clic en una fila para ver su ficha completa. `Esc` deselecciona.
4. **Config. BT3D** exporta la tabla de parámetros de las filas visibles.

## Stack
HTML/CSS/JS offline · **Plotly** (vendorizado en `js/`) · datos pre-resueltos y generados con `tools/generate_data.py`.

## Despliegue (URL)
GitHub Pages: https://imoriana3.github.io/visores/ayora/ · `.nojekyll` incluido. Source: *Deploy from a branch* → `main` / `/ (root)`.

## Regenerar los datos
```
cd tools && python3 generate_data.py
```
Lee `tools/source/{filas,mesas,motores,puntos}.csv` y escribe `js/data.js`.

*Factiun · proyecto interno.*
