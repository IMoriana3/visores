# Auditoría de visores as-built, topografía y geometría de planta

## 1. TASK IDENTIFICATION

| Campo | Valor |
|---|---|
| Task | `10-INTERFACES-VISORES__visores` |
| Target chat | `10_INTERFACES` |
| Repository | `visores` |
| Mode | `AUDIT_ONLY_THEN_PERSIST_REPORT` |
| Fecha de auditoría | 2026-09-21 |
| Rama base auditada | `work` (única rama local disponible; no hay remoto ni referencia local `main`) |
| Commit base auditado | `e300912dfe6e4d5269a8060bc3f35e971e5cf9e4` |
| Alcance de cambio | Este informe únicamente. No se modificaron visores, generadores, fuentes ni generados. |

La auditoría es estática y de regeneración aislada. Se inspeccionaron todos los ficheros versionados, el historial disponible y los tres caminos funcionales: visor/editor `san-jose/`, visor histórico `ayora/` y visor común `asbuilt/`. Las regeneraciones se ejecutaron sobre una copia en `/tmp`, nunca sobre el árbol de trabajo.

## 2. EXECUTIVE FINDINGS

1. **El repositorio no contiene una autoridad as-built completa y autónoma.** En Ayora, los CSV de `ayora/tools/source/` son la fuente efectiva más alta disponible, pero ya contienen geometría, asignaciones y vectores calculados; no está el levantamiento bruto ni el proceso que produjo esos CSV. En San José, el levantamiento bruto sí está versionado, pero el reparto, las cotas reparadas y el as-built proceden de `cobertura-zigbee`, repositorio/proceso externo no incluido.
2. **La autoridad debe separarse por dominio.** Las observaciones topográficas crudas, el catálogo/layout de trackers y las correcciones manuales aprobadas son datos canónicos distintos. La asignación punto→tracker, la geometría de vigas, las pendientes, vecindades, backtracking y estados son derivados, aunque hoy varios vivan en carpetas llamadas `source`.
3. **`js/data.js` y `asbuilt/data/*.js` son artefactos de visualización, no autoridad.** `asbuilt/data/ayora.js` es además un mirror byte a byte de `ayora/js/data.js` (SHA-256 común `dc7715e…f36671`). Los CSV descargados desde el navegador son exports efímeros y filtrables, sin manifiesto ni hash.
4. **San José tiene dos asignaciones coexistentes.** `san-jose/tools/source/final_v2_labeled.csv` conserva la asignación anterior (18.190 puntos, 339 no asignados), mientras `asbuilt/source/sanjose/sanjose_puntos.json` contiene el reparto nuevo de los 18.289 puntos. El visor/editor usa la primera y añade los 99 puntos ausentes como no asignados; el visor as-built usa la segunda. No deben presentarse como una única autoridad.
5. **La edición manual no persiste como revisión.** El editor muta memoria, recalcula esquina/mesa heurísticamente, ofrece undo/reset y descarga `asignacion_editada.csv`; no hay importación del resultado, log de cambios, autor, fecha, motivo, base hash, revisión ni mecanismo de promoción a fuente.
6. **CRS insuficientemente especificado.** Solo se declaran `30N` y `19S`, además de una lat/lon y un origen local para San José. No se declara EPSG, datum horizontal, época, geoide/datum vertical, unidades por campo, orden de ejes ni transformación. La sospecha de mezcla elipsoidal/ortométrica se detecta por heurística, no por metadata geodésica.
7. **No hay modelo de terreno canónico.** “Terreno” significa medianas laterales de puntos o diferencias de cotas entre ejes vecinos; no existe DTM/TIN, versión de superficie, máscara, breaklines ni incertidumbre. Los vectores de Ayora ya vienen calculados en `filas.csv`; San José calcula solo pendiente transversal y deja magnitud/azimut de resultante en `null`.
8. **Reproducibilidad parcial.** Ayora y el as-built San José regeneraron de forma byte-idéntica en copia aislada. El generador del editor San José no pudo ejecutarse porque no hay entorno/dependencias bloqueadas (`numpy`, y además requiere `pandas`, `scipy`). No hay tests ni CI, hashes embebidos, schema version, tool version o receta completa de upstream.
9. **Hay documentación desactualizada.** README y documentación del detector dicen 98 cotas anómalas; el artefacto y la regeneración actuales contienen 99 puntos en 54 filas. El generador imprime accidentalmente el contenido de `plantas.js` en lugar del resumen de referencia vertical por reutilizar `txt`.
10. **El Plant Package debe incorporar un contrato versionado.** Debe transportar observaciones crudas inmutables, layout/IDs, CRS horizontal y vertical, asignaciones y correcciones como revisiones, geometría as-built con provenance por valor, productos BT3D derivados, QA, hashes y una receta reproducible. El visor debe ser consumidor/adaptador, nunca el lugar donde nace silenciosamente la autoridad.

