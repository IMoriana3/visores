# As-built de módulos — una app, todas las plantas

Visor de la **geometría medida** de los seguidores: extremos y cotas de cada fila,
pendiente longitudinal, pendiente hacia la fila vecina de cada lado y puntos del
levantamiento. Es lo que se usa para configurar el backtracking corregido por terreno.

    asbuilt/?planta=ayora      (por defecto)
    asbuilt/?planta=sanjose

Antes había dos aplicaciones distintas con el mismo nombre en el Panel: la de Ayora
—geometría terminada— y la de San José —editor de asignación puntos↔tracker—, que no
se parecían en nada porque no hacían lo mismo. Ahora la app es una y los datos van por
planta en `data/<planta>.js`, todos con el mismo esquema (`window.DATA = {meta,f,m,o,p}`).

## Datos

| planta | filas | seguidores | puntos | origen |
|---|---|---|---|---|
| Ayora | 1.508 | 754 | 3.069 | `ayora/tools/generate_data.py` (levantamiento feb-2026) |
| San José | 4.491 | 2.287 | 17.839 | `san-jose/tools/generate_asbuilt.py` (asignación ya casada) |

Las plantas sin articulaciones ni motores levantados (San José) traen esos bloques
vacíos: la app lo dice («ninguna medida») en vez de fingir que valen cero.

El **editor de asignación** de San José sigue donde estaba (`san-jose/`): es la
herramienta de la fase anterior, la que produce el dato que aquí se muestra.
