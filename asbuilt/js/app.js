/* ============================================================================
 * Visor Ayora — geometría as-built de seguidores y configuración de backtracking 3D
 * Datos en window.DATA (js/data.js), generados por tools/generate_data.py.
 * ==========================================================================*/
/* Una sola app para el as-built de módulos de TODAS las plantas. Las que aún no
   tienen medidas ciertas piezas —San José no lleva articulaciones ni motores
   levantados— traen esos bloques vacíos, y aquí se rellenan con listas vacías
   para que la app no tenga que preguntar por cada uno. */
const D = window.DATA, F = D.f, P = D.p, MET = D.meta;
const _vacio = n => { const o = {}; ['f','s','y0','y1','z0','z1','L','p','x','y','z','m','d'].forEach(k => o[k] = new Array(n).fill(null)); return o; };
const M = (D.m && D.m.f) ? D.m : _vacio(0);
const O = (D.o && D.o.x) ? D.o : _vacio((D.f && D.f.id) ? D.f.id.length : 0);
const NF = F.id.length, NP = P.id.length;
const plotDiv = document.getElementById('plot');
const EST_TXT = ['OK', 'Atención', 'Revisar', 'Sin dato'];
const EST_COL = ['#36c275', '#e8d44d', '#f5762a', '#5a606b'];
const EXT_TXT = ['Sur', 'Norte', 'Motor'];

/* ---------------- métricas por vista ---------------- */
const MODES = {
  bt3d: {
    help: 'Geometría del eje y pendiente hacia la fila vecina de cada lado. Al amanecer sombrea la del este; al atardecer, la del oeste.',
    metrics: [
      { k: 'sl', t: 'Pendiente longitudinal (%)', div: true },
      { k: 'so', t: 'Pendiente transversal al oeste (%)', div: true },
      { k: 'se', t: 'Pendiente transversal al este (%)', div: true },
      { k: 'dOE', t: 'Diferencia oeste − este (%)', div: true },
      { k: 'mo', t: 'Pendiente resultante al oeste (%)', div: false },
      { k: 'me', t: 'Pendiente resultante al este (%)', div: false },
      { k: 'ao', t: 'Azimut de máxima pendiente · oeste', azi: true },
      { k: 'ae', t: 'Azimut de máxima pendiente · este', azi: true },
      { k: 'tp', t: 'Tipo de seguidor', cat: 'tp' },
    ]
  },
  art: {
    help: 'Las 17 bifilas articuladas (34 filas). El quiebro es dato medido en el motor: las demás filas son vigas rígidas.',
    metrics: [
      { k: 'ar', t: 'Articulada / rígida', cat: 'ar' },
      { k: 'dmot', t: 'Desplazamiento del motor (m)', div: true },
      { k: 'dmesa', t: 'Diferencia de pendiente entre alas (%)', div: true },
      { k: 'sl', t: 'Pendiente longitudinal (%)', div: true },
    ]
  },
  asb: {
    help: 'Contraste con la geometría de proyecto de los ficheros .cdt. El sector anómalo concentra la mayor parte de las desviaciones.',
    metrics: [
      { k: 'dp', t: 'Δ pendiente medida − proyecto (%)', div: true },
      { k: 'es', t: 'Estado', cat: 'es' },
      { k: 'an', t: 'Sector anómalo', cat: 'an' },
      { k: 'pp', t: 'Pendiente de proyecto (%)', div: true },
    ]
  },
  pts: {
    help: 'Los 3.069 puntos del levantamiento, ya asignados a fila y extremo. Solo consulta: la asignación está cerrada y verificada.',
    metrics: [
      { k: 'e', t: 'Extremo medido', cat: 'e' },
      { k: 'j', t: 'Junta compartida entre trackers', cat: 'j' },
      { k: 'z', t: 'Cota medida (m)', div: false },
    ]
  }
};

let ui = { view: 'bt3d', metric: 'sl', zona: 'all', tipo: 'all', soloArt: false, soloAnom: false,
           filas: true, mot: false, pts: false, vec: false };
let sel = -1, uirev = 1, pendingRange = null;