## 3. VIEWER / GENERATOR INVENTORY

### 3.1 Inventario y clasificación

| Artefacto | Función | Clasificación actual | Motivo |
|---|---|---|---|
| `ayora/tools/source/{filas,mesas,motores,puntos}.csv` | Dataset preparado de Ayora | **CANONICAL DATA** de facto, con campos derivados mezclados | Es la entrada más alta disponible y permite regenerar el visor, pero no es fuente primaria trazable. |
| `ayora/tools/generate_data.py` | Compacta CSV, resuelve índices, shear y control vertical | **ADAPTER** | Traduce al esquema del visor y añade derivados locales. |
| `ayora/js/data.js` | Payload servido por el visor Ayora | **DERIVED ARTIFACT** | Regenerable y redondeado. |
| `ayora/index.html`, `ayora/js/app.js`, CSS | Visualización/exportación Ayora histórica | **LEGACY** | Funcional, pero duplicada por `asbuilt/`; conserva exportaciones con nombre fijo Ayora. |
| `san-jose/tools/source/sanjose_levantamiento.csv` | Observaciones topográficas originales declaradas | **CANONICAL DATA** | `id,X,Y,Z` sin tocar; no obstante carece de metadata CRS/vertical y hash de entrega externo. |
| `san-jose/tools/source/tracker_master.csv` | Catálogo/layout oficial declarado | **CANONICAL DATA** | Identidad de tracker y referencia XY; la afirmación “oficial” no lleva documento/versión fuente. |
| `san-jose/tools/source/final_v2_labeled.csv` | Asignación anterior y etiquetas | **LEGACY** | Parcial (faltan 99 observaciones) y distinta del reparto consumido por as-built. |
| `san-jose/tools/generate_data.py` | Genera el payload del editor y completa los 99 ausentes | **ADAPTER** | Construye índices, estados, vecinos y colores; depende de librerías no fijadas. |
| `san-jose/js/data.js` | Snapshot de editor | **DERIVED ARTIFACT** | Regenerable en principio; mezcla catálogo, asignación y atributos de UI. |
| `san-jose/index.html`, `san-jose/js/app.js` | Editor en navegador | **LEGACY** | Herramienta de fase anterior; las ediciones solo sobreviven mediante descarga manual. |
| `asbuilt/source/sanjose/sanjose_puntos.json` | Nube cruda más reparto nuevo | **MIRROR** | Copia declarada desde `cobertura-zigbee`; observación y asignación derivada están mezcladas. |
| `asbuilt/source/sanjose/sanjose_asbuilt.json` | Geometría de filas del reparto | **MIRROR** | Resultado de generadores externos no incluidos; no puede reproducirse aquí desde las fuentes primarias. |
| `asbuilt/source/sanjose/sanjose_cotas.json` | Modelo de cotas reparadas/reconstruidas | **MIRROR** | Resultado externo con provenance semántica útil, pero sin receta ejecutable local. |
| `asbuilt/source/sanjose/shear.csv` | Cizallado E/W | **DERIVED ARTIFACT** | Consumido por el editor; el generador as-built lo recalcula y no lo consume. |
| `asbuilt/source/sanjose/meta.json` | Override de cliente | **CANONICAL DATA** | Declaración manual explícita, aunque sin autor/revisión. |
| `asbuilt/tools/ref_vertical.py` | Detector heurístico de referencia vertical | **ADAPTER** | Control QA derivado, no transformación geodésica. |
| `asbuilt/tools/generate_asbuilt.py` | Normaliza/copla fuentes a esquema común | **ADAPTER** | Transforma local→UTM, añade filas reconstruidas, calcula geometría/QA y genera manifiesto. |
| `asbuilt/data/sanjose.js` | Payload as-built San José | **DERIVED ARTIFACT** | Resultado reproducible desde mirrors locales. |
| `asbuilt/data/ayora.js` | Payload Ayora del visor común | **MIRROR** | Idéntico byte a byte a `ayora/js/data.js`; no lo escribe `generate_asbuilt.py`. |
| `asbuilt/data/plantas.js` | Catálogo de payloads disponibles | **DERIVED ARTIFACT** | El generador lo muta conservando entradas previas. |
| `asbuilt/index.html`, `asbuilt/js/app.js` | Visor común y exportador | **ADAPTER** | Presenta el payload y lo serializa; no debe conferir autoridad. |
| `lib/plotly.min.js`, tema, portadas | Runtime/UI | **ADAPTER** | No contienen datos de ingeniería. |

