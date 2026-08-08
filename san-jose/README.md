# Visor San José — Editor puntos–tracker

> Visor offline para casar el levantamiento topográfico con los IDs de seguidor de la PSFV San José (Acciona, Aragón).

## Qué es
Aplicación web de una sola página para **revisar y corregir** la asignación de los puntos del levantamiento a cada tracker del proyecto **San José**: 18.190 puntos, 2.289 trackers bifila y 21 NCU. La asignación inicial se resuelve por flujo de coste mínimo (min-cost flow, NetworkX) y el visor permite auditarla y reasignar a mano. Funciona 100% offline (datos y librería se cargan como `<script>`, sin `fetch`).

## Funcionalidades
- **Mapa interactivo** (Plotly/WebGL) con los 18.190 puntos y los 2.289 motores: zoom, pan y hover con la ficha de cada punto (tracker, esquina, mesa, estado).
- **Coloreado** por tracker (grafo de 7 colores, ningún vecino comparte color), por **NCU** (21 tonos) o por **estado**.
- **Filtros** por NCU y por estado (completos / incompletos / a revisar / sin puntos) con contadores en vivo.
- **Editor**: reasigna un punto a un tracker; la esquina (NE/NO/SE/SO) y la mesa se recalculan por geometría y el estado se actualiza al instante.
- **Deshacer / revertir todo** y **exportación a CSV** (formato Excel español `;` y `,`, UTF-8 con BOM).

## Uso
1. Abre `index.html` (o el despliegue) en el navegador — sin servidor.
2. Filtra por NCU/estado; con `Estado = No completos` y `Color = Estado` localizas lo pendiente.
3. Haz clic en un punto (se rodea en **cian**) y luego en el rombo (motor) del tracker destino, o escribe el ID y pulsa **Asignar**.
4. **Exporta el CSV** al terminar. Atajos: `Esc` deselecciona · rueda = zoom · arrastrar = pan.

## Stack
HTML/CSS/JS offline · **Plotly 3.6.0** (vendorizado en `js/` para uso sin red) · datos pre-resueltos con **NetworkX** (min-cost flow) y generados con `tools/generate_data.py` (pandas, numpy, scipy).

## Despliegue (URL)
GitHub Pages: https://imoriana3.github.io/visores/san-jose/ · `.nojekyll` incluido para servir todo tal cual. Source: *Deploy from a branch* → `main` / `/ (root)`.

## Notas
- Cliente: **Acciona** (PSFV San José, Aragón).
- Geometría: cada tracker es bifila (2 filas a 6,2 m en X, 2 mesas, 8 esquinas). Asignación original validada geométricamente (ancho 6,16 m ± 8 cm, mesa ~36 m).
- Para regenerar `js/data.js`: `cd tools && python3 generate_data.py` con los CSV de `tools/source/`.
- Los puntos editados se resaltan en **ámbar**; el seleccionado, en **cian**.

*Factiun · proyecto interno.*
