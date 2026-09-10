#!/usr/bin/env python3
"""
generate_asbuilt.py — el as-built de módulos de UNA PLANTA, con el mismo esquema
para todas, para que el visor (asbuilt/index.html) sea uno solo.

    python3 asbuilt/tools/generate_asbuilt.py <planta>        (por defecto sanjose)

Entradas, en asbuilt/source/<planta>/ — copiadas tal cual de cobertura-zigbee,
que es donde se generan (un reparto, un dibujo):

  <planta>_asbuilt.json  ->  una fila por (tracker, lado E/W), ya con sus extremos
  <planta>_puntos.json       medidos y sus puntos (tools/reparte_levantamiento.py).
  <planta>_cotas.json    ->  de dónde sale la cota de cada viga en el MODELO
                             (medida · una punta repuesta · las dos · copiada de
                             su hermana · del plano) y los puntos [id, desvío]
                             de cada cota repuesta (tools/cotas_asbuilt.py).
  meta.json              ->  OPCIONAL: lo que ni el plano ni el levantamiento
                             saben (p. ej. {"cliente": "Acciona"}); pisa la meta.

Salida: asbuilt/data/<planta>.js — el fichero que CARGA la página — y una
entrada en asbuilt/data/plantas.js, que es de donde el selector de la página
saca las plantas disponibles. La meta (nombre, código, huso UTM) sale del
propio as-built, que la hereda del layout: aquí no hay nada escrito a mano.

CÓMO CARGAR UNA PLANTA NUEVA (p. ej. elburgo):
  1. en cobertura-zigbee: elburgo_layout.json (el plano) + elburgo_levantamiento.csv
     (el CSV del topógrafo, id,X,Y,Z sin tocar);
     python3 tools/reparte_levantamiento.py elburgo ; python3 tools/cotas_asbuilt.py elburgo
  2. copiar elburgo_asbuilt.json, elburgo_puntos.json y elburgo_cotas.json a
     asbuilt/source/elburgo/ ;  python3 asbuilt/tools/generate_asbuilt.py elburgo
  3. abrir asbuilt/?planta=elburgo

DE DÓNDE VENÍA. Esto nació como san-jose/tools/generate_asbuilt.py, escrito
para San José: rutas, huso 19S y nombres clavados. Lo que hace no tiene nada de
San José —cruzar el as-built con la nube y con las cotas del modelo y traducirlo
al esquema del visor—, así que se parametriza por planta y se deja aquí, junto
al visor que lo consume. La historia de por qué el reparto se rehízo (la
asignación del proveedor tenía 93 trackers con puntos imposibles y decidía la
fase tracker a tracker) está en el historial del simulador.
"""
import os, csv, json, math, collections, statistics, sys