### 3.2 Cardinalidades verificadas

- **Ayora:** 1.508 IDs de fila únicos, 754 bifilas, 3.069 puntos únicos, 34 filas/17 bifilas articuladas. Origen declarado de filas: 1.496 `medido`, 10 `extremo estimado con pendiente de proyecto`, 2 `ARTICULADA en plano SIN cota de motor medida`.
- **Editor San José:** 2.289 tracker IDs únicos; 18.190 registros etiquetados (17.851 asignados, 339 no asignados) y 18.289 observaciones crudas únicas. El generador incorpora como no asignados los 99 IDs presentes solo en el crudo.
- **As-built San José:** source as-built con 4.572 filas y 2.287 trackers; source de cotas con 2.289 trackers; payload final con 4.578 filas y 2.289 trackers al añadir reconstrucciones. Origen final: 4.526 medidos, 35 con una cota repuesta, 4 con ambas repuestas, 9 vigas duplicadas de hermana y 4 filas de 2 trackers reconstruidos del plano.

## 4. SOURCE DATA / PROVENANCE

### 4.1 Qué puede considerarse autoridad hoy

- **Observación topográfica San José:** `sanjose_levantamiento.csv`, exclusivamente sus cuatro primeras columnas `id,X,Y,Z`. Es el único fichero que el código denomina explícitamente crudo y “sin tocar”.
- **Identidad/layout San José:** `tracker_master.csv`, condicionado a confirmar externamente qué revisión del Excel oficial representa.
- **Ayora:** no existe raw delivery en el repositorio. `puntos.csv` es autoridad de observaciones de facto y `filas.csv`/`mesas.csv`/`motores.csv` son autoridad de ingeniería de facto, pero todos son productos ya preparados. El texto “levantada en febrero de 2026” no sustituye una cadena de custodia.
- **Override manual:** `meta.json` es canónico solo para `cliente`; no debe validar por implicación el resto de metadata heredada.

### 4.2 Derivaciones y mirrors

San José declara que `sanjose_asbuilt.json`, `sanjose_puntos.json` y `sanjose_cotas.json` se copiaron “tal cual” desde `cobertura-zigbee`. Sus campos `fuente`, `reparto`, `origen` y `nota` documentan intención, pero faltan repositorio/URL, commit SHA, comando exacto, versión de inputs y hashes upstream. Por tanto son **mirrors sin cadena verificable**, no canonical sources autónomos.

Ayora tiene mejor regeneración local del payload, pero peor provenance aguas arriba: no están los ficheros originales del topógrafo, los `.cdt`, el algoritmo que asignó puntos, ni el cálculo que produjo `pend_proy`, `tcu_*`, residuales y estados. Es imposible auditar desde este repositorio la exactitud de esos valores, aunque sí su traslado al JS.

### 4.3 Revisiones y hashes

- La única revisión persistente común es Git. Ningún dataset declara `schema_version`, `data_revision`, `source_revision`, timestamp, autor/aprobador o estado de aprobación.
- Ningún generado embebe hashes de sus inputs, del generador o de la salida. Los SHA-256 calculados durante esta auditoría prueban únicamente el snapshot auditado; no constituyen un manifiesto mantenido.
- No existe changelog de correcciones topográficas ni registro de decisiones. Los mensajes de commit explican cambios importantes, pero no son un ledger de datos consumible por máquinas.

