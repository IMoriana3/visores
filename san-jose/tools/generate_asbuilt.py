#!/usr/bin/env python3
"""
generate_asbuilt.py — el as-built de módulos de San José, con el MISMO esquema
que el de Ayora, para que los dos visores sean uno solo.

El visor de Ayora lee `window.DATA = {meta, f, m, o, p}` donde `f` es una fila por
fila de seguidor con su geometría medida (extremos, cotas, pendiente longitudinal
y pendientes/azimut hacia las vecinas). San José tenía en su lugar el editor de
asignación puntos↔tracker, con los puntos ya casados pero sin derivar geometría.
Esto lo deriva:

  final_v2_labeled.csv  ->  una fila por (Tracker_ID, row_side), con sus 4 esquinas
                            (NW/NE/SW/SE) promediadas a extremo sur y extremo norte.
  shear.csv             ->  cizallado por seguidor (diferencia entre sus dos filas).

Salida: ../js/data.js con el esquema de Ayora (los campos que San José no puede
tener todavía —articulaciones, motores medidos— van vacíos, y el visor ya los
trata como "sin dato").

Uso:  cd san-jose/tools && python3 generate_asbuilt.py
"""
import os, csv, json, math, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, 'source')
OUT  = os.path.join(HERE, '..', 'js', 'data_asbuilt.js')


def rd(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(v, nd=3):
    return None if v is None else round(float(v), nd)


def main():
    ptos = [r for r in rd('final_v2_labeled.csv') if r.get('assigned') == 'True']
    shear = {r['tid']: float(r['shear']) for r in rd('shear.csv') if r.get('shear') not in (None, '')}

    # --- una "fila" por (tracker, lado W/E): sus 4 esquinas -------------------
    filas = collections.defaultdict(list)
    for r in ptos:
        tid, side = r['Tracker_ID'], r['row_side']
        if not tid or side not in ('W', 'E'):
            continue
        filas[(tid, side)].append(r)

    F = collections.defaultdict(list)
    idx, orden = {}, []
    for (tid, side), ps in filas.items():
        norte = [p for p in ps if p['corner'] in ('NW', 'NE')]
        sur   = [p for p in ps if p['corner'] in ('SW', 'SE')]
        if not norte or not sur:
            continue                                   # fila incompleta: sin geometría fiable
        y1 = statistics.fmean(float(p['Y']) for p in norte)
        y0 = statistics.fmean(float(p['Y']) for p in sur)
        z1 = statistics.fmean(float(p['Z']) for p in norte)
        z0 = statistics.fmean(float(p['Z']) for p in sur)
        x  = statistics.fmean(float(p['X']) for p in ps)
        L  = abs(y1 - y0)
        sl = ((z1 - z0) / L * 100) if L > 5 else None   # pendiente longitudinal (%); fila corta = extremos mal casados
        if sl is not None and abs(sl) > 15:            # 15% es ya un talud: es un punto mal asignado, no un seguidor
            sl = None
        fid = tid + '-' + side
        orden.append((fid, tid, side, x, y0, y1, z0, z1, sl, len(ps)))

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
        fid, tid, side, x, y0, y1, z0, z1, sl, npts = o
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
        F['og'].append('medido')

    # --- puntos del levantamiento -------------------------------------------
    P = collections.defaultdict(list)
    EXT = {'N': 1, 'S': 0}
    for r in ptos:
        fid = r['Tracker_ID'] + '-' + r['row_side']
        if fid not in idx:
            continue
        P['id'].append(int(float(r['id'])))
        P['x'].append(num(r['X'])); P['y'].append(num(r['Y'])); P['z'].append(num(r['Z']))
        P['f'].append(idx[fid])
        P['e'].append(EXT.get((r['corner'] or ' ')[0], 0))
        P['j'].append(0)

    pit = []
    for i in range(len(orden)):
        for j in vecino[i]:
            if j >= 0:
                pit.append(abs(orden[j][3] - orden[i][3]))
    pit.sort()

    meta = dict(planta='San José', codigo='24019', cliente='Acciona',
                n_filas=len(orden), n_trk=len({o[1] for o in orden}), n_pts=len(P['id']),
                n_art=0, n_art_trk=0, n_art_plano=0,
                pitch=round(pit[len(pit) // 2], 2) if pit else None,
                h_eje=None, azimut_eje=None)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('window.DATA=' + json.dumps(dict(meta=meta, f=dict(F), m={}, o={}, p=dict(P)),
                                            ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('filas:', len(orden), '· trackers:', meta['n_trk'], '· puntos:', meta['n_pts'],
          '· pitch:', meta['pitch'])
    sl = [v for v in F['sl'] if v is not None]
    so = [v for v in F['so'] if v is not None]
    if sl:
        sl.sort(); print('pendiente longitudinal %%: min %.2f  mediana %.2f  max %.2f' % (sl[0], sl[len(sl)//2], sl[-1]))
    if so:
        so.sort(); print('pendiente transversal %%: min %.2f  mediana %.2f  max %.2f' % (so[0], so[len(so)//2], so[-1]))
    print('->', OUT)


if __name__ == '__main__':
    main()
