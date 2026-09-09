#!/usr/bin/env python3
"""
generate_asbuilt.py — el as-built de módulos de San José, con el MISMO esquema
que el de Ayora, para que los dos visores sean uno solo.

El visor de Ayora lee `window.DATA = {meta, f, m, o, p}` donde `f` es una fila por
fila de seguidor con su geometría medida (extremos, cotas, pendiente longitudinal
y pendientes/azimut hacia las vecinas). San José tenía en su lugar el editor de
asignación puntos↔tracker, con los puntos ya casados pero sin derivar geometría.
Esto lo deriva:

  sanjose_asbuilt.json  ->  una fila por (tracker, lado E/W), ya con sus extremos
  sanjose_puntos.json       medidos y sus puntos. Los dos salen del MISMO reparto
                            (cobertura-zigbee tools/reparte_levantamiento.py) que
                            usa el simulador: un reparto, un dibujo.
  shear.csv             ->  cizallado por seguidor (diferencia entre sus dos filas).
  sanjose_cotas.json    ->  de dónde sale la geometría de cada viga en el MODELO
                            (medida · una punta repuesta · duplicada de su
                            hermana · reconstruida del plano), que es lo que
                            distingue en el mapa una viga levantada de una
                            supuesta. Sale de cobertura-zigbee
                            tools/cotas_asbuilt.py, el mismo que come el 3D.

DE DÓNDE VENÍA Y POR QUÉ SE CAMBIA. Hasta aquí esto leía `final_v2_labeled.csv`,
la asignación punto↔tracker que vino del proveedor. Esa asignación tenía 93
trackers con puntos IMPOSIBLES —hasta 1.575 m de dispersión, uno con 44 puntos
repartidos un kilómetro en Y con 0,5 m en X— y, sobre todo, decidía la fase de
cada tubo tracker a tracker: 153 seguidores se quedaban con una sola viga y
algunos se dibujaban a media longitud, que es lo que se veía en el visor con los
puntos cayendo fuera de las barras. El dato del topógrafo estaba intacto; lo que
fallaba era de quién se decía que era cada punto.

El reparto nuevo resuelve la FASE POR LÍNEA (hay líneas cuyos tubos están
desplazados 7 m respecto de lo que el plano declara para ese tracker) y comparte
el punto de un tope medido una sola vez entre los dos tubos que se encuentran
ahí. Contra lo que había: 4.421 -> 4.449 filas, 2.134 -> 2.162 trackers con las
dos vigas, 153 -> 125 con una sola, y ninguna fila emitida a media longitud.

Salida: ../../asbuilt/data/sanjose.js — el fichero que CARGA asbuilt/index.html,
con el esquema de Ayora (los campos que San José no puede tener todavía
—articulaciones, motores medidos— van vacíos, y el visor ya los trata como
"sin dato").

Uso:  cd san-jose/tools && python3 generate_asbuilt.py
"""
import os, csv, json, math, collections, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, 'source')
# EL FICHERO QUE SIRVE LA PÁGINA, no una copia suya. Esto escribía en
# san-jose/js/data_asbuilt.js, que no lo carga NADIE: la página del as-built es
# asbuilt/index.html y lee asbuilt/data/<planta>.js. Los dos se separaron y el
# visor se quedó sirviendo 4.491 filas de una versión vieja mientras el
# generador decía «OK» sobre el fichero muerto. Una sola salida, la de verdad.
OUT  = os.path.join(HERE, '..', '..', 'asbuilt', 'data', 'sanjose.js')
sys.path.insert(0, os.path.join(HERE, '..', '..', 'asbuilt', 'tools'))
import ref_vertical                                    # mismo criterio que Ayora


# de dónde sale la geometría de cada viga, en el mismo orden que el código `oi`
OG_TXT = ['medido',
          'una punta repuesta: su cota vino con otra referencia vertical y se toma del terreno vecino '
          '(la otra punta, la posición y el largo son medida)',
          'las DOS cotas repuestas del terreno vecino: las cuatro puntas vinieron con otra referencia '
          'vertical — la posición y el largo siguen siendo medida',
          'viga DUPLICADA de su hermana: este seguidor se levantó a medias y esta viga no tiene ninguna punta medida',
          'seguidor RECONSTRUIDO del plano: no se levantó — geometría del layout y cota del terreno vecino']