## 5. IDS / CRS / UNITS / GEOMETRY

### 5.1 IDs y aliases

- **Ayora:** `id` de fila (p. ej. `HD-1-0`) es único; la identidad de bifila se recompone con `(zona, tracker)` y `fila` 0/1. Las vecinas se almacenan tanto como índice (`vo/ve`) como texto (`tvo/tve`), con aliases textuales como `"HD-1-0 (hermana)"`. No existe tabla formal de aliases ni UUID estable.
- **San José:** `Tracker_ID` (p. ej. `TR-03_1-001`) es único en master. La fila añade sufijo `-E/-W`. El generador también fabrica IDs `TR-PLANO-%04d` cuando falta tracker ID. En el payload, `tk` puede ser el número terminal o, para IDs no numéricos, el índice de orden: no es un identificador estable.
- Los puntos tienen IDs enteros únicos dentro de cada planta, pero no están namespaced globalmente. El contrato debe usar `(plant_id, survey_id, point_id)`.
- `NCU`, `NCU ACCIONA`, `PS`, `GW`, `TCU`, zona, tracker y fila son relaciones/aliases diferentes; hoy no hay tabla explícita con vigencia y fuente.

### 5.2 CRS, datum y unidades

- Las coordenadas parecen UTM y la UI las etiqueta así; metadata declara solo `huso='30N'` (Ayora) y `huso='19S'` (San José). Esto **no identifica un CRS completo**: falta autoridad/código EPSG y datum.
- San José incluye `lat=-16.5957735`, `lon=-71.8064406`, `cE`, `cN`, `base` y zona 19S, pero no especifica el CRS de lat/lon, la transformación, época o precisión.
- El datum vertical no está declarado. El detector infiere que una diferencia aproximada de +36,55 m podría corresponder a mezcla elipsoidal/ortométrica; es evidencia QA, no identificación formal del datum ni una corrección válida.
- X/Y/Z, longitudes, pitch, cuerda, huecos y desplazamientos se tratan como metros; pendientes como porcentaje; azimut/grados desde norte en sentido horario; `limite` como grados. Estas unidades viven en documentación/nombres, no en un schema machine-readable.
- En San José source as-built, `x`, `zs`, `zn`, `ys`, `yn` son locales/relativos; el generador aplica `X=cE+x`, `Y=cN-z_local`, `Z=base+y_local`. El cambio de signo del eje local debe formalizarse como transformación versionada.

### 5.3 Geometría y asignación

- **Ayora:** endpoints y cotas de eje ya vienen resueltos. Para filas rígidas se usan dos extremos; para articuladas, mesas y motor. La cota de eje resta `0,829 m` a la medida sobre módulo, constante empírica aún no confirmada. Por ello Z de eje es una **aproximación**, no observación directa.
- **Asignación editor San José:** la base `final_v2_labeled.csv` se generó por flujo de coste mínimo, pero el código que lo resolvió no está aquí. Al editar, E/W se decide por cercanía a `X_ref` o `X_ref-6,2`; dentro de cada lado se ordena Y descendente y solo los primeros cuatro puntos reciben mesa/esquina. No valida distancia, capacidad, duplicados semánticos ni geometría física.
- **Asignación as-built San José:** procede del reparto externo y asigna los 18.289 puntos a 4.572 filas. El generador cruza fila por ID, y reconstrucciones por tolerancia geométrica `|dx|<1 m` más solape. Esta asignación es diferente y posterior a la del editor.
- **Vecindad:** Ayora la recibe en `filas.csv`. San José la recalcula buscando la primera fila al oeste/este dentro de `1,6 × pitch` y con solape longitudinal mayor a 5 m. Es una regla derivada, no relación canónica.

## 6. AS-BUILT VS DERIVED DATA

### 6.1 Observado, corregido, reconstruido

El modelo debe distinguir, por cada valor y no solo por fila:

1. `MEASURED`: coordenada/cota observada.
2. `ESTIMATED`: extremo Ayora estimado con pendiente de proyecto.
3. `REPLACED_VERTICAL_REFERENCE`: una o dos cotas sustituidas desde hermana/vecindario.
4. `COPIED_SIBLING`: viga completa duplicada desde su hermana.
5. `RECONSTRUCTED_LAYOUT`: tracker no levantado, generado desde plano.
6. `INTERPOLATED`: motor Ayora interpolado en fila rígida.

