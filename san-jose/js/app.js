/* ====== San José · visor + editor de asignación puntos–tracker ====== */
const D = window.DATA;
const N = D.px.length;
const NT = D.tid.length;
const CL = {0:'NE',1:'NO',2:'SE',3:'SO'};
const CIN = {NE:0,NO:1,SE:2,SO:3};
const STC = {OK:'#36c275', REVISAR:'#f5a623', INCOMPLETO:'#e8d44d', SIN_PUNTOS:'#e0508a'};
const BIFILA = 6.2;
const plotDiv = document.getElementById('plot');

/* ---- mutable model ---- */
let asg = new Int32Array(N);
let cor = new Int16Array(N);
let mes = new Int16Array(N);
for(let i=0;i<N;i++){ asg[i]=D.pt[i]; cor[i]=D.pc[i]; mes[i]=D.pm[i]; }
let origAsg = Int32Array.from(asg);
let qual = D.tstatus.slice();
let trkPts = new Map();
function rebuildTrkPts(){ trkPts=new Map(); for(let t=0;t<NT;t++) trkPts.set(t,[]); for(let i=0;i<N;i++){ if(asg[i]>=0) trkPts.get(asg[i]).push(i);} }
rebuildTrkPts();

let ui = { ncu:'all', status:'all', mode:'tracker', motors:true, unassigned:true };
let selectedPoint=-1, trkHighlight=-1;
let uirev=1, pendingRange=null;
let history=[];
let traceMeta=[];

/* ---- geometry helpers ---- */
function ncuOf(i){ return asg[i]>=0 ? D.tncu[asg[i]] : D.pn[i]; }
function rowIsE(i,t){ return Math.abs(D.px[i]-D.tx[t]) <= Math.abs(D.px[i]-(D.tx[t]-BIFILA)); }
function relabelTracker(t){
  const pts=trkPts.get(t)||[];
  for(const i of pts){ cor[i]=-1; mes[i]=-1; }
  const E=[],W=[];
  for(const i of pts){ (rowIsE(i,t)?E:W).push(i); }
  const spec=[[1,'N'],[1,'S'],[2,'N'],[2,'S']];
  [['E',E],['O',W]].forEach(([rc,row])=>{
    row.sort((a,b)=>D.py[b]-D.py[a]);
    for(let k=0;k<row.length && k<4;k++){
      const i=row[k]; mes[i]=spec[k][0];
      cor[i]=CIN[spec[k][1]+rc];   // NE/SE or NO/SO
    }
  });
}
function recomputeQual(t){
  const pts=trkPts.get(t)||[];
  if(pts.length===0){ qual[t]='SIN_PUNTOS'; return; }
  const c=[0,0,0,0];
  for(const i of pts){ if(cor[i]>=0) c[cor[i]]++; }
  qual[t]=(c[0]===2&&c[1]===2&&c[2]===2&&c[3]===2)?'OK':'INCOMPLETO';
}
function assign(i,t,record){
  const from=asg[i];
  if(from===t) return;
  if(record) history.push({i,from,to:t});
  if(from>=0){ const a=trkPts.get(from); const k=a.indexOf(i); if(k>=0) a.splice(k,1); }
  asg[i]=t;
  if(t>=0) trkPts.get(t).push(i); else { cor[i]=-1; mes[i]=-1; }
  if(from>=0){ relabelTracker(from); recomputeQual(from); }
  if(t>=0){ relabelTracker(t); recomputeQual(t); }
}
function editedCount(){ let n=0; for(let i=0;i<N;i++) if(asg[i]!==origAsg[i]) n++; return n; }

/* ---- bbox ---- */
function minMax(a){let mn=Infinity,mx=-Infinity;for(let k=0;k<a.length;k++){const v=a[k];if(v<mn)mn=v;if(v>mx)mx=v;}return[mn,mx];}
function squareRange(x0,x1,y0,y1,pad){let cx=(x0+x1)/2,cy=(y0+y1)/2,h=Math.max(x1-x0,y1-y0)/2;if(!isFinite(h)||h<=0)h=50;h*=(1+pad);return[[cx-h,cx+h],[cy-h,cy+h]];}
function bboxForNCU(ncu){const xs=[],ys=[];for(let i=0;i<N;i++){if(ncu===null||ncuOf(i)===ncu){xs.push(D.px[i]);ys.push(D.py[i]);}}if(!xs.length){for(let t=0;t<NT;t++){if(ncu===null||D.tncu[t]===ncu){xs.push(D.tx[t]);ys.push(D.ty[t]);}}}const[xa,xb]=minMax(xs),[ya,yb]=minMax(ys);return squareRange(xa,xb,ya,yb,0.04);}

