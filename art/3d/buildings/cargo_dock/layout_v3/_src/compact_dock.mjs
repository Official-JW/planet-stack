// Layout v3 (cargo_dock_compact_v3.glb). Make a compact copy of dock 882c: farm (x>15.8) moved behind the hall, mast moved to back-left,
// L-pipe horizontal leg shortened to x<=17.2. Usage: node compact_dock.mjs IN.glb OUT.glb
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
const [,, IN, OUT] = process.argv;
export const CAM = [9.5, 1.5, 16.6, 48]; // dock-local ct + frame_w (world ct 369.5, 1.5, 8.6 with the dock at 360, 0, -8)
export const FARM = [-20, 0, -42], MAST = [10, 0, -14], CUT = 15.8, CLIPX = 17.2;
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(IN); const root = doc.getRoot();
const mul = (m, v) => [m[0]*v[0]+m[4]*v[1]+m[8]*v[2]+m[12], m[1]*v[0]+m[5]*v[1]+m[9]*v[2]+m[13], m[2]*v[0]+m[6]*v[1]+m[10]*v[2]+m[14]];
function inv(m){ // affine inverse (scale+rot+trans, general 3x3)
  const a=m[0],b=m[4],c=m[8],d=m[1],e=m[5],f=m[9],g=m[2],h=m[6],i=m[10];
  const A=e*i-f*h,B=-(d*i-f*g),C=d*h-e*g,det=a*A+b*B+c*C;
  const r=[A,-(b*i-c*h),b*f-c*e,B,a*i-c*g,-(a*f-c*d),C,-(a*h-b*g),a*e-b*d].map(x=>x/det); // row-major inverse
  const R=[r[0],r[3],r[6],0,r[1],r[4],r[7],0,r[2],r[5],r[8],0,0,0,0,1];
  const t=mul(R,[m[12],m[13],m[14]]); R[12]=-t[0];R[13]=-t[1];R[14]=-t[2]; return R; }
const isTier = n => { for (let p = n; p; p = p.getParentNode()) if (/^Tier_/.test(p.getName())) return p.getName(); return null; };
const log = { moved_farm:0, moved_mast:0, clipped:0, islands:0 };
for (const node of root.listNodes()) {
  const mesh = node.getMesh(); if (!mesh) continue;
  if (isTier(node)) continue;
  const M = node.getWorldMatrix(), Mi = inv(M);
  for (const prim of mesh.listPrimitives()) {
    const pos = prim.getAttribute('POSITION'); const n = pos.getCount(); const idx = prim.getIndices();
    const P = []; const t=[0,0,0]; for (let k=0;k<n;k++){ pos.getElement(k,t); P.push(mul(M,t)); }
    const par = Int32Array.from({length:n},(_,k)=>k); const f = k=>{ while(par[k]!==k){par[k]=par[par[k]];k=par[k];} return k; };
    const I = idx ? idx.getArray() : Uint32Array.from({length:n},(_,k)=>k);
    for (let k=0;k<I.length;k+=3){ const a=f(I[k]),b=f(I[k+1]),c=f(I[k+2]); par[b]=a; par[f(c)]=a; }
    const bb = new Map();
    for (let k=0;k<n;k++){ const r=f(k); let q=bb.get(r); if(!q){q=[1e9,1e9,1e9,-1e9,-1e9,-1e9];bb.set(r,q);} for(let j=0;j<3;j++){q[j]=Math.min(q[j],P[k][j]);q[j+3]=Math.max(q[j+3],P[k][j]);} }
    log.islands += bb.size;
    const mode = new Map();
    for (const [r,q] of bb){ const cx=(q[0]+q[3])/2;
      if (q[0] < CLIPX && q[3] > CLIPX + 0.5 && q[0] < CUT) mode.set(r,'clip');      // L-pipe leg & anything straddling from the hall side
      else if (cx > CUT) mode.set(r,'farm');
      else if (q[3] < -20) mode.set(r,'mast'); else mode.set(r,'keep'); }
    const cnt = {}; for (const v of mode.values()) cnt[v]=(cnt[v]||0)+1;
    console.log(node.getName(), mesh.getName(), 'verts', n, JSON.stringify(cnt),
      [...bb].filter(([r])=>mode.get(r)==='clip').map(([,q])=>q.map(x=>x.toFixed(1)).join(',')).join(' | '));
    const out = new Float32Array(n*3);
    for (let k=0;k<n;k++){ const m=mode.get(f(k)); const p=P[k].slice();
      if (m==='farm') for(let j=0;j<3;j++) p[j]+=FARM[j];
      else if (m==='mast') for(let j=0;j<3;j++) p[j]+=MAST[j];
      else if (m==='clip' && p[0] > CLIPX) p[0]=CLIPX;
      const l = mul(Mi,p); out.set(l,k*3); }
    const acc = doc.createAccessor().setType('VEC3').setArray(out).setBuffer(root.listBuffers()[0]);
    prim.setAttribute('POSITION', acc);
  }
}
// Tier groups that belong to the farm move with it
for (const node of root.listNodes()) {
  const nm = node.getName();
  if (nm==='Tier_05' || nm==='Tier_12') { const t=node.getTranslation(); node.setTranslation([t[0]+FARM[0],t[1],t[2]+FARM[2]]); console.log('moved', nm); }
  if (nm==='Cam_Target') { node.setTranslation(CAM.slice(0, 3)); node.setExtras({ frame_w: CAM[3], note: 'layout v3 Lv1 framing, 38 deg vFOV, 18 deg pitch, ct at screen centre' }); console.log('Cam_Target ->', CAM); }
  if (nm==='Pipe_LaunchPad') { const t=node.getTranslation(); node.setTranslation([t[0]+FARM[0],t[1],t[2]+FARM[2]]); console.log('Pipe_LaunchPad ->', node.getTranslation()); }
}
{ const sc = root.listScenes()[0]; const ex = sc.getExtras(); const gn = JSON.parse(ex.game_nodes);
  const m = gn.markers.Pipe_LaunchPad; gn.markers.Pipe_LaunchPad = [m[0] + FARM[0], m[1] - FARM[2], m[2]];
  gn.markers.Cam_Target = [CAM[0], -CAM[2], CAM[1]]; gn.marker_extras.Cam_Target = { frame_w: CAM[3] };
  sc.setExtras({ ...ex, game_nodes: JSON.stringify(gn), layout_v3: { source: 'dock_tankfarm_game 882c8e27 (8ca81ac)', farm_offset_m: FARM, mast_offset_m: MAST, lpipe_clipped_at_x: CLIPX, tiers_moved_with_farm: ['Tier_05', 'Tier_12'], note: 'Tier_20 spans hall + farm and was NOT moved; re-place before Lv20' } }); }
for (const a of root.listAccessors()) if (!a.listParents().some(p=>p!==root)) a.dispose();
await io.write(OUT, doc);
console.log(JSON.stringify(log));