San José ya conserva parcialmente categorías `oi=0..4`; Ayora usa texto libre `origen` y `medido` del motor. Ninguno conserva lineage por coordenada, método parametrizado, source IDs, incertidumbre o aprobador. El Plant Package debe normalizar esas categorías y mantener a la vez el valor bruto y el valor de uso.

### 6.2 Terrain, cotas y backtracking

- No hay terreno explícito. El control vertical toma la mediana de cotas laterales dentro de `dy=10 m`, `dx=30 m`, mínimo 3 vecinos y marca si `|desvío|>3 m`. `SIN_DECIDIR` se conserva, correctamente, separado de limpio.
- Ayora contiene `s_oeste/s_este`, magnitud y azimut resultantes, residuales, vecinos, relación de hermana y campos `tcu_*`. Son **derivados upstream opacos**: el repositorio no contiene su fórmula de origen. El generador solo los empaqueta.
- San José calcula pendiente longitudinal de extremos y pendiente transversal usando diferencia de Z media / separación X. Descarta longitudinales mayores de 15 % y transversales mayores de 25 % convirtiéndolas a `null`. No calcula azimut ni magnitud resultante (`ao/ae/mo/me=null`) y, por tanto, no produce un vector BT3D equivalente al de Ayora.
- `sanjose_asbuilt.json` declara que ciertos campos TCU se heredan de un as-built anterior y que su regla no está en este repositorio. Esto impide tratarlos como cálculo reproducible.

### 6.3 Qué es solo visualización

Colores de grafo/NCU/estado, filtros, camera range, selección, overlays, textos, compactación columnar e índices de arrays son solo visualización. También lo son los estados recalculados únicamente para feedback del editor. Ninguno debe volver al Plant Package salvo mediante un workflow explícito de propuesta/revisión/aprobación.

## 7. LOCAL COMPUTATION

| Cálculo | Lugar | Naturaleza y riesgo |
|---|---|---|
| Índices fila/vecina, compactación y redondeo | generadores | Adaptación; el redondeo a 2/3 decimales pierde precisión respecto de fuentes. |
| Shear E/W | generadores Ayora/as-built | Derivado de diferencia longitudinal entre centros de hermanas. Umbral anómalo San José: `>0,5 m`; el editor usa `>=3 m` desde `shear.csv`, semántica distinta. |
| Pendientes longitudinal/transversal | as-built generator | Cálculo físico local con cortes 15 %/25 % no expresados como QA configurable. |
| Resultante/azimut BT3D | fuente Ayora | No se calcula localmente; provenance/fórmula ausente. |
| Referencia vertical | `ref_vertical.py` | Heurística QA robusta documentada, no conversión de datum. |
| Nearest tracker/NCU | generator editor | KD-tree; sugerencia visual para no asignados. |
| Reetiquetado esquina/mesa | navegador | Heurística mutable; puede dejar puntos sin etiqueta si hay más de cuatro por lado. |
| Estado tracker | generator/navegador | El navegador degrada `REVISAR` a `OK` tras editar porque solo cuenta esquinas y omite shear. |
| Exports CSV | navegador | Serialización del estado/filtrado visible; coma decimal, `;`, BOM. Sin schema, revision ni checksum. |

Los cálculos físicos locales deben moverse a una librería/generador validado del Plant Package o, como mínimo, emitir método, versión, parámetros, inputs y QA. El navegador debería limitarse a recomputaciones de preview claramente no autoritativas.

## 8. REGENERATION / REPRODUCIBILITY

### 8.1 Resultado observado

- `ayora/tools/generate_data.py` regeneró `ayora/js/data.js` byte a byte. Reportó 1.508 filas, 3.069 puntos, 34 filas articuladas, 2.963/3.069 cotas decidibles y cero marcadas.
- `asbuilt/tools/generate_asbuilt.py sanjose` regeneró `asbuilt/data/sanjose.js` y `plantas.js` byte a byte. Reportó 4.578 filas, 2.289 trackers, 18.289 puntos y pitch 6,2 m.
- `san-jose/tools/generate_data.py` no fue ejecutable en el entorno base: `ModuleNotFoundError: numpy`. No hay `requirements.txt`, lockfile o imagen fijada; también importa pandas y SciPy.
- No existen tests, fixtures, validación de schemas, golden hashes ni CI observable en el árbol auditado.