/* ---- filters ---- */
function statusMatch(s){
  switch(ui.status){
    case 'all':return true;
    case 'OK':return s==='OK';
    case 'no':return s!=='OK';
    case 'INCOMPLETO':return s==='INCOMPLETO';
    case 'REVISAR':return s==='REVISAR';
    case 'SIN_PUNTOS':return s==='SIN_PUNTOS';
  }
  return true;
}
function pointColor(i){
  if(ui.mode==='ncu') return D.ncu_colors[ncuOf(i)];
  if(ui.mode==='estado') return (asg[i]>=0?STC[qual[asg[i]]]:'#888')||'#888';
  return D.palette[D.tcolor[asg[i]]];
}
function buildCustom(i){
  const a=asg[i]>=0;
  const tlabel=a?D.tid[asg[i]]:('sin asignar · cerca de '+(D.pne[i]>=0?D.tid[D.pne[i]]:'—'));
  const est=a?qual[asg[i]]:'—';
  const corner=cor[i]>=0?CL[cor[i]]:'—';
  const mesa=mes[i]>=0?mes[i]:'—';
  return [D.pid[i],tlabel,ncuOf(i),corner,mesa,est];
}

/* ---- layout ---- */
function baseLayout(){
  const lay={
    paper_bgcolor:'#13151a',plot_bgcolor:'#0e1014',
    margin:{l:60,r:14,t:14,b:46},
    xaxis:{title:{text:'X (UTM)',font:{size:11}},color:'#8b919c',gridcolor:'#20232b',zeroline:false,tickfont:{family:'monospace',size:10}},
    yaxis:{title:{text:'Y (UTM)',font:{size:11}},color:'#8b919c',gridcolor:'#20232b',zeroline:false,scaleanchor:'x',scaleratio:1,tickfont:{family:'monospace',size:10}},
    showlegend:false,
    hoverlabel:{bgcolor:'#1b1e26',bordercolor:'#3a3f4b',font:{family:'monospace',size:11,color:'#e8eaed'},align:'left'},
    uirevision:String(uirev),dragmode:'pan',
  };
  if(pendingRange){lay.xaxis.range=pendingRange[0].slice();lay.yaxis.range=pendingRange[1].slice();}
  return lay;
}

