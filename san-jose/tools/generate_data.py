#!/usr/bin/env python3
"""
generate_data.py — genera js/data.js a partir de los resultados de la asignación.

Entradas (en tools/source/):
  - final_v2_labeled.csv : puntos del levantamiento ya asignados y etiquetados
       columnas: id, X, Y, Z, assigned, tracker_idx, Tracker_ID, NCU, corner, mesa, row_side
  - tracker_master.csv   : catálogo de trackers del Excel oficial
       columnas: Tracker_ID, X_ref, Y_ref, NCU, 'NCU ACCIONA', PS, GW, TCU
  - shear.csv            : desfase Y entre filas por tracker (tid, shear)

Salida:
  - ../js/data.js  ->  window.DATA = { ... }

Incluye:
  * coloreado de grafo de trackers (7-8 colores, vecinos siempre distintos)
  * colores por NCU (rotación de tono por ángulo áureo)
  * estado por tracker (OK / REVISAR / INCOMPLETO / SIN_PUNTOS)
  * tracker más cercano por punto (para los puntos sin asignar)

Uso:
  cd tools && python3 generate_data.py
"""
import os, json, colorsys
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, 'source')
OUT  = os.path.join(HERE, '..', 'js', 'data.js')
BIFILA = 6.2  # separación entre filas de la bifila (m)

def main():
    final  = pd.read_csv(os.path.join(SRC, 'final_v2_labeled.csv'))
    master = pd.read_csv(os.path.join(SRC, 'tracker_master.csv')).reset_index(drop=True)
    shear  = pd.read_csv(os.path.join(SRC, 'shear.csv'))

    tid2i = {t: i for i, t in enumerate(master.Tracker_ID)}

    # --- NCU más cercana + tracker más cercano para puntos SIN asignar ---
    tree = cKDTree(master[['X_ref', 'Y_ref']].values)
    una = ~final.assigned
    if una.any():
        _, idx = tree.query(final.loc[una, ['X', 'Y']].values, k=1)
        final.loc[una, 'NCU'] = master.iloc[idx].NCU.values

    # nearest tracker idx por punto (asignado -> su tracker; sin asignar -> el más cercano)
    pne = final.Tracker_ID.map(tid2i).fillna(-1).astype(int).values.copy()
    if una.any():
        pne[np.where(una.values)[0]] = idx

    # --- estado por tracker ---
    asg = final[final.assigned]
    cnt = asg.groupby('Tracker_ID').agg(
        nNO=('corner', lambda s: (s == 'NW').sum()),
        nNE=('corner', lambda s: (s == 'NE').sum()),
        nSO=('corner', lambda s: (s == 'SW').sum()),
        nSE=('corner', lambda s: (s == 'SE').sum())).reset_index()
    cnt = cnt.merge(shear.rename(columns={'tid': 'Tracker_ID'}), on='Tracker_ID', how='left')
    status = {}
    for _, r in cnt.iterrows():
        has8 = (r.nNO == 2 and r.nNE == 2 and r.nSO == 2 and r.nSE == 2)
        if not has8:           status[r.Tracker_ID] = 'INCOMPLETO'
        elif pd.isna(r.shear) or r.shear < 3: status[r.Tracker_ID] = 'OK'
        else:                  status[r.Tracker_ID] = 'REVISAR'
    for t in master.Tracker_ID:
        status.setdefault(t, 'SIN_PUNTOS')
    master['estado'] = master.Tracker_ID.map(status)

    # --- coloreado de grafo: trackers adyacentes (dx<=14 y dy<=85) con color distinto ---
    coords = master[['X_ref', 'Y_ref']].values
    kt = cKDTree(coords)
    pairs = kt.query_pairs(r=90, output_type='ndarray')
    adj = {i: set() for i in range(len(master))}
    for a, b in pairs:
        if abs(coords[a, 0] - coords[b, 0]) <= 14 and abs(coords[a, 1] - coords[b, 1]) <= 85:
            adj[a].add(b); adj[b].add(a)
    order = sorted(range(len(master)), key=lambda i: -len(adj[i]))
    color = [-1] * len(master)
    for i in order:
        used = {color[j] for j in adj[i] if color[j] >= 0}
        c = 0
        while c in used: c += 1
        color[i] = c
    ncolors = max(color) + 1
    print(f"Coloreado de grafo: {ncolors} colores · conflictos: "
          f"{sum(1 for a in adj for b in adj[a] if color[a]==color[b])}")
    master['color'] = color

    # --- colores por NCU (ángulo áureo) ---
    def hsl(h, s, l):
        r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    ncus = sorted(master.NCU.unique())
    ncu_color = {int(n): hsl((k * 137.508) % 360, 0.65, 0.55) for k, n in enumerate(ncus)}

    PALETTE = ['#e6194B', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
               '#42d4f4', '#f032e6', '#bfef45', '#469990', '#9A6324'][:max(8, ncolors)]

    # --- arrays por punto ---
    corner_code = {'NE': 0, 'NW': 1, 'SE': 2, 'SW': 3}
    final = final.sort_values('id')
    final['ti']    = final.Tracker_ID.map(tid2i).fillna(-1).astype(int)
    final['ci']    = final.corner.map(corner_code).fillna(-1).astype(int)
    final['mi']    = final.mesa.fillna(-1).astype(int)
    final['ncu_i'] = final.NCU.fillna(-1).astype(int)
    pne_sorted = pd.Series(pne, index=pd.read_csv(os.path.join(SRC, 'final_v2_labeled.csv')).id.values).sort_index().values

    data = {
        'palette': PALETTE,
        'ncu_colors': {str(k): v for k, v in ncu_color.items()},
        'ncus': [int(n) for n in ncus],
        'px':  [round(float(v), 2) for v in final.X.values],
        'py':  [round(float(v), 2) for v in final.Y.values],
        'pz':  [round(float(v), 3) for v in final.Z.values],
        'pid': [int(v) for v in final.id.values],
        'pt':  [int(v) for v in final.ti.values],
        'pn':  [int(v) for v in final.ncu_i.values],
        'pc':  [int(v) for v in final.ci.values],
        'pm':  [int(v) for v in final.mi.values],
        'pa':  [bool(v) for v in final.assigned.values],
        'pne': [int(v) for v in pne_sorted],
        'tid':     list(master.Tracker_ID.values),
        'tcolor':  [int(v) for v in master.color.values],
        'tncu':    [int(v) for v in master.NCU.values],
        'tx':      [round(float(v), 2) for v in master.X_ref.values],
        'ty':      [round(float(v), 2) for v in master.Y_ref.values],
        'tstatus': list(master.estado.values),
        'tps':     list(master.PS.astype(str).values),
        'tgw':     [int(v) for v in master.GW.values],
        'ttcu':    [int(v) for v in master.TCU.values],
        'tncuacc': list(master['NCU ACCIONA'].astype(str).values),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('window.DATA=' + json.dumps(data, separators=(',', ':')) + ';\n')
    print(f"OK -> {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)  "
          f"{len(data['px'])} puntos, {len(data['tid'])} trackers, {len(ncus)} NCU")

if __name__ == '__main__':
    main()