### 8.2 Límites

La igualdad byte a byte demuestra determinismo desde los inputs **intermedios versionados**, no reproducibilidad desde entregas originales. San José necesita herramientas ausentes de `cobertura-zigbee`; Ayora necesita el proceso ausente que creó sus cuatro CSV. Además, `generate_asbuilt.py` lee y reescribe el manifiesto existente: una generación limpia de una sola planta no garantiza el mismo catálogo completo.

El log de `generate_asbuilt.py` tiene un defecto: la variable `txt` del resumen de referencia vertical se reutiliza al leer `plantas.js`, por lo que imprime el manifiesto en lugar del resumen. El dato generado no cambia, pero se pierde evidencia QA del run.

## 9. DISCREPANCIES

| ID | Discrepancia | Clasificación | Impacto |
|---|---|---|---|
| D-01 | README/ref detector dicen 98 puntos con referencia distinta; payload/regeneración actuales contienen 99 en 54 filas. | **BUG** | Documentación y criterio operativo no corresponden al snapshot servido. |
| D-02 | README raíz dice 18.190 puntos del editor; el payload actual incorpora los 18.289 crudos. | **LEGACY** | Cardinalidad mostrada/documentada inconsistente. |
| D-03 | README San José sitúa la planta en Aragón; metadata/UTM 19S/lat-lon y README as-built la sitúan en Arequipa. | **BUG** | Riesgo crítico de identificación de planta/CRS. Debe confirmarse el nombre/emplazamiento oficial. |
| D-04 | Dos asignaciones: `final_v2_labeled.csv` anterior frente a reparto nuevo de `sanjose_puntos.json`. | **INTENTIONAL** pero no gobernada | Editor y visor as-built pueden discrepar; falta declarar revisión vigente y deprecación. |
| D-05 | `shear.csv` es leído por editor; as-built recalcula shear de geometría y no usa el CSV. | **INTENTIONAL** | Dos consumidores y umbrales distintos; el nombre común oculta semántica/revisión. |
| D-06 | Editor recalcula `OK/INCOMPLETO` sin conservar regla `REVISAR` por shear. | **BUG** | Una edición puede borrar visualmente una alerta sin resolverla. |
| D-07 | San José usa `BIFILA=6,2` en editor, mientras source as-built declara desplazamiento de hermana `6,174`. | **APPROXIMATION** | Puede alterar clasificación E/W cerca de bisectriz; debe derivarse del layout/versionarse. |
| D-08 | Ayora resta 0,829 m para cota de eje, explícitamente pendiente de confirmar. | **APPROXIMATION** | Z absoluta de eje no debe etiquetarse como medida sin calificador/incertidumbre. |
| D-09 | San José elimina pendientes >15 %/>25 % en lugar de conservar valor bruto con flag. | **APPROXIMATION** | Pierde evidencia y hace que ausencia y rechazo QA sean indistinguibles. |
| D-10 | `asbuilt/data/ayora.js` es copia idéntica pero ningún generador común mantiene esa copia. | **LEGACY** | Riesgo de drift manual futuro. |
| D-11 | `generate_asbuilt.py` imprime manifiesto en lugar del resumen vertical. | **BUG** | Log de regeneración incompleto/engañoso. |
| D-12 | `sanjose_asbuilt.json` tiene 2.287 trackers/4.572 filas, `sanjose_cotas.json` 2.289 y salida 2.289/4.578. | **INTENTIONAL** | Son dos trackers reconstruidos y filas añadidas; requiere lineage explícito, hoy inferido por código. |
| D-13 | Source cotas reporta `n_sh=10` trackers; salida marca 20 filas (dos por tracker). | **INTENTIONAL** | Cardinalidad tracker vs fila; etiquetas deben indicar unidad de conteo. |
| D-14 | Documentación habla de “vectores BT3D” para el visor común, pero San José deja magnitud/azimut en `null`. | **BUG** documental / **UNKNOWN** funcional | No puede asumirse que el export San José sea configuración TCU completa. |
| D-15 | No hay EPSG/datum horizontal ni datum/geoid vertical en ninguna planta. | **UNKNOWN** | No se puede certificar interoperabilidad o transformación. |
| D-16 | Provenance de Ayora y generadores upstream San José ausente. | **LEGACY** | No se puede reproducir el as-built desde fuentes originales. |
| D-17 | Exports dependen del filtro/vista y carecen de revisión/hash/provenance. | **INTENTIONAL** como UX, **BUG** si se usan como entrega | No aptos como artefacto contractual. |
| D-18 | “Manual corrections” solo existen en memoria/CSV descargado; no hay ledger/import/promoción. | **BUG** de gobernanza | Correcciones aprobadas no son reproducibles ni auditables. |
| D-19 | `tk` generado puede ser número terminal o índice artificial. | **LEGACY** | No debe usarse como clave entre sistemas. |
| D-20 | Detector vertical documenta una explicación geoidal probable sin datum confirmado. | **UNKNOWN** | Debe mantenerse como hipótesis hasta recibir metadata del topógrafo. |