/* ---- render ---- */
function render(){
  const showNCU = ui.ncu==='all'?null:parseInt(ui.ncu);
  const cx=[],cy=[],cc=[],ccd=[],cIdx=[];
  const sx=[],sy=[],scd=[],sIdx=[];
  const ex=[],ey=[];                 // edited overlay
  for(let i=0;i<N;i++){
    if(showNCU!==null && ncuOf(i)!==showNCU) continue;
    if(asg[i]>=0){
      if(!statusMatch(qual[asg[i]])) continue;
      cx.push(D.px[i]); cy.push(D.py[i]); cc.push(pointColor(i)); ccd.push(buildCustom(i)); cIdx.push(i);
      if(asg[i]!==origAsg[i]){ ex.push(D.px[i]); ey.push(D.py[i]); }
    } else {
      if(!ui.unassigned || ui.status==='OK') continue;
      sx.push(D.px[i]); sy.push(D.py[i]); scd.push(buildCustom(i)); sIdx.push(i);
      if(origAsg[i]>=0){ ex.push(D.px[i]); ey.push(D.py[i]); }
    }
  }
  const mx=[],my=[],mc=[],mcd=[],mIdx=[];
  if(ui.motors){
    for(let t=0;t<NT;t++){
      if(showNCU!==null && D.tncu[t]!==showNCU) continue;
      if(!statusMatch(qual[t])) continue;
      mx.push(D.tx[t]); my.push(D.ty[t]); mc.push(D.ncu_colors[D.tncu[t]]);
      mcd.push([D.tid[t],D.tncu[t],qual[t],D.tps[t],D.tgw[t],D.ttcu[t]]); mIdx.push(t);
    }
  }
  const traces=[]; traceMeta=[];
  traces.push({type:'scattergl',mode:'markers',x:cx,y:cy,marker:{size:5,color:cc,line:{width:0}},customdata:ccd,
    hovertemplate:'ID %{customdata[0]}<br>Tracker <b>%{customdata[1]}</b><br>NCU %{customdata[2]} · Esquina %{customdata[3]} (mesa %{customdata[4]})<br>Estado %{customdata[5]}<extra></extra>'});
  traceMeta.push({kind:'assigned',idx:cIdx});
  if(ui.unassigned && ui.status!=='OK'){
    traces.push({type:'scattergl',mode:'markers',x:sx,y:sy,marker:{size:9,color:'#f4f4f4',symbol:'square',line:{width:1,color:'#0a0a0a'}},customdata:scd,
      hovertemplate:'ID %{customdata[0]}<br><b>%{customdata[1]}</b><br>NCU %{customdata[2]}<extra></extra>'});
    traceMeta.push({kind:'unassigned',idx:sIdx});
  }
  if(ui.motors){
    traces.push({type:'scattergl',mode:'markers',x:mx,y:my,marker:{size:9,color:mc,symbol:'diamond',line:{width:0.8,color:'#0a0a0a'}},customdata:mcd,
      hovertemplate:'MOTOR <b>%{customdata[0]}</b><br>NCU %{customdata[1]} · Estado %{customdata[2]}<br>PS %{customdata[3]} · GW %{customdata[4]} · TCU %{customdata[5]}<extra></extra>'});
    traceMeta.push({kind:'motor',idx:mIdx});
  }
  if(ex.length){
    traces.push({type:'scattergl',mode:'markers',x:ex,y:ey,marker:{size:11,color:'rgba(0,0,0,0)',symbol:'circle-open',line:{width:1.6,color:'#f5a623'}},hoverinfo:'skip'});
    traceMeta.push({kind:'none'});
  }
  if(selectedPoint>=0){
    traces.push({type:'scattergl',mode:'markers',x:[D.px[selectedPoint]],y:[D.py[selectedPoint]],marker:{size:20,color:'rgba(0,0,0,0)',symbol:'circle-open',line:{width:3,color:'#46d4f4'}},hoverinfo:'skip'});
    traceMeta.push({kind:'none'});
  }
  if(trkHighlight>=0){
    traces.push({type:'scattergl',mode:'markers',x:[D.tx[trkHighlight]],y:[D.ty[trkHighlight]],marker:{size:28,color:'rgba(0,0,0,0)',symbol:'circle-open',line:{width:3,color:'#ffffff'}},hoverinfo:'skip'});
    traceMeta.push({kind:'none'});
  }
  Plotly.react(plotDiv,traces,baseLayout(),{responsive:true,displaylogo:false,scrollZoom:true,modeBarButtonsToRemove:['select2d','lasso2d','autoScale2d']});
  pendingRange=null;
  document.getElementById('stats').innerHTML='<b>'+(cx.length+sx.length)+'</b> puntos · '+cx.length+' asignados · <b>'+sx.length+'</b> sin asignar'+(ui.motors?(' · '+mx.length+' motores'):'');
  updateCounts();
}

function updateCounts(){
  let ok=0,inc=0,rev=0,vac=0;
  for(let t=0;t<NT;t++){ const q=qual[t]; if(q==='OK')ok++; else if(q==='INCOMPLETO')inc++; else if(q==='REVISAR')rev++; else vac++; }
  document.getElementById('counts').innerHTML=
    '<span class="pill" style="--c:'+STC.OK+'">'+ok+' completos</span>'+
    '<span class="pill" style="--c:'+STC.INCOMPLETO+'">'+inc+' incompletos</span>'+
    '<span class="pill" style="--c:'+STC.REVISAR+'">'+rev+' revisar</span>'+
    '<span class="pill" style="--c:'+STC.SIN_PUNTOS+'">'+vac+' sin pts</span>';
  document.getElementById('editCount').textContent=editedCount()+' ediciones';
}