/* ---------------- valores derivados ---------------- */
const dOE = new Float64Array(NF), dmot = new Float64Array(NF), dmesa = new Float64Array(NF);
dOE.fill(NaN); dmot.fill(NaN); dmesa.fill(NaN);
const mesasDe = new Map();
for (let i = 0; i < M.f.length; i++) {
  if (!mesasDe.has(M.f[i])) mesasDe.set(M.f[i], []);
  mesasDe.get(M.f[i]).push(i);
}
for (let i = 0; i < NF; i++) {
  if (F.so[i] != null && F.se[i] != null) dOE[i] = F.so[i] - F.se[i];
  dmot[i] = O.d[i];
  const ms = mesasDe.get(i);
  if (ms && ms.length === 2) dmesa[i] = M.p[ms[1]] - M.p[ms[0]];
}
function val(k, i) {
  if (k === 'dOE') return dOE[i];
  if (k === 'dmot') return dmot[i];
  if (k === 'dmesa') return dmesa[i];
  return F[k] ? F[k][i] : NaN;
}

/* ---------------- paletas ---------------- */
const DIV = ['#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b'];
const SEQ = ['#0d3b66', '#1c5d8c', '#2f80a8', '#4aa3b8', '#6fc0ac', '#a5d68a', '#dbdf6b', '#f4b24a', '#e2622f'];
const AZI = { N: '#4a9de0', NE: '#3fbf9a', E: '#7cc94a', SE: '#d8cf42', S: '#e8a33d', SO: '#dd6a4a', O: '#c85ea8', NO: '#8a6fd4' };
const AZI_ORD = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
function aziSector(a) { return AZI_ORD[Math.floor((((a % 360) + 360 + 22.5) % 360) / 45)]; }
const CATS = {
  tp: { vals: ['2TTx56', '2TTx42', '2TTx28'], cols: ['#4aa3b8', '#a5d68a', '#f4b24a'], lbl: v => v },
  ar: { vals: [1, 0], cols: ['#f5a623', '#3d5566'], lbl: v => v ? 'Articulada' : 'Rígida' },
  es: { vals: [0, 1, 2, 3], cols: EST_COL, lbl: v => EST_TXT[v] },
  an: { vals: [1, 0], cols: ['#dd6a4a', '#3d5566'], lbl: v => v ? 'Sector anómalo' : 'Resto' },
  e: { vals: [0, 1, 2], cols: ['#4aa3b8', '#a5d68a', '#f5a623'], lbl: v => EXT_TXT[v] },
  j: { vals: [1, 0], cols: ['#c85ea8', '#4aa3b8'], lbl: v => v ? 'En junta' : 'Extremo libre' }
};

/* ---------------- filtro ---------------- */
function pasa(i) {
  if (ui.zona !== 'all' && F.zo[i] !== ui.zona) return false;
  if (ui.tipo !== 'all' && F.tp[i] !== ui.tipo) return false;
  if (ui.soloArt && !F.ar[i]) return false;
  if (ui.soloAnom && !F.an[i]) return false;
  return true;
}

/* ---------------- binning ---------------- */
function bins(k, idxs) {
  const m = MODES[ui.view].metrics.find(x => x.k === k) || {};
  if (m.cat) {
    const c = CATS[m.cat];
    return { kind: 'cat', cat: c, key: (i) => (m.cat === 'e' ? P.e[i] : m.cat === 'j' ? P.j[i] : F[k][i]) };
  }
  if (m.azi) return { kind: 'azi' };
  const vs = idxs.map(i => val(k, i)).filter(v => v != null && !isNaN(v));
  if (!vs.length) return { kind: 'none' };
  vs.sort((a, b) => a - b);
  const lo = vs[Math.floor(0.02 * vs.length)], hi = vs[Math.floor(0.98 * vs.length)];
  if (m.div) { const a = Math.max(Math.abs(lo), Math.abs(hi)) || 1; return { kind: 'num', lo: -a, hi: a, pal: DIV }; }
  return { kind: 'num', lo, hi, pal: SEQ };
}
function binOf(b, v) {
  if (v == null || isNaN(v)) return -1;
  const n = b.pal.length;
  let k = Math.floor((v - b.lo) / (b.hi - b.lo) * n);
  return Math.max(0, Math.min(n - 1, k));
}
const fmt = (v, d = 2) => (v == null || isNaN(v)) ? '—' : v.toFixed(d);

