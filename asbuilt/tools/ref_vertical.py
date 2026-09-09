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

EL UMBRAL NO ES DELICADO. El reparto de |desvio| deja una banda VACIA enorme
entre lo limpio y lo contaminado — el detalle, mas abajo, en «donde queda el
umbral». En Ayora ningun punto pasa de 1,38 m y no se marca nada.

LO QUE NO SE PUEDE DECIDIR SE DICE. Un punto sin vecinos laterales suficientes
no se declara limpio: se marca como NO DECIDIBLE (estado 2). Llamarlo «limpio»
seria afirmar algo que no se ha comprobado.

DE DONDE SALEN dy=10 / dx=30 / minv=3, medidos, no elegidos a ojo. La primera
version (3/60/6) dejaba SIN COMPROBAR el 23 % de Ayora, que es demasiado hueco
para una planta que luego se declara limpia. El barrido de los tres parametros
dice que ninguno de los tres costaba lo que parecia:

  · dy (ventana en Y) se suelta de 3 a 10 m sin que San Jose se mueva UN PUNTO.
    Tiene sentido fisico: el escalon de TR-07 esta a 37 m —la distancia entre
    estaciones—, asi que 10 m siguen sin cruzarlo. A partir de 15 m empieza a
    derivar (101 puntos en vez de 98), y ahi se para.
  · minv (vecinos minimos) de 6 a 3 tampoco mueve San Jose. Un punto contaminado
    lo esta por +36 m: no hace falta cuorum para verlo.
  · dx (ventana en X) es el que fija el SUELO DE RUIDO, y lo quiere ESTRECHO, no
    ancho — al reves de lo que parecia. Con 60 m la ventana abarca tanta ladera
    que la propia pendiente lateral se lee como desvio: en Ayora habia tres
    puntos a 2,1-2,4 m que son terreno puro (sus vecinos bajan 734,12 · 733,72 ·
    733,43 · 733,15... y el punto esta en lo alto de la rampa), demasiado cerca
    del umbral de 3 m. A 30 m —cinco vanos— el suelo baja a 1,38 m en Ayora y
    2,18 m en San Jose sin mover el veredicto. Por debajo de 24 m si se mueve
    (91 puntos en vez de 98): 30 es el ultimo valor seguro. Y AMPLIARLO es lo
    peligroso: a 100 m aparecen 11 falsos positivos en el talud de TR-07, porque
    la ventana ya alcanza su otro nivel.

DONDE QUEDA EL UMBRAL. Con 10/30/3 el desvio mas grande de un punto limpio es
2,18 m y el mas pequeno de uno contaminado, 35,01 m: cualquier umbral entre esos
dos da EXACTAMENTE el mismo veredicto. Los 3 m estan dentro, con 33 m de banda
libre por delante.

UNA HIPOTESIS PROBADA Y DESCARTADA: ajustar una RECTA en x a los vecinos en vez
de tomar su mediana, para quitar la pendiente lateral de raiz. Baja el suelo de
Ayora a 0,97 m, si — pero fabrica 13 falsos positivos en TR-02, con desvios de
-17,2 m y +11,4 m donde la mediana ve +-0,4 m. Donde el vecindario no es una
recta limpia (dos niveles, o un contaminado dentro) la regresion se inclina y
miente, y este control vive justo donde el vecindario esta roto. La mediana es
robusta; la recta, no. Se queda la mediana.

Resultado del ajuste, con el veredicto de San Jose IDENTICO (98 puntos, 54
filas, cero en el talud): la cobertura de Ayora pasa de 76,9 % a 96,5 % y la de
San Jose de 99,1 % a 99,9 %.
"""

LIMPIO, MARCADO, SIN_DECIDIR = 0, 1, 2


def marca(xs, ys, zs, umbral=3.0, dy=10.0, dx=30.0, minv=3):
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
