# Visores — Factiun

> Visores offline de levantamientos topográficos y geometría as-built de seguidores solares. Un repositorio, un despliegue, varias plantas.

## Qué hay

| Planta | Código | Qué resuelve |
|---|---|---|
| [**Ayora**](https://imoriana3.github.io/visores/ayora/) | 24025 · Valencia | Geometría as-built de 754 seguidores bifila (1.508 filas) desde 3.069 puntos, y los vectores de backtracking corregido por terreno que se cargan en cada TCU. |
| [**San José**](https://imoriana3.github.io/visores/san-jose/) | 24019 · Arequipa, Acciona | Editor de la asignación de 18.190 puntos a 2.289 seguidores, resuelta por flujo de coste mínimo y corregible a mano. |

## Estructura

```
lib/plotly.min.js     una sola copia de la librería de dibujo (4,7 MB)
css/factiun.css       base del tema, común a todos los visores
index.html            portada
ayora/                index.html · css/style.css · js/{app,data}.js · tools/
san-jose/             index.html · js/{app,data}.js · tools/
```

Cada visor trae sus datos ya resueltos en `js/data.js` y el generador que los produce en `<planta>/tools/`. Para regenerarlos: `cd <planta>/tools && python3 generate_data.py`.

## Por qué un solo repositorio
Los visores comparten tema y librería: con uno por planta, cada uno arrastraba su propia copia de Plotly (4,7 MB idénticos) y su duplicado del CSS, y cualquier retoque del tema había que repetirlo. Los datos, que sí son propios de cada planta, siguen separados por carpeta.

## Despliegue
GitHub Pages: https://imoriana3.github.io/visores/ · `.nojekyll` incluido. Source: *Deploy from a branch* → `main` / `/ (root)`.

## Notas
- Sin servidor y sin red: los datos y la librería se cargan como `<script>`, no por `fetch`.
- El tema se toca en `css/factiun.css`; lo propio de cada visor va en `<planta>/css/style.css`.

*Factiun · proyecto interno.*