/* ---------------- trazas ---------------- */
function trazasFilas(idxs, b) {
  const grupos = new Map();
  for (const i of idxs) {
    let g, col;
    if (b.kind === 'cat') { const v = F[ui.metric] ? F[ui.metric][i] : null; g = String(v); col = b.cat.cols[b.cat.vals.indexOf(v)] || '#555'; }
    else if (b.kind === 'azi') { const a = val(ui.metric, i); if (a == null) { g = '—'; col = '#3d5566'; } else { g = aziSector(a); col = AZI[g]; } }
    else { const k = binOf(b, val(ui.metric, i)); g = String(k); col = k < 0 ? '#3d5566' : b.pal[k]; }
    if (!grupos.has(g)) grupos.set(g, { col, x: [], y: [] });
    const s = grupos.get(g);
    // fila articulada -> dos tramos (quiebro real en el motor)
    const ms = mesasDe.get(i);
    if (F.ar[i] && ms) {
      for (const j of ms) { s.x.push(F.x[i], F.x[i], NaN); s.y.push(M.y0[j], M.y1[j], NaN); }
    } else {
      s.x.push(F.x[i], F.x[i], NaN); s.y.push(F.y0[i], F.y1[i], NaN);
    }
  }
  const out = [];
  for (const [g, s] of grupos) out.push({
    type: 'scattergl', mode: 'lines', x: s.x, y: s.y,
    line: { color: s.col, width: F.ar[0] !== undefined && ui.soloArt ? 4 : 2.5 },
    hoverinfo: 'skip', showlegend: false
  });
  return out;
}
function trazaHover(idxs) {
  const x = [], y = [], cd = [];
  for (const i of idxs) {
    x.push(F.x[i]); y.push((F.y0[i] + F.y1[i]) / 2);
    cd.push([F.id[i], F.tp[i], F.st[i], F.ar[i] ? 'articulada' : 'rígida',
      fmt(F.sl[i], 3), fmt(F.so[i]), fmt(F.se[i]),
      F.ao[i] == null ? '—' : (fmt(F.ao[i], 1) + '° ' + aziSector(F.ao[i])),
      F.ae[i] == null ? '—' : (fmt(F.ae[i], 1) + '° ' + aziSector(F.ae[i])),
      F.vo[i] >= 0 ? F.id[F.vo[i]] + (F.ho[i] ? ' (hermana)' : '') : '—',
      F.ve[i] >= 0 ? F.id[F.ve[i]] + (F.he[i] ? ' (hermana)' : '') : '—',
      fmt(F.dp[i], 3), EST_TXT[F.es[i]]]);
  }
  return {
    type: 'scattergl', mode: 'markers', x, y, customdata: cd,
    marker: { size: 7, color: 'rgba(255,255,255,0.01)', line: { width: 0 } },
    hovertemplate: '<b>%{customdata[0]}</b> · %{customdata[1]} · %{customdata[2]} strings · %{customdata[3]}<br>' +
      'pend. longitudinal %{customdata[4]} %<br>' +
      'transversal O %{customdata[5]} % · E %{customdata[6]} %<br>' +
      'azimut O %{customdata[7]} · E %{customdata[8]}<br>' +
      'vecina O %{customdata[9]}<br>vecina E %{customdata[10]}<br>' +
      'Δ vs proyecto %{customdata[11]} % · %{customdata[12]}<extra></extra>',
    showlegend: false
  };
}
function trazaMotores(idxs) {
  const s = new Set(idxs), x = [], y = [], c = [], cd = [];
  for (let i = 0; i < NF; i++) {
    if (!s.has(i)) continue;
    x.push(O.x[i]); y.push(O.y[i]); c.push(O.m[i] ? '#f5a623' : '#46708a');
    cd.push([F.id[i], fmt(O.z[i], 3), O.m[i] ? 'medida en campo' : 'interpolada (viga rígida)', fmt(O.d[i], 3)]);
  }
  return {
    type: 'scattergl', mode: 'markers', x, y, customdata: cd,
    marker: { size: 7, symbol: 'diamond', color: c, line: { width: 0 } },
    hovertemplate: 'Motor <b>%{customdata[0]}</b><br>cota %{customdata[1]} m (%{customdata[2]})<br>' +
      'desplazamiento respecto a la recta %{customdata[3]} m<extra></extra>', showlegend: false
  };
}
function trazaPuntos(idxs) {
  const s = new Set(idxs), x = [], y = [], c = [], cd = [];
  const b = bins(ui.metric, idxs);
  for (let k = 0; k < NP; k++) {
    if (!s.has(P.f[k])) continue;
    x.push(P.x[k]); y.push(P.y[k]);
    let col = '#8ab4d8';
    if (ui.view === 'pts') {
      if (b.kind === 'cat') { const v = ui.metric === 'e' ? P.e[k] : P.j[k]; col = b.cat.cols[b.cat.vals.indexOf(v)] || '#555'; }
      else if (b.kind === 'num') { const q = binOf(b, P.z[k]); col = q < 0 ? '#555' : b.pal[q]; }
    }
    c.push(col);
    cd.push([P.id[k], F.id[P.f[k]], EXT_TXT[P.e[k]], fmt(P.z[k], 3), P.j[k] ? 'sí' : 'no']);
  }
  return {
    type: 'scattergl', mode: 'markers', x, y, customdata: cd,
    marker: { size: 4, color: c, line: { width: 0 } },
    hovertemplate: 'Punto <b>%{customdata[0]}</b><br>fila %{customdata[1]} · extremo %{customdata[2]}<br>' +
      'cota %{customdata[3]} m · junta %{customdata[4]}<extra></extra>', showlegend: false
  };
}
function trazaSel() {
  if (sel < 0) return [];
  const t = [{
    type: 'scattergl', mode: 'lines', x: [F.x[sel], F.x[sel]], y: [F.y0[sel], F.y1[sel]],
    line: { color: '#46d4f4', width: 5 }, hoverinfo: 'skip', showlegend: false
  }];
  if (ui.vec) for (const j of [F.vo[sel], F.ve[sel]]) {
    if (j >= 0) t.push({
      type: 'scattergl', mode: 'lines', x: [F.x[j], F.x[j]], y: [F.y0[j], F.y1[j]],
      line: { color: '#f5a623', width: 4, dash: 'dot' }, hoverinfo: 'skip', showlegend: false
    });
  }
  return t;
}

