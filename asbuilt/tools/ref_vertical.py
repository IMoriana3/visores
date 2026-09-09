#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Marca los puntos del levantamiento con OTRA REFERENCIA VERTICAL.

Lo usan los dos generadores (ayora/ y san-jose/) para que las dos plantas se
midan con el MISMO criterio y el visor pueda decir lo mismo de las dos.

QUE BUSCA. Cotas entregadas en una referencia distinta a la del resto: en San
Jose aparecen 98 puntos, todos POSITIVOS, +36,55 m de media con sigma 0,40 —
la ondulacion del geoide en Arequipa. Huele a cota elipsoidal WGS84 colada
entre ortometricas. No es ruido de campo: es un dato de otro sistema.

Y NO ES UN PUNTO SUELTO, ES UNA MESA. Lo que se procesa con otra referencia es
una sesion de campo entera: TR-09_1-044-E tiene la mesa sur a 1531,7 m y la
norte a 1568,7 —36,7 m de salto en el MISMO tubo, fisicamente imposible—
mientras su hermana -W tiene las cuatro cotas a 1531,x.

CONTRA QUE SE COMPARA CADA PUNTO, Y POR QUE ASI. Contra los puntos de los
seguidores de al lado A SU MISMA COORDENADA NORTE, no contra una bola de radio
fijo. La diferencia no es cosmetica:

  · Una referencia distinta afecta a un punto o a una sesion, no a un SITIO:
    sus vecinos laterales estan bien y el punto canta solo.
  · El relieve real es SOLIDARIO: un talud aparece igual en todos los
    seguidores de esa estacion, asi que comparando lateralmente se cancela.
    Con una bola de 40 m la mediana mezcla los dos niveles del talud y marca
    terreno bueno — en San Jose, 7 falsos positivos en el borde sur de TR-07,
    que es un escalon real de ~3,5 m identico en 067 a 073.

EL UMBRAL NO ES DELICADO. En San Jose el reparto de |desvio| deja una banda
VACIA entre 5 y 20 m: cualquier umbral de 3 a 20 m marca exactamente los
mismos 98 puntos. En Ayora ninguno pasa de 1,7 m y no se marca nada.

LO QUE NO SE PUEDE DECIDIR SE DICE. Un punto sin vecinos laterales suficientes
no se declara limpio: se marca como NO DECIDIBLE (estado 2). En Ayora son el
23 % — pocos puntos y muy repartidos —, y llamarlos «limpios» seria afirmar
algo que no se ha comprobado.
"""

LIMPIO, MARCADO, SIN_DECIDIR = 0, 1, 2


def marca(xs, ys, zs, umbral=3.0, dy=3.0, dx=60.0, minv=6):
    """Devuelve (estado por punto, desvio por punto o None).

    xs/ys/zs: coordenadas de cada punto (x este, y norte, z cota ABSOLUTA).
    """
    n = len(xs)
    cubos = {}
    for i in range(n):
        cubos.setdefault(int(xs[i] // dx), []).append(i)
    est = [SIN_DECIDIR] * n
    des = [None] * n
    for i in range(n):
        b = int(xs[i] // dx)
        vec = []
        for k in (b - 1, b, b + 1):
            for j in cubos.get(k, ()):
                if j != i and abs(ys[j] - ys[i]) <= dy and abs(xs[j] - xs[i]) <= dx:
                    vec.append(zs[j])
        if len(vec) < minv:
            continue
        vec.sort()
        r = zs[i] - vec[len(vec) // 2]
        des[i] = round(r, 2)
        est[i] = MARCADO if abs(r) > umbral else LIMPIO
    return est, des


def resumen(est, des, filaDe):
    """Un renglon para el log del generador, y el recuento por fila.

    filaDe: indice de fila de cada punto. Devuelve (texto, {fila: n_marcados}).
    """
    porFila = {}
    marcados = [des[i] for i in range(len(est)) if est[i] == MARCADO]
    for i in range(len(est)):
        if est[i] == MARCADO:
            porFila[filaDe[i]] = porFila.get(filaDe[i], 0) + 1
    dec = sum(1 for e in est if e != SIN_DECIDIR)
    if not marcados:
        txt = ('referencia vertical: nada marcado · %d de %d puntos decidibles (%.1f%%)'
               % (dec, len(est), 100.0 * dec / max(1, len(est))))
        return txt, porFila
    marcados.sort()
    med = marcados[len(marcados) // 2]
    signo = 'todos positivos' if marcados[0] > 0 else ('todos negativos' if marcados[-1] < 0 else 'DE LOS DOS SIGNOS')
    txt = ('referencia vertical: %d punto(s) en %d fila(s) · desvio mediana %+.2f m '
           '(min %+.2f / max %+.2f, %s) · %d de %d puntos decidibles (%.1f%%)'
           % (len(marcados), len(porFila), med, marcados[0], marcados[-1], signo,
              dec, len(est), 100.0 * dec / max(1, len(est))))
    return txt, porFila