def rd(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(v, nd=3):
    return None if v is None else round(float(v), nd)


def main():
    with open(os.path.join(SRC, 'sanjose_asbuilt.json'), encoding='utf-8') as f:
        AB = json.load(f)
    with open(os.path.join(SRC, 'sanjose_puntos.json'), encoding='utf-8') as f:
        NB = json.load(f)
    shear = {r['tid']: float(r['shear']) for r in rd('shear.csv') if r.get('shear') not in (None, '')}
    # DE DÓNDE SALE CADA VIGA EN EL MODELO. El as-built del reparto trae la
    # geometría medida; el que decide qué cota es medida y qué cota se repone
    # es `cotas_asbuilt.py`, y eso vive en sanjose_cotas.json. Sin cruzarlos, el
    # visor pintaba igual una viga con sus cuatro puntas medidas y una copiada
    # de su hermana, que es justo lo que hay que poder distinguir.
    #   0 medida · 1 una punta repuesta del terreno vecino · 2 las dos cotas
    #   repuestas (posición y largo medidos) · 3 viga DUPLICADA de su hermana ·
    #   4 seguidor RECONSTRUIDO del plano
    CO = None
    _co = os.path.join(SRC, 'sanjose_cotas.json')
    if os.path.exists(_co):
        with open(_co, encoding='utf-8') as f:
            CO = json.load(f)

    # El as-built del reparto va en el sistema LOCAL de la planta (cE/cN/base) y
    # su eje z apunta al SUR: zs = -n_sur. El visor dibuja en UTM absolutas, que
    # es lo que trae la nube. Se deshace aquí y no en dos sitios distintos.
    cE, cN, base = AB['meta']['cE'], AB['meta']['cN'], AB['meta']['base']
    nPor = collections.defaultdict(list)               # id de fila -> puntos de la nube
    for i in range(NB['n']):
        nPor[NB['filas'][NB['fi'][i]]].append(i)

    # CRUCE AS-BUILT ↔ COTAS. Cada viga de cotas se busca en el as-built por
    # (tracker, x). Las que aparecen se MARCAN con su origen; las que no —la
    # hermana duplicada de un seguidor levantado a medias, y el seguidor entero
    # que no se levantó— se AÑADEN, para que el mapa y la escena 3D dibujen la
    # misma planta. Los reconstruidos no llevan tk (no se levantaron): esos se
    # cruzan por geometría (misma x y solape en n).
    ORI, EXTRA = {}, []
    if CO:
        porTk = collections.defaultdict(list)
        for r in AB['f']:
            porTk[r['tk']].append(r)
        for ti, t in enumerate(CO['t']):
            if not t:
                continue
            for f in t['f']:
                og = (4 if t.get('est') else 3 if f.get('hm')
                      else 2 if f.get('ye') == 3 else 1 if f.get('ye') else 0)
                cand = [r for r in porTk.get(t.get('tk') or '', ()) if abs(r['x'] - f['x']) < 1.0]
                if not cand and t.get('est'):
                    cand = [r for r in AB['f'] if abs(r['x'] - f['x']) < 1.0
                            and min(-r['zs'], -r['zn']) < max(f['n']) - 1
                            and max(-r['zs'], -r['zn']) > min(f['n']) + 1]
                if cand:
                    ORI[cand[0]['id']] = og
                    continue
                # el seguidor reconstruido no tiene id de levantamiento (no se
                # levantó): se le da uno propio, el mismo para sus dos vigas,
                # para que en el visor sigan siendo UN seguidor
                tk = t.get('tk') or 'TR-PLANO-%04d' % ti
                EXTRA.append({'id': f.get('id') or tk, 'zo': t.get('zo') or 'SJ', 'tk': tk,
                              'x': f['x'], 'zs': -f['n'][0], 'zn': -f['n'][1],
                              'ys': f['y'][0], 'yn': f['y'][1],
                              'zm': None, 'ym': None, 'mods': f.get('md'),
                              'art': 0, 'pa': [], 'npt': 0, '_og': og})
        # la pareja del reconstruido: la de más al este es la -E
        for a in EXTRA:
            if a['id'].endswith(('-E', '-W')):
                continue
            par = [b for b in EXTRA if b['tk'] == a['tk']]
            a['id'] += '-E' if a['x'] >= max(b['x'] for b in par) else '-W'

    F = collections.defaultdict(list)
    idx, orden = {}, []
    for r in list(AB['f']) + EXTRA:
        fid, tid, side = r['id'], r['tk'], r['id'].rsplit('-', 1)[1]
        # una fila que el as-built midió y cotas NO conserva es una fila cuya
        # cota vino con otra referencia vertical: el modelo la repone, así que
        # tampoco puede pintarse como medida limpia
        og = r.get('_og', ORI.get(fid, 0 if not CO else 3))
        # LOS EXTREMOS SON LOS EXTREMOS, NO LA MEDIA DE LAS ESQUINAS. En Ayora
        # una fila es UNA mesa y sus dos puntos son sus dos puntas, asi que
        # promediar da lo mismo. En San Jose la fila es un TUBO DE DOS MESAS de
        # 36,74 m con una junta de 0,89 m en medio, y sus cuatro puntos son las
        # puntas de CADA mesa: hay dos etiquetados N y dos etiquetados S, a 37 m
        # unos de otros. Promediarlos colapsaba el tubo a la MITAD de su largo
        # (36,75 m declarados frente a 74,43 m que cubren sus propios puntos y
        # 75,12 m de separacion entre filas de la misma linea) y ademas lo
        # centraba justo en la junta: en el plano, las lineas de puntos caian
        # FUERA de las barras, que es como se vio. El reparto ya emite los
        # extremos de verdad, asi que aqui solo se traducen de sitio.
        #
        # Y no era solo el dibujo: la pendiente longitudinal salia de restar dos
        # medias, y eso ESCONDIA los saltos de referencia vertical. En
        # TR-09_1-044-E la mesa sur esta a 1531,7 m y la norte a 1568,7 —36,7 m
        # en el mismo tubo, imposible— y la resta de medias daba +0,28 %, un
        # numero de lo mas normal. Con los extremos de verdad sale ~+49 %, que
        # el propio filtro de 15 % ya descarta y marca la fila sin pendiente.
        y0, y1 = cN - r['zs'], cN - r['zn']            # punta sur / punta norte
        z0, z1 = base + r['ys'], base + r['yn']
        x = cE + r['x']
        L = abs(y1 - y0)
        sl = ((z1 - z0) / L * 100) if L > 5 else None  # pendiente longitudinal (%)
        if sl is not None and abs(sl) > 15:            # 15% es ya un talud: es un punto mal asignado, no un seguidor
            sl = None
        orden.append((fid, tid, side, x, y0, y1, z0, z1, sl, len(nPor.get(fid, ())), og))

    orden.sort(key=lambda t: (t[3], t[4]))              # de oeste a este, y de sur a norte
    for i, o in enumerate(orden):
        idx[o[0]] = i

    # --- pendiente transversal hacia la fila vecina de cada lado -------------
    # Vecina de cada lado: la fila contigua DE VERDAD — a menos de 1,6 pasos en X
    # y con solape en Y. Sin esas dos condiciones se emparejaban filas de bloques
    # distintos (al otro lado de un camino) y salían pendientes transversales
    # imposibles, de cientos por ciento.
    dxs = []
    porX = sorted(range(len(orden)), key=lambda i: (orden[i][3], orden[i][4]))
    for k in range(1, len(porX)):
        d = orden[porX[k]][3] - orden[porX[k - 1]][3]
        if 0.5 < d < 40:
            dxs.append(d)
    paso = statistics.median(dxs) if dxs else 6.0
    vecino = {}
    for k, i in enumerate(porX):
        xi, a0, a1 = orden[i][3], orden[i][4], orden[i][5]
        def busca(rango):
            for j in rango:
                dx = abs(orden[j][3] - xi)
                if dx < 0.5 or dx > 1.6 * paso:
                    continue
                b0, b1 = orden[j][4], orden[j][5]
                if min(a1, b1) - max(a0, b0) > 5:      # solapan a lo largo de la fila
                    return j
            return -1
        vecino[i] = (busca(porX[:k][::-1]), busca(porX[k + 1:]))

    def zmed(i):
        return (orden[i][6] + orden[i][7]) / 2

    for i, o in enumerate(orden):
        fid, tid, side, x, y0, y1, z0, z1, sl, npts, og = o
        vo, ve = vecino[i]
        so = se = None
        if vo >= 0:
            d = abs(x - orden[vo][3]);  so = (zmed(i) - zmed(vo)) / d * 100 if d > 0.5 else None
        if ve >= 0:
            d = abs(orden[ve][3] - x);  se = (zmed(ve) - zmed(i)) / d * 100 if d > 0.5 else None
        if so is not None and abs(so) > 25: so = None
        if se is not None and abs(se) > 25: se = None
        F['id'].append(fid)
        F['zo'].append(tid.split('-')[0].replace('TR_', '').replace('TR', '') or 'SJ')
        F['tk'].append(int(tid.split('-')[-1]) if tid.split('-')[-1].isdigit() else i)
        F['fl'].append(0 if side == 'W' else 1)
        F['tp'].append('1V')
        F['st'].append(0)
        F['ar'].append(0); F['ap'].append(0)           # articulaciones: no medidas en San José
        F['x'].append(num(x)); F['y0'].append(num(y0)); F['y1'].append(num(y1))
        F['z0'].append(num(z0)); F['z1'].append(num(z1))
        F['sl'].append(num(sl)); F['slt'].append(num(sl))
        F['so'].append(num(so, 2)); F['se'].append(num(se, 2))
        F['ao'].append(None); F['ae'].append(None); F['mo'].append(None); F['me'].append(None)
        F['vo'].append(vo); F['ve'].append(ve)
        F['ho'].append(0); F['he'].append(0)
        F['pp'].append(None); F['dp'].append(None)
        F['es'].append(3 if sl is None else 0)
        F['an'].append(1 if shear.get(tid, 0) > 0.5 else 0)
        F['ro'].append(None); F['re'].append(None)
        for k in ('to', 'tao', 'tmo', 'te', 'tae', 'tme'):
            F[k].append(None)
        F['tvo'].append(orden[vo][0] if vo >= 0 else '')
        F['tve'].append(orden[ve][0] if ve >= 0 else '')
        # ORIGEN DEL DATO DE ESTA VIGA, con su texto y su categoría. El visor
        # ya enseñaba `og` en rojo cuando no es «medido»; `oi` es lo mismo en
        # número, para poder pintarlo y filtrarlo en el mapa.
        F['og'].append(OG_TXT[og])
        F['oi'].append(og)

    # --- puntos del levantamiento -------------------------------------------
    # La nube ya viene en UTM absolutas y con su fila. El extremo (N/S) no lo
    # trae etiquetado —y menos mal: la etiqueta del proveedor era justo la que
    # colapsaba el tubo—, se decide por dónde cae respecto del centro de SU fila.
    P = collections.defaultdict(list)
    for fid, ks in nPor.items():
        if fid not in idx:
            continue
        i = idx[fid]
        medio = (orden[i][4] + orden[i][5]) / 2.0
        for k in ks:
            P['id'].append(NB['id'][k])
            P['x'].append(num(NB['x'][k])); P['y'].append(num(NB['y'][k])); P['z'].append(num(NB['z'][k]))
            P['f'].append(i)
            P['e'].append(1 if NB['y'][k] > medio else 0)
            P['j'].append(0)

    # --- cotas con otra referencia vertical ----------------------------------
    # No se corrigen ni se esconden: se MARCAN, y el visor las enseña. Una cota
    # de otro sistema no es un punto «raro», es un dato que hay que devolverle
    # al topógrafo con su id.
    P['r'], P['rd'] = ref_vertical.marca(P['x'], P['y'], P['z'])
    txt, nMal = ref_vertical.resumen(P['r'], P['rd'], P['f'])
    F['rv'] = [nMal.get(i, 0) for i in range(len(orden))]

    pit = []
    for i in range(len(orden)):
        for j in vecino[i]:
            if j >= 0:
                pit.append(abs(orden[j][3] - orden[i][3]))
    pit.sort()

    meta = dict(planta='San José', codigo='24019', cliente='Acciona',
                n_filas=len(orden), n_trk=len({o[1] for o in orden}), n_pts=len(P['id']),
                n_art=0, n_art_trk=0, n_art_plano=0, huso='19S',   # Arequipa (Peru), no 30N
                n_rv=sum(1 for v in P['r'] if v == ref_vertical.MARCADO),
                n_rv_filas=sum(1 for v in F['rv'] if v),
                pitch=round(pit[len(pit) // 2], 2) if pit else None,
                h_eje=None, azimut_eje=None)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('window.DATA=' + json.dumps(dict(meta=meta, f=dict(F), m={}, o={}, p=dict(P)),
                                            ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('filas:', len(orden), '· trackers:', meta['n_trk'], '· puntos:', meta['n_pts'],
          '· pitch:', meta['pitch'])
    print(txt)
    sl = [v for v in F['sl'] if v is not None]
    so = [v for v in F['so'] if v is not None]
    if sl:
        sl.sort(); print('pendiente longitudinal %%: min %.2f  mediana %.2f  max %.2f' % (sl[0], sl[len(sl)//2], sl[-1]))
    if so:
        so.sort(); print('pendiente transversal %%: min %.2f  mediana %.2f  max %.2f' % (so[0], so[len(so)//2], so[-1]))
    print('->', OUT)


if __name__ == '__main__':
    main()