/* ---------------- layout y render ---------------- */
function baseLayout() {
  const l = {
    paper_bgcolor: '#13151a', plot_bgcolor: '#0e1014', margin: { l: 62, r: 14, t: 14, b: 46 },
    xaxis: { title: { text: 'X · UTM 30N (m)', font: { size: 11 } }, color: '#8b919c', gridcolor: '#20232b', zeroline: false, tickfont: { family: 'monospace', size: 10 } },
    yaxis: { title: { text: 'Y · UTM 30N (m)', font: { size: 11 } }, color: '#8b919c', gridcolor: '#20232b', zeroline: false, scaleanchor: 'x', scaleratio: 1, tickfont: { family: 'monospace', size: 10 } },
    showlegend: false, dragmode: 'pan', uirevision: String(uirev),
    hoverlabel: { bgcolor: '#1b1e26', bordercolor: '#3a3f4b', font: { family: 'monospace', size: 11, color: '#e8eaed' }, align: 'left' }
  };
  if (pendingRange) { l.xaxis.range = pendingRange[0].slice(); l.yaxis.range = pendingRange[1].slice(); }
  return l;
}
let idxsActuales = [];
function render() {
  const idxs = []; for (let i = 0; i < NF; i++) if (pasa(i)) idxs.push(i);
  idxsActuales = idxs;
  const b = bins(ui.metric, idxs);
  const data = [];
  if (ui.filas && ui.view !== 'pts') data.push(...trazasFilas(idxs, b));
  if (ui.view === 'pts' || ui.pts) data.push(trazaPuntos(idxs));
  if (ui.mot) data.push(trazaMotores(idxs));
  data.push(...trazaSel());
  if (ui.view !== 'pts') data.push(trazaHover(idxs));
  Plotly.react(plotDiv, data, baseLayout(), { responsive: true, scrollZoom: true, displayModeBar: false });
  pintaLeyenda(b, idxs);
  pintaStats(idxs);
  document.getElementById('counts').innerHTML =
    '<span class="pill" style="--c:#36c275">' + idxs.length + ' filas</span>' +
    '<span class="pill" style="--c:#f5a623">' + idxs.filter(i => F.ar[i]).length + ' articuladas</span>';
}
function pintaLeyenda(b, idxs) {
  const el = document.getElementById('legend');
  const m = MODES[ui.view].metrics.find(x => x.k === ui.metric) || {};
  let h = '';
  if (b.kind === 'cat') {
    h = '<div class="swrow">' + b.cat.vals.map((v, k) =>
      '<span class="sw"><i style="background:' + b.cat.cols[k] + '"></i>' + b.cat.lbl(v) + '</span>').join('') + '</div>';
  } else if (b.kind === 'azi') {
    h = '<div class="swrow">' + AZI_ORD.map(s => '<span class="sw"><i style="background:' + AZI[s] + '"></i>' + s + '</span>').join('') + '</div>';
  } else if (b.kind === 'num') {
    h = '<div class="ramp">' + b.pal.map(c => '<i style="background:' + c + '"></i>').join('') + '</div>' +
      '<div class="ramplbl"><span>' + fmt(b.lo) + '</span><span>' + fmt((b.lo + b.hi) / 2) + '</span><span>' + fmt(b.hi) + '</span></div>';
  }
  el.innerHTML = h + '<p class="hint">' + (m.t || '') + '</p>';
}
function pintaStats(idxs) {
  const k = ui.metric;
  const vs = idxs.map(i => val(k, i)).filter(v => v != null && !isNaN(v));
  let h = '<b>' + idxs.length + '</b> filas · <b>' + new Set(idxs.map(i => F.zo[i] + F.tk[i])).size + '</b> bifilas<br>';
  if (vs.length && !(MODES[ui.view].metrics.find(x => x.k === k) || {}).cat) {
    vs.sort((a, b) => a - b);
    const med = vs[Math.floor(vs.length / 2)], mn = vs[0], mx = vs[vs.length - 1];
    const avg = vs.reduce((a, b) => a + b, 0) / vs.length;
    h += 'media <b>' + fmt(avg, 3) + '</b> · mediana <b>' + fmt(med, 3) + '</b><br>rango <b>' + fmt(mn, 3) + '</b> … <b>' + fmt(mx, 3) + '</b>';
  }
  document.getElementById('stats').innerHTML = h;
}
function pintaFicha() {
  const el = document.getElementById('ficha');
  if (sel < 0) { el.innerHTML = 'Haz clic en una fila del mapa.'; return; }
  const i = sel, ms = mesasDe.get(i);
  const lin = (a, b) => '<div class="fr"><span>' + a + '</span><b>' + b + '</b></div>';
  let h = '<div class="fid mono">' + F.id[i] + '</div>' +
    lin('Tipo', F.tp[i] + ' · ' + F.st[i] + ' strings') +
    lin('Viga', F.ar[i] ? 'articulada (2 alas)' : 'rígida') +
    lin('Longitud', fmt(F.y1[i] - F.y0[i], 2) + ' m') +
    lin('Cota eje S → N', fmt(F.z0[i], 3) + ' → ' + fmt(F.z1[i], 3) + ' m') +
    lin('Pend. longitudinal', fmt(F.sl[i], 3) + ' %');
  if (F.ar[i] && ms) h += lin('Ala sur / norte', fmt(M.p[ms[0]], 3) + ' % / ' + fmt(M.p[ms[1]], 3) + ' %') +
    lin('Desplaz. del motor', fmt(O.d[i], 3) + ' m');
  h += '<div class="fsep">Backtracking · lado oeste (atardecer)</div>' +
    lin('Pend. transversal', fmt(F.so[i]) + ' %') +
    lin('Pend. resultante', fmt(F.mo[i]) + ' %') +
    lin('Azimut', F.ao[i] == null ? '—' : fmt(F.ao[i], 1) + '° · ' + aziSector(F.ao[i])) +
    lin('Fila vecina', F.vo[i] >= 0 ? F.id[F.vo[i]] + (F.ho[i] ? ' · hermana' : '') : '—') +
    '<div class="fsep">Backtracking · lado este (amanecer)</div>' +
    lin('Pend. transversal', fmt(F.se[i]) + ' %') +
    lin('Pend. resultante', fmt(F.me[i]) + ' %') +
    lin('Azimut', F.ae[i] == null ? '—' : fmt(F.ae[i], 1) + '° · ' + aziSector(F.ae[i])) +
    lin('Fila vecina', F.ve[i] >= 0 ? F.id[F.ve[i]] + (F.he[i] ? ' · hermana' : '') : '—') +
    '<div class="fsep">Contraste con proyecto</div>' +
    lin('Pend. proyecto', fmt(F.pp[i], 3) + ' %') +
    lin('Δ pendiente', fmt(F.dp[i], 3) + ' %') +
    lin('Estado', EST_TXT[F.es[i]] + (F.an[i] ? ' · sector anómalo' : ''));
  if (F.og[i] !== 'medido') h += '<p class="hint" style="color:var(--edit)">' + F.og[i] + '</p>';
  el.innerHTML = h;
}