/* ---- selection / editing ---- */
function selectPoint(i){
  selectedPoint=i;
  const a=asg[i]>=0;
  const cur=a?D.tid[asg[i]]:'(sin asignar)';
  const near=D.pne[i]>=0?D.tid[D.pne[i]]:'';
  document.getElementById('selInfo').innerHTML=
    'Punto <b class="mono">'+D.pid[i]+'</b><br>Actual: <b class="mono">'+cur+'</b>'+(a&&cor[i]>=0?(' · '+CL[cor[i]]+' m'+mes[i]):'');
  const inp=document.getElementById('targetTrk');
  inp.value=a?D.tid[asg[i]]:near;
  document.getElementById('editBox').classList.add('active');
  render();
}
function clearSelection(){ selectedPoint=-1; document.getElementById('editBox').classList.remove('active'); document.getElementById('selInfo').innerHTML='Haz clic en un punto para seleccionarlo.'; render(); }
function doAssign(){
  if(selectedPoint<0){ flash('Selecciona primero un punto'); return; }
  const q=document.getElementById('targetTrk').value.trim().toUpperCase();
  let t=D.tid.findIndex(x=>x.toUpperCase()===q);
  if(t<0) t=D.tid.findIndex(x=>x.toUpperCase().includes(q));
  if(t<0){ flash('Tracker no encontrado'); return; }
  assign(selectedPoint,t,true);
  flash('→ asignado a '+D.tid[t]+' ('+qual[t]+')');
  selectPoint(selectedPoint);
}
function doUnassign(){ if(selectedPoint<0){flash('Selecciona un punto');return;} assign(selectedPoint,-1,true); flash('→ marcado sin asignar'); selectPoint(selectedPoint); }
function undo(){ const h=history.pop(); if(!h){flash('Nada que deshacer');return;} assign(h.i,h.from,false); flash('Deshecho'); if(selectedPoint===h.i) selectPoint(h.i); else render(); }
function resetEdits(){ if(!editedCount()){flash('Sin ediciones');return;} for(let i=0;i<N;i++) if(asg[i]!==origAsg[i]) assign(i,origAsg[i],false); history=[]; flash('Ediciones revertidas'); render(); }
let flashT=null;
function flash(m){ const e=document.getElementById('flash'); e.textContent=m; e.style.opacity=1; clearTimeout(flashT); flashT=setTimeout(()=>e.style.opacity=0,2200); }

/* ---- export ---- */
function num(v){ return (Math.round(v*1000)/1000).toString().replace('.',','); }
function exportCSV(){
  const H=['ID_punto','X_punto','Y_punto','Z_punto','Tracker','NCU_ACCIONA','PS','NCU','GW','TCU','Fila_bifila','Mesa','Esquina','Asignado'];
  const lines=[H.join(';')];
  const order=Array.from({length:N},(_,i)=>i).sort((a,b)=>D.pid[a]-D.pid[b]);
  for(const i of order){
    const a=asg[i]>=0, t=asg[i];
    const fila=cor[i]>=0?((cor[i]===0||cor[i]===2)?'Este':'Oeste'):'';
    const row=[
      D.pid[i], num(D.px[i]), num(D.py[i]), num(D.pz[i]),
      a?D.tid[t]:'', a?D.tncuacc[t]:'', a?D.tps[t]:'', a?D.tncu[t]:'', a?D.tgw[t]:'', a?D.ttcu[t]:'',
      fila, mes[i]>=0?mes[i]:'', cor[i]>=0?CL[cor[i]]:'', a?'Si':'No'
    ];
    lines.push(row.join(';'));
  }
  const blob=new Blob(['\ufeff'+lines.join('\r\n')],{type:'text/csv;charset=utf-8;'});
  const url=URL.createObjectURL(blob); const aEl=document.createElement('a');
  aEl.href=url; aEl.download='asignacion_editada.csv'; aEl.click(); URL.revokeObjectURL(url);
  flash('CSV exportado ('+editedCount()+' ediciones)');
}

