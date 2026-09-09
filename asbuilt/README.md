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

## Cotas con otra referencia vertical

`tools/ref_vertical.py` lo comparten los dos generadores, para que las dos plantas
se midan con la misma vara. Marca las cotas entregadas en una referencia distinta a
la del resto: en San José son **98 puntos en 54 filas**, todos positivos, **+36,55 m
de media con σ 0,40** — la ondulación del geoide en Arequipa, o sea cota elipsoidal
WGS84 colada entre ortométricas. En Ayora **ninguna**.

Cada punto se compara con los de los seguidores **de al lado, a su misma coordenada
norte**, no con una bola de radio fijo. El motivo es que el relieve real es
*solidario*: un talud aparece igual en todos los seguidores de esa estación y al
comparar lateralmente se cancela, mientras que una referencia distinta no. Con una
bola de 40 m salían 7 falsos positivos en el borde sur de TR-07, que es un escalón
real de ~3,5 m idéntico en 067-073.

El umbral no es delicado: en San José hay una **banda vacía entre 5 y 20 m**, así que
cualquier valor de 3 a 20 marca exactamente los mismos 98 puntos.

La ventana (`dy=10 m`, `dx=30 m`, mínimo 3 vecinos) está **medida, no elegida a ojo**,
y el barrido dio dos sorpresas. La primera: aflojar `dy` y el mínimo de vecinos no
mueve San José **un solo punto**, y sube la cobertura de Ayora del 76,9 % al 96,5 %.
La segunda: `dx` quiere ser **estrecho**, no ancho — con 60 m la ventana abarca tanta
ladera que la propia pendiente lateral se lee como desvío (tres puntos de Ayora a
2,1-2,4 m que son terreno puro), y a 30 m ese suelo de ruido baja a **1,38 m** sin
cambiar el veredicto. Por debajo de 24 m sí cambia, y ampliarlo a 100 m mete 11 falsos
positivos del talud de TR-07.

Con eso, **el umbral no tiene dónde equivocarse**: el desvío mayor de un punto limpio
es 2,18 m y el menor de uno contaminado, 35,01 m. Cualquier valor entre los dos da el
mismo veredicto.

Se probó también ajustar una **recta** a los vecinos en vez de su mediana, para quitar
la pendiente lateral de raíz. Baja el suelo a 0,97 m, pero fabrica 13 falsos positivos
en TR-02 con desvíos de −17,2 y +11,4 m donde la mediana ve ±0,4: donde el vecindario
no es una recta limpia, la regresión se inclina y miente. Se quedó la mediana.

Lo que sale de ahí, en el dato y en la app:

| campo | qué es |
|---|---|
| `p.r` | por punto: `0` comprobado · `1` marcado · `2` sin vecinos para decidir |
| `p.rd` | desvío del punto contra sus laterales (m) |
| `f.rv` | cuántas cotas marcadas tiene esa fila |
| `meta.n_rv`, `meta.n_rv_filas` | recuentos de planta |

En pantalla: chip de recuento, filtro «Solo cota de otra referencia», capa de
resalte encima de cualquier coloreado, métricas propias en las vistas de filas y de
puntos, y el detalle con **id de punto y desvío** en la ficha de la fila. **No se
corrigen**: se marcan, porque lo que toca es reclamárselas al topógrafo. Un punto
que no se puede decidir no se declara limpio.