/* ---------------- exportación ---------------- */
function csv(nombre, cab, filas) {
  const num = v => (v == null || v === '' || (typeof v === 'number' && isNaN(v))) ? '' : String(v).replace('.', ',');
  const txt = [cab.join(';')].concat(filas.map(r => r.map(num).join(';'))).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['﻿' + txt], { type: 'text/csv;charset=utf-8' }));
  a.download = nombre; a.click(); URL.revokeObjectURL(a.href);
  flash(nombre + ' · ' + filas.length + ' filas');
}
function expBt3d() {
  const cab = ['id', 'zona', 'tracker', 'fila', 'tipo', 'strings', 'articulada', 'x', 'y_sur', 'y_norte',
    'z_eje_sur', 'z_eje_norte', 'longitud', 'pend_long_pct', 'ala_sur_pct', 'ala_norte_pct',
    'pend_transv_oeste_pct', 'pend_result_oeste_pct', 'azimut_oeste_deg', 'vecina_oeste', 'hermana_oeste',
    'pend_transv_este_pct', 'pend_result_este_pct', 'azimut_este_deg', 'vecina_este', 'hermana_este',
    'z_motor', 'motor_medido', 'origen'];
  const f = idxsActuales.map(i => {
    const ms = mesasDe.get(i);
    return [F.id[i], F.zo[i], F.tk[i], F.fl[i], F.tp[i], F.st[i], F.ar[i] ? 'SI' : 'NO',
      F.x[i], F.y0[i], F.y1[i], F.z0[i], F.z1[i], (F.y1[i] - F.y0[i]).toFixed(2), F.sl[i],
      ms ? M.p[ms[0]] : '', ms ? M.p[ms[1]] : '',
      F.so[i], F.mo[i], F.ao[i], F.vo[i] >= 0 ? F.id[F.vo[i]] : '', F.ho[i] ? 'SI' : 'NO',
      F.se[i], F.me[i], F.ae[i], F.ve[i] >= 0 ? F.id[F.ve[i]] : '', F.he[i] ? 'SI' : 'NO',
      O.z[i], O.m[i] ? 'SI' : 'NO', F.og[i]];
  });
  csv('ayora_config_bt3d.csv', cab, f);
}
function expVista() {
  if (ui.view === 'pts') {
    const s = new Set(idxsActuales), f = [];
    for (let k = 0; k < NP; k++) if (s.has(P.f[k])) f.push([P.id[k], P.x[k], P.y[k], P.z[k], F.id[P.f[k]], EXT_TXT[P.e[k]], P.j[k] ? 'SI' : 'NO']);
    csv('ayora_puntos.csv', ['punto', 'x', 'y', 'z', 'fila', 'extremo', 'junta'], f);
  } else if (ui.view === 'art') {
    const f = [];
    for (const i of idxsActuales) {
      const ms = mesasDe.get(i); if (!ms) continue;
      for (const j of ms) f.push([F.id[i], M.s[j], M.y0[j], M.y1[j], M.z0[j], M.z1[j], M.L[j], M.p[j], O.z[i], O.d[i]]);
    }
    csv('ayora_alas_articuladas.csv', ['fila', 'ala', 'y_ini', 'y_fin', 'z_ini', 'z_fin', 'longitud', 'pend_pct', 'z_motor', 'desplaz_motor'], f);
  } else {
    const f = idxsActuales.map(i => [F.id[i], F.tp[i], F.sl[i], F.pp[i], F.dp[i], EST_TXT[F.es[i]], F.an[i] ? 'SI' : 'NO']);
    csv('ayora_asbuilt.csv', ['fila', 'tipo', 'pend_medida_pct', 'pend_proyecto_pct', 'delta_pct', 'estado', 'sector_anomalo'], f);
  }
}
let flashT = null;
function flash(t) {
  const el = document.getElementById('flash'); el.textContent = t; el.style.opacity = 1;
  clearTimeout(flashT); flashT = setTimeout(() => el.style.opacity = 0, 1800);
}