## 10. REQUIRED PLANT PACKAGE ARTIFACT CONTRACT

### 10.1 Paquete mínimo propuesto

```text
plant-package/
  manifest.json
  schemas/
  survey/surveys.json
  survey/observations.parquet (o CSV canónico)
  layout/trackers.geojson
  layout/id_aliases.csv
  assignment/point_tracker_assignment.parquet
  assignment/corrections.ndjson
  geometry/asbuilt_rows.parquet
  geometry/joints_motors.parquet
  terrain/terrain_manifest.json (+ DTM/TIN si existe)
  products/backtracking_3d.parquet
  qa/findings.json
  provenance/lineage.json
  checksums.sha256
```

### 10.2 Requisitos del `manifest`

- `plant_id` inmutable, nombre/código/client aliases y emplazamiento confirmado.
- `package_schema_version`, `package_revision`, estado (`draft/reviewed/approved/superseded`), created time, author y approver.
- Commit/version de cada herramienta; comando reproducible; hashes de todos los inputs y outputs.
- CRS horizontal completo: autoridad/código (p. ej. EPSG confirmado, no inferido), WKT/PROJJSON, orden de ejes, unidades, época si aplica.
- CRS vertical: tipo de altura, datum/geoid/modelo y versión; si es desconocido, `UNKNOWN` explícito por survey/batch, nunca supuesto.
- Convención geométrica: ejes locales, transformación affine/local→CRS, azimut, orientación E/W/N/S, signos y unidades.

### 10.3 Entidades y provenance

- **Observation:** `(plant_id, survey_id, point_id)` único; XYZ original sin redondear; timestamp/batch/instrument/quality si existen; source file/hash/row; CRS horizontal y vertical.
- **Tracker/layout:** ID estable opaco, geometry/type/NCU y revisión de diseño. Aliases en tabla many-to-one con namespace, vigencia y source; nunca reconstruir identidad partiendo strings.
- **Assignment:** point key, row/tracker key, role (corner/end/joint), confidence, método y revisión. Separar asignación automática, propuesta manual y asignación aprobada.
- **Correction ledger:** correction ID, base revision/hash, before/after, reason code/text, actor, timestamp y approval. Aplicación determinista, detección de conflicto e import/export simétricos.
- **As-built geometry:** row/end/joint/motor primitives; para cada coordenada: `value`, `unit`, `origin_class`, source observations, método, parámetros, uncertainty y QA flags. Conservar bruto junto al reparado/reconstruido.
- **Terrain:** superficie identificada y versionada o `NONE`. Si solo se usan vecinos, llamarlo explícitamente `lateral_neighbor_estimator`, con ventana, umbral y coverage; no denominarlo DTM.
- **BT3D product:** row ID, side, longitudinal/transverse/resultant slope, downhill azimuth, neighbor row, method/version, terrain revision, geometry revision y validity/QA. No emitir “config” si faltan resultante o azimut.
- **QA:** findings con severidad, estado (`pass/fail/unknown/not_evaluated`), objeto afectado, valor bruto, regla/umbral y disposition. Nunca reemplazar un valor rechazado por `null` sin conservarlo.

### 10.4 Política de artefactos

