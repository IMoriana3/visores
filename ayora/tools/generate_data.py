#!/usr/bin/env python3
"""
generate_data.py — genera js/data.js a partir de los CSV de tools/source/.

Entradas (tools/source/):
  filas.csv    : una fila por fila de tracker (1.508). Geometría del eje, pendiente
                 longitudinal, y pendiente/azimut transversal hacia la vecina de cada lado.
  mesas.csv    : los dos tramos de las filas articuladas (34 filas → 68 tramos).
  motores.csv  : posición y cota del motor de cada fila (medida en las articuladas,
                 interpolada en las rígidas).
  puntos.csv   : los 3.069 puntos del levantamiento, ya asignados a fila y extremo.

Salida:
  ../js/data.js  ->  window.DATA = { ... }

Uso:
  cd tools && python3 generate_data.py
"""
import os, csv, json, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, 'source')
OUT  = os.path.join(HERE, '..', 'js', 'data.js')

EST = {'ok': 0, 'atencion': 1, 'revisar': 2, 'sin dato': 3}
EXT = {'sur': 0, 'norte': 1, 'motor': 2}


def rd(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(v, nd=3):
    if v is None or v == '':
        return None
    return round(float(v), nd)


def main():
    filas = rd('filas.csv')
    mesas = rd('mesas.csv')
    motor = rd('motores.csv')
    ptos  = rd('puntos.csv')

    idx = {r['id']: i for i, r in enumerate(filas)}

    F = collections.defaultdict(list)
    for r in filas:
        F['id'].append(r['id'])
        F['zo'].append(r['zona'])
        F['tk'].append(int(r['tracker']))
        F['fl'].append(int(r['fila']))
        F['tp'].append(r['tipo'])
        F['st'].append(int(r['strings']))
        F['ar'].append(1 if r['articulada'] == 'SI' else 0)
        F['ap'].append(1 if r['art_plano'] == 'SI' else 0)
        F['x'].append(num(r['x']))
        F['y0'].append(num(r['y_sur']))
        F['y1'].append(num(r['y_norte']))
        F['z0'].append(num(r['z_sur']))
        F['z1'].append(num(r['z_norte']))
        F['sl'].append(num(r['pend_long']))
        F['slt'].append(num(r['pend_long_trk']))
        F['so'].append(num(r['s_oeste'], 2))
        F['se'].append(num(r['s_este'], 2))
        F['ao'].append(num(r['azi_oeste'], 1))
        F['ae'].append(num(r['azi_este'], 1))
        F['mo'].append(num(r['mag_oeste'], 2))
        F['me'].append(num(r['mag_este'], 2))
        F['vo'].append(idx.get(r['tcu_vec_oeste'].split(' ')[0], -1))
        F['ve'].append(idx.get(r['tcu_vec_este'].split(' ')[0], -1))
        F['ho'].append(1 if r['tcu_herm_oeste'] == 'SI' else 0)
        F['he'].append(1 if r['tcu_herm_este'] == 'SI' else 0)
        F['pp'].append(num(r['pend_proy']))
        F['dp'].append(num(r['d_pend']))
        F['es'].append(EST.get(r['estado'], 3))
        F['an'].append(1 if r['sector'] == 'anomalo' else 0)
        F['ro'].append(num(r['resid_oeste']))
        F['re'].append(num(r['resid_este']))
        for k, c in (('to', 'tcu_s_oeste'), ('tao', 'tcu_az_oeste'), ('tmo', 'tcu_mag_oeste'),
                     ('te', 'tcu_s_este'), ('tae', 'tcu_az_este'), ('tme', 'tcu_mag_este')):
            F[k].append(num(r[c]))
        F['tvo'].append(r['tcu_vec_oeste'])
        F['tve'].append(r['tcu_vec_este'])
        F['og'].append(r['origen'])

    M = collections.defaultdict(list)
    for r in mesas:
        M['f'].append(idx[r['id']])
        M['s'].append(r['mesa'])
        M['y0'].append(num(r['y_ini']))
        M['y1'].append(num(r['y_fin']))
        M['z0'].append(num(r['z_ini']))
        M['z1'].append(num(r['z_fin']))
        M['L'].append(num(r['L'], 2))
        M['p'].append(num(r['pend']))

    O = collections.defaultdict(list)
    for r in motor:
        O['x'].append(num(r['x']))
        O['y'].append(num(r['y']))
        O['z'].append(num(r['z']))
        O['m'].append(1 if r['medido'] == 'SI' else 0)
        O['d'].append(num(r['desplaz']))

    P = collections.defaultdict(list)
    for r in ptos:
        P['id'].append(int(r['pid']))
        P['x'].append(num(r['x']))
        P['y'].append(num(r['y']))
        P['z'].append(num(r['z']))
        P['f'].append(idx[r['fila']])
        P['e'].append(EXT[r['extremo']])
        P['j'].append(1 if r['junta'] == 'SI' else 0)

    # pitch real observado (mediana de las separaciones a cada lado)
    pit = []
    for i in range(len(filas)):
        for k in ('vo', 've'):
            j = F[k][i]
            if j >= 0:
                pit.append(abs(F['x'][j] - F['x'][i]))
    pit.sort()

    meta = dict(
        planta='Ayora', codigo='24025', cliente='',
        n_filas=len(filas), n_trk=len({(F['zo'][i], F['tk'][i]) for i in range(len(filas))}),
        n_pts=len(ptos), n_art=sum(F['ar']), n_art_trk=sum(F['ar']) // 2,
        n_art_plano=sum(F['ap']) // 2,
        pitch=round(pit[len(pit) // 2], 3),
        h_eje=0.829,
        azimut_eje=0.0014,
    )

    data = dict(meta=meta, f=dict(F), m=dict(M), o=dict(O), p=dict(P))
    js = 'window.DATA=' + json.dumps(data, separators=(',', ':'), ensure_ascii=False) + ';\n'
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(js)
    print('js/data.js  %.1f KB  ·  %d filas · %d puntos · %d filas articuladas'
          % (len(js) / 1024, meta['n_filas'], meta['n_pts'], meta['n_art']))


if __name__ == '__main__':
    main()