/* ---------------- interfaz ---------------- */
function pintaMetricas() {
  const s = document.getElementById('metricSel');
  s.innerHTML = MODES[ui.view].metrics.map(m => '<option value="' + m.k + '">' + m.t + '</option>').join('');
  if (!MODES[ui.view].metrics.some(m => m.k === ui.metric)) ui.metric = MODES[ui.view].metrics[0].k;
  s.value = ui.metric;
  document.getElementById('viewHelp').textContent = MODES[ui.view].help;
}
document.querySelectorAll('input[name=view]').forEach(r => r.addEventListener('change', e => {
  /* "Asignación" no es una métrica: es la herramienta con la que se casan los
     puntos del levantamiento con su seguidor. Vive en la misma pantalla y en el
     mismo menú —antes era otra aplicación con otros menús— y solo aparece en las
     plantas que todavía tienen puntos por asignar. */
  if (e.target.value === 'edit') { document.body.classList.add('modo-editor'); return; }
  document.body.classList.remove('modo-editor');
  ui.view = e.target.value;
  ui.soloArt = (ui.view === 'art'); document.getElementById('chkArt').checked = ui.soloArt;
  document.getElementById('chkPts').checked = ui.pts = (ui.view === 'pts');
  pintaMetricas(); render();
}));
document.getElementById('metricSel').addEventListener('change', e => { ui.metric = e.target.value; render(); });
document.getElementById('zonaSel').addEventListener('change', e => { ui.zona = e.target.value; render(); });
document.getElementById('tipoSel').addEventListener('change', e => { ui.tipo = e.target.value; render(); });
[['chkArt', 'soloArt'], ['chkAnom', 'soloAnom'], ['chkFilas', 'filas'], ['chkMot', 'mot'], ['chkPts', 'pts'], ['chkVec', 'vec']]
  .forEach(([id, k]) => document.getElementById(id).addEventListener('change', e => { ui[k] = e.target.checked; render(); }));