1. **Versionar como Plant Package:** raw surveys autorizados, layout autorizado, aliases, correcciones aprobadas, asignación aprobada, geometría as-built normalizada, producto BT3D, QA, provenance y checksums.
2. **Regenerar, no declarar autoridad:** `js/data.js`, payloads compactos, palettes, índices, estados de UI y CSV de vista.
3. **Mirrors:** permitidos solo con `upstream_uri`, revision/commit, source hash, copied-at y verificación automática.
4. **Exports:** incluir package revision, schema version y hash; export completo por defecto. Un export filtrado debe declararse `subset` e incluir criterio.
5. **Gates:** schema validation, claves/aliases, CRS, unidades, cardinalidad, cobertura de asignación, lineage completo, golden numerical tolerances, deterministic build y comparación de hashes.

## 11. QUESTIONS TO 10_INTERFACES / 06_PLANT / 00_MASTER

### A `10_INTERFACES`

1. ¿Qué interfaz será la única vía para promover un CSV de correcciones del editor a revisión aprobada, y cómo se representarán conflicto, undo y aprobación?
2. ¿Puede el viewer recibir siempre `package_revision`, schemas y checksums y mostrar de forma inequívoca `measured/estimated/replaced/copied/reconstructed`?
3. ¿Se retira `ayora/` a favor de `asbuilt/`, o se mantendrá como consumidor legacy con prueba automática de igualdad?
4. ¿El export BT3D es entrega contractual o ayuda de usuario? Si es contractual, ¿qué campos son obligatorios y cómo se impide exportar San José con magnitud/azimut ausentes?
5. ¿Debe el editor migrar de heurística browser-only a propuestas firmadas contra una base hash?

### A `06_PLANT`

1. Confirmar CRS/EPSG, datum horizontal, época, datum vertical/geoid y unidades oficiales de Ayora y San José.
2. Confirmar si “San José” 24019 está en Arequipa; corregir la referencia a Aragón o identificar si se mezclaron dos plantas homónimas.
3. Entregar/referenciar los levantamientos originales de Ayora, `.cdt`, revisión de layout y proceso que produjo `filas/mesas/motores/puntos.csv`.
4. Definir autoridad entre asignación legacy del editor y reparto nuevo de `cobertura-zigbee`; declarar cuál está aprobada y desde qué revisión.
5. Confirmar `h_eje=0,829 m` de Ayora y su incertidumbre; hasta entonces, ¿debe publicarse Z sobre módulo en lugar de Z eje?
6. Confirmar fórmula, convención y revisión de vectores `tcu_*` de Ayora y campos TCU heredados en San José.
7. Confirmar los 99 puntos con referencia vertical anómala y su datum/batch; ¿deben corregirse mediante transformación documentada o reclamarse y sustituirse?
8. ¿Existe DTM/TIN oficial? Si no, aprobar formalmente que pendiente transversal se base en geometría de ejes vecinos y no en terreno continuo.

### A `00_MASTER`

1. ¿Qué repositorio/sistema será la autoridad del Plant Package y cuál será la política de versionado, aprobación, retención y supersession?
2. ¿Se permite versionar raw survey data y derivados pesados en Git, Git LFS o registro de artefactos? Definir URI estable y política de hashes.
3. ¿Qué taxonomía corporativa se adopta para `CANONICAL DATA`, `DERIVED ARTIFACT`, `MIRROR`, `ADAPTER`, `LEGACY` y para findings `INTENTIONAL/APPROXIMATION/LEGACY/BUG/UNKNOWN`?
4. ¿Qué tolerancias y sign-off convierten una geometría/asignación en “as-built aprobado” y un BT3D en “cargable en TCU”?
5. ¿Debe bloquearse publicación/despliegue cuando falten CRS, datum vertical, provenance o tests de reproducibilidad?

---

**Conclusión:** los visores son consumidores útiles y contienen decisiones de ingeniería valiosas, pero hoy actúan también como frontera informal de integración. La autoridad no debe inferirse por la carpeta `source`, por lo que se dibuja o por lo que exporta el navegador. La migración prioritaria es crear el Plant Package con identidad, CRS/datum, lineage por valor, correcciones revisables y builds deterministas; después, hacer que ambos visores consuman exclusivamente adaptadores generados desde ese paquete.