HERE   = os.path.dirname(os.path.abspath(__file__))
PLANTA = (sys.argv[1] if len(sys.argv) > 1 else 'sanjose').strip().lower().replace('-', '')
SRC    = os.path.join(HERE, '..', 'source', PLANTA)
# EL FICHERO QUE SIRVE LA PÁGINA, no una copia suya (asbuilt/index.html lee
# data/<planta>.js). Y el manifiesto de plantas, del que sale el selector.
OUT  = os.path.join(HERE, '..', 'data', PLANTA + '.js')
MANI = os.path.join(HERE, '..', 'data', 'plantas.js')
sys.path.insert(0, HERE)
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
    with open(os.path.join(SRC, PLANTA + '_asbuilt.json'), encoding='utf-8') as f:
        AB = json.load(f)
    with open(os.path.join(SRC, PLANTA + '_puntos.json'), encoding='utf-8') as f:
        NB = json.load(f)
    # EL CIZALLADO SE MIDE AQUI, DE LA GEOMETRIA QUE SE DIBUJA. Antes venia de
    # shear.csv, calculado sobre la asignacion vieja del proveedor: marcaba 59
    # seguidores como «sector anomalo» y, medido sobre el reparto nuevo, solo 1
    # de ellos tiene de verdad las vigas corridas — las otras 58 marcas eran de
    # una asignacion que ya no existe. Se calcula abajo, viga E contra viga W
    # del mismo seguidor, y la marca sale de eso.
    shear = {}
    # DE DÓNDE SALE CADA VIGA EN EL MODELO. El as-built del reparto trae la
    # geometría medida; el que decide qué cota es medida y qué cota se repone
    # es `cotas_asbuilt.py`, y eso vive en sanjose_cotas.json. Sin cruzarlos, el
    # visor pintaba igual una viga con sus cuatro puntas medidas y una copiada
    # de su hermana, que es justo lo que hay que poder distinguir.
    #   0 medida · 1 una punta repuesta del terreno vecino · 2 las dos cotas
    #   repuestas (posición y largo medidos) · 3 viga DUPLICADA de su hermana ·
    #   4 seguidor RECONSTRUIDO del plano
    CO = None
    _co = os.path.join(SRC, PLANTA + '_cotas.json')
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
    ORI, EXTRA, JUN = {}, [], {}
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
                    # y la junta que el MODELO conserva: nm/ym (norte positivo).
                    # En una fila con cota repuesta el modelo la suelta y la fila
                    # va rigida; el as-built crudo aun la trae, con la cota
                    # contaminada (daba motores «desplazados» 37 m).
                    JUN[cand[0]['id']] = (f.get('nm'), f.get('ym'))
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
    M, O = collections.defaultdict(list), collections.defaultdict(list)
    GAP = float(AB['meta'].get('gapDrive') or 0.55)   # hueco del accionamiento en la junta (m)
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
        # LA JUNTA (el morro): donde el tubo articula y donde va el motor. El
        # as-built la trae medida (zm/ym) en las filas con sus cuatro puntos;
        # las reparadas y las del plano no la tienen. Con ella la fila se
        # dibuja como sus DOS mesas y se puede trazar la biela entre las dos
        # vigas del seguidor.
        # EL 2D DIBUJA EL LEVANTAMIENTO TAL CUAL: puntas y junta del as-built,
        # que es lo que el topografo entrego (la cota contaminada va MARCADA,
        # no corregida). Del modelo solo se toma una decision: si el modelo
        # soltó la junta —fila con una o dos cotas repuestas, que va rígida—
        # aquí también va rígida. Mezclar puntas del as-built con la junta del
        # modelo daba motores «desplazados» 37 m en las copias de hermana.
        # (la copia de hermana también: su as-built es la fila que el modelo
        # descartó, con la junta sana y las puntas a +36 m, y articularla
        # dibuja una mesa al 200 %; el modelo la sustituye entera)
        # y la fila cuya JUNTA es la contaminada (puntas sanas, ye=0): el
        # modelo la suelta (nm=None) y la fila va rigida
        modelo_rigida = bool(CO) and (og in (1, 2, 3) or (fid in JUN and JUN[fid][0] is None))
        if modelo_rigida:
            jm = jz = None
        else:
            jm = (cN - r['zm']) if r.get('zm') is not None else None
            jz = (base + r['ym']) if r.get('ym') is not None else None
        orden.append((fid, tid, side, x, y0, y1, z0, z1, sl, len(nPor.get(fid, ())), og, jm, jz))

    orden.sort(key=lambda t: (t[3], t[4]))              # de oeste a este, y de sur a norte
    for i, o in enumerate(orden):
        idx[o[0]] = i
    # cizallado por seguidor: cuanto se corre a lo largo del eje el centro de
    # una viga respecto del de su hermana (las dos comparten tubo: deberia ser
    # ~0). Por id de tracker, con las dos vigas presentes.
    _c = collections.defaultdict(list)
    for o in orden:
        _c[o[1]].append((o[4] + o[5]) / 2.0)
    shear = {tid: abs(v[0] - v[1]) for tid, v in _c.items() if len(v) == 2}

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
        fid, tid, side, x, y0, y1, z0, z1, sl, npts, og, jm, jz = o
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
        # ARTICULADA = con la junta medida: la fila son dos mesas que pivotan
        # en el morro, y asi se dibuja. Sin junta (cota repuesta, del plano) va
        # como viga rigida, que es lo que el modelo hace con ella.
        art = 1 if (jm is not None and jz is not None) else 0
        F['ar'].append(art); F['ap'].append(0)
        # el motor (O): en el morro si esta medido; si no, en el centro y marcado
        if art:
            t = (jm - y0) / (y1 - y0) if abs(y1 - y0) > 1e-6 else 0.5
            recta = z0 + (z1 - z0) * t
            O['x'].append(num(x)); O['y'].append(num(jm)); O['z'].append(num(jz)); O['m'].append(1)
            O['d'].append(num(jz - recta))
            # las dos mesas, con el hueco del accionamiento en la junta
            g = GAP / 2.0
            for lado, a, b in (('sur', y0, jm - g), ('norte', jm + g, y1)):
                # cotas de cada mesa: la punta medida y la junta medida
                if lado == 'sur':  za, zb = z0, jz
                else:              za, zb = jz, z1
                Lm = abs(b - a)
                M['f'].append(i); M['s'].append(lado)
                M['y0'].append(num(a)); M['y1'].append(num(b))
                M['z0'].append(num(za)); M['z1'].append(num(zb))
                M['L'].append(num(Lm, 2)); M['p'].append(num((zb - za) / Lm * 100 if Lm > 1 else None))
        else:
            O['x'].append(num(x)); O['y'].append(num((y0 + y1) / 2.0)); O['z'].append(num((z0 + z1) / 2.0))
            O['m'].append(0); O['d'].append(None)
        F['x'].append(num(x)); F['y0'].append(num(y0)); F['y1'].append(num(y1))
        F['z0'].append(num(z0)); F['z1'].append(num(z1))
        F['sl'].append(num(sl)); F['slt'].append(num(sl))
        F['so'].append(num(so, 2)); F['se'].append(num(se, 2))
        F['ao'].append(None); F['ae'].append(None); F['mo'].append(None); F['me'].append(None)
        F['vo'].append(vo); F['ve'].append(ve)
        F['ho'].append(0); F['he'].append(0)
        F['pp'].append(None); F['dp'].append(None)
        F['es'].append(3 if sl is None else 0)
        F['an'].append(1 if shear.get(tid, 0) > 0.5 else 0)   # sector anomalo: vigas corridas > 0,5 m
        F['sh'].append(num(shear.get(tid), 3))
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

    # nombre, codigo y huso: del as-built, que los hereda del layout de la
    # planta. Sin huso declarado, el visor dice «UTM» a secas: no se inventa.
    # Lo que ni el layout ni el levantamiento saben (el cliente, p. ej.) va
    # DECLARADO a mano en source/<planta>/meta.json, y pisa a lo heredado.
    MA = dict(AB.get('meta', {}))
    _mj = os.path.join(SRC, 'meta.json')
    if os.path.exists(_mj):
        with open(_mj, encoding='utf-8') as f:
            MA.update(json.load(f))
    meta = dict(planta=MA.get('planta') or PLANTA, codigo=MA.get('codigo') or '',
                cliente=MA.get('cliente') or '',
                n_filas=len(orden), n_trk=len({o[1] for o in orden}), n_pts=len(P['id']),
                n_art=sum(F['ar']), n_art_trk=len({orden[i][1] for i in range(len(orden)) if F['ar'][i]}),
                n_art_plano=0, huso=MA.get('huso'),
                n_rv=sum(1 for v in P['r'] if v == ref_vertical.MARCADO),
                n_rv_filas=sum(1 for v in F['rv'] if v),
                pitch=round(pit[len(pit) // 2], 2) if pit else None,
                h_eje=None, azimut_eje=None)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('window.DATA=' + json.dumps(dict(meta=meta, f=dict(F), m=dict(M), o=dict(O), p=dict(P)),
                                            ensure_ascii=False, separators=(',', ':')) + ';\n')
    # el manifiesto: una entrada por planta generada (Ayora la escribe su propio
    # generador; si aún no está, se conserva lo que haya)
    mani = {}
    if os.path.exists(MANI):
        with open(MANI, encoding='utf-8') as f:
            txt = f.read()
            mani = json.loads(txt[txt.index('=') + 1:].rstrip().rstrip(';'))
    mani[PLANTA] = dict(titulo=meta['planta'], codigo=meta['codigo'], huso=meta['huso'],
                        n_filas=meta['n_filas'], n_trk=meta['n_trk'], n_pts=meta['n_pts'])
    with open(MANI, 'w', encoding='utf-8') as f:
        f.write('window.PLANTAS=' + json.dumps(mani, ensure_ascii=False, sort_keys=True) + ';\n')
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