document.getElementById('expBt3d').addEventListener('click', expBt3d);
document.getElementById('expView').addEventListener('click', expVista);

plotDiv.addEventListener('click', () => { });
function enganchaClick() {
  plotDiv.on('plotly_click', ev => {
    const p = ev.points && ev.points[0]; if (!p) return;
    if (p.data.customdata && p.data.customdata[p.pointIndex] && typeof p.data.customdata[p.pointIndex][0] === 'string'
      && p.data.customdata[p.pointIndex][0].indexOf('-') > 0) {
      const id = p.data.customdata[p.pointIndex][0];
      const k = F.id.indexOf(id); if (k >= 0) { sel = k; pintaFicha(); render(); }
    } else if (p.data.customdata) {
      const id = p.data.customdata[p.pointIndex][1];
      const k = F.id.indexOf(id); if (k >= 0) { sel = k; pintaFicha(); render(); }
    }
  });
  plotDiv.on('plotly_relayout', e => {
    if (e['xaxis.range[0]'] != null) pendingRange = [[e['xaxis.range[0]'], e['xaxis.range[1]']], [e['yaxis.range[0]'], e['yaxis.range[1]']]];
  });
}
addEventListener('keydown', e => { if (e.key === 'Escape') { sel = -1; pintaFicha(); render(); } });

/* ---------------- arranque ---------------- */
document.getElementById('hdrSub').textContent =
  MET.n_trk.toLocaleString('es') + ' bifilas · ' + MET.n_filas.toLocaleString('es') + ' filas · ' +
  MET.n_pts.toLocaleString('es') + ' puntos · ' + MET.n_art_trk + ' bifilas articuladas.';
document.getElementById('notas').innerHTML =
  'Pitch entre filas <b>' + MET.pitch.toFixed(3) + ' m</b>, uniforme (medido, no de proyecto). ' +
  'Eje norte-sur puro (azimut ' + MET.azimut_eje + '°). ' +
  'Las cotas <b>Z eje</b> son la cota medida sobre módulo menos ' + MET.h_eje + ' m; ' +
  'esa constante está por confirmar con el detalle de montaje y no afecta a pendientes ni azimutes. ' +
  'Azimut medido desde el norte en sentido horario, en la dirección de máxima pendiente descendente. ' +
  'El quiebro solo se aplica a las ' + MET.n_art_trk + ' bifilas con cota de motor medida; el resto son vigas rígidas.';
pintaMetricas(); pintaFicha(); render(); enganchaClick();