/* ---- controls ---- */
function initControls(){
  const sel=document.getElementById('ncuSel');
  let html='<option value="all">Todas las NCU</option>';
  D.ncus.forEach(n=>{html+='<option value="'+n+'">NCU '+n+'</option>';});
  sel.innerHTML=html;
  sel.onchange=()=>{ui.ncu=sel.value;trkHighlight=-1;pendingRange=bboxForNCU(ui.ncu==='all'?null:parseInt(ui.ncu));uirev++;render();};

  const ss=document.getElementById('statusSel');
  ss.onchange=()=>{ui.status=ss.value;render();};

  document.querySelectorAll('input[name=mode]').forEach(r=>{r.onchange=()=>{if(r.checked){ui.mode=r.value;render();updateLegend();}};});
  document.getElementById('chkMotors').onchange=e=>{ui.motors=e.target.checked;render();};
  document.getElementById('chkUnassigned').onchange=e=>{ui.unassigned=e.target.checked;render();};
  document.getElementById('resetBtn').onclick=()=>{ui.ncu='all';sel.value='all';trkHighlight=-1;pendingRange=bboxForNCU(null);uirev++;render();};

  const go=()=>{
    const q=document.getElementById('search').value.trim().toUpperCase(); if(!q)return;
    let idx=D.tid.findIndex(t=>t.toUpperCase()===q); if(idx<0) idx=D.tid.findIndex(t=>t.toUpperCase().includes(q));
    const msg=document.getElementById('searchMsg');
    if(idx<0){msg.textContent='No encontrado';msg.style.color='#e0508a';return;}
    msg.textContent='→ '+D.tid[idx]+' (NCU '+D.tncu[idx]+', '+qual[idx]+')';msg.style.color='#8b919c';
    trkHighlight=idx; pendingRange=[[D.tx[idx]-70,D.tx[idx]+70],[D.ty[idx]-70,D.ty[idx]+70]];uirev++;render();
  };
  document.getElementById('goBtn').onclick=go;
  document.getElementById('search').onkeydown=e=>{if(e.key==='Enter')go();};

  document.getElementById('assignBtn').onclick=doAssign;
  document.getElementById('unassignBtn').onclick=doUnassign;
  document.getElementById('undoBtn').onclick=undo;
  document.getElementById('resetEditsBtn').onclick=resetEdits;
  document.getElementById('exportBtn').onclick=exportCSV;
  document.getElementById('targetTrk').onkeydown=e=>{if(e.key==='Enter')doAssign();};
  document.getElementById('clearSelBtn').onclick=clearSelection;

  let leg=''; D.ncus.forEach(n=>{leg+='<span class="sw"><i style="background:'+D.ncu_colors[n]+'"></i>'+n+'</span>';});
  document.getElementById('ncuLegend').innerHTML=leg;

  document.addEventListener('keydown',e=>{ if(e.key==='Escape') clearSelection(); });
  updateLegend();
}
function attachPlotEvents(){
  plotDiv.on('plotly_click',ev=>{
    if(!ev.points||!ev.points.length) return;
    const p=ev.points[0]; const meta=traceMeta[p.curveNumber]; if(!meta) return;
    if(meta.kind==='assigned'||meta.kind==='unassigned'){ selectPoint(meta.idx[p.pointNumber]); }
    else if(meta.kind==='motor'){
      const t=meta.idx[p.pointNumber];
      if(selectedPoint>=0){ assign(selectedPoint,t,true); flash('→ asignado a '+D.tid[t]+' ('+qual[t]+')'); selectPoint(selectedPoint); }
      else { document.getElementById('targetTrk').value=D.tid[t]; flash('Destino fijado: '+D.tid[t]+' · ahora elige un punto'); }
    }
  });
}
function updateLegend(){
  const box=document.getElementById('modeLegend');
  if(ui.mode==='tracker'){
    let s='<div class="lh">Color = tracker (vecinos distintos, 7 colores)</div><div class="swrow">';
    D.palette.forEach(c=>{s+='<span class="sw"><i style="background:'+c+'"></i></span>';}); s+='</div>';
    box.innerHTML=s;
  } else if(ui.mode==='ncu'){ box.innerHTML='<div class="lh">Color = NCU (leyenda abajo)</div>'; }
  else { box.innerHTML='<div class="lh">Color = estado</div><div class="swrow">'+
    '<span class="sw"><i style="background:'+STC.OK+'"></i>OK</span>'+
    '<span class="sw"><i style="background:'+STC.INCOMPLETO+'"></i>Incompl.</span>'+
    '<span class="sw"><i style="background:'+STC.REVISAR+'"></i>Revisar</span>'+
    '<span class="sw"><i style="background:'+STC.SIN_PUNTOS+'"></i>Sin pts</span></div>'; }
}

window.addEventListener('load',()=>{
  initControls();
  pendingRange=bboxForNCU(null); uirev++;
  render();
  attachPlotEvents();
  clearSelection();
});
