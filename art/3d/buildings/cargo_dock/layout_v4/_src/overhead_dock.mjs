// Layout v4 (cargo_dock_overhead_v4.glb): GC-1 becomes an overhead bridge crane on an elevated runway that cantilevers over the
// loaded lane; 20 Lv1 CargoBox slots under the hall-front yard; SC-1 + side apron retired. Input = layout_v3 GLB (9fb1ddbe).
// Usage: node overhead_dock.mjs IN.glb OUT.glb   (gltf-transform + meshoptimizer from /home/box/apps/gltftools/node_modules)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import { writeFileSync } from 'fs';
import { RIG, SLOTS, STOP, PICKS, CLIPS, KT, RUNWAY, COLS, TIER03, clipKeys } from './v4_layout.mjs';
const [,, IN, OUT] = process.argv;
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(IN); const root = doc.getRoot(); const buf = root.listBuffers()[0];
const mul = (m, v) => [m[0]*v[0]+m[4]*v[1]+m[8]*v[2]+m[12], m[1]*v[0]+m[5]*v[1]+m[9]*v[2]+m[13], m[2]*v[0]+m[6]*v[1]+m[10]*v[2]+m[14]];
function inv(m){ const a=m[0],b=m[4],c=m[8],d=m[1],e=m[5],f=m[9],g=m[2],h=m[6],i=m[10];
  const A=e*i-f*h,B=-(d*i-f*g),C=d*h-e*g,det=a*A+b*B+c*C;
  const r=[A,-(b*i-c*h),b*f-c*e,B,a*i-c*g,-(a*f-c*d),C,-(a*h-b*g),a*e-b*d].map(x=>x/det);
  const R=[r[0],r[3],r[6],0,r[1],r[4],r[7],0,r[2],r[5],r[8],0,0,0,0,1]; const t=mul(R,[m[12],m[13],m[14]]); R[12]=-t[0];R[13]=-t[1];R[14]=-t[2]; return R; }
const byName = n => root.listNodes().find(x => x.getName() === n);
const inside = (q, B) => q[0]>=B[0]&&q[1]>=B[1]&&q[2]>=B[2]&&q[3]<=B[3]&&q[4]<=B[4]&&q[5]<=B[5];
// ---- island helper: dock-space positions + island id + bbox per vertex
function islands(node, prim){ const M=node.getWorldMatrix(); const pos=prim.getAttribute('POSITION'); const n=pos.getCount(); const P=[],t=[0,0,0];
  for(let k=0;k<n;k++){pos.getElement(k,t);P.push(mul(M,t));}
  const par=Int32Array.from({length:n},(_,k)=>k); const f=k=>{while(par[k]!==k){par[k]=par[par[k]];k=par[k];}return k;};
  const I=prim.getIndices().getArray(); for(let k=0;k<I.length;k+=3){const a=f(I[k]),b=f(I[k+1]),c=f(I[k+2]);par[b]=a;par[f(c)]=a;}
  const id=new Int32Array(n), bb=new Map(); for(let k=0;k<n;k++){const r=f(k); id[k]=r; let q=bb.get(r); if(!q){q=[1e9,1e9,1e9,-1e9,-1e9,-1e9];bb.set(r,q);} for(let j=0;j<3;j++){q[j]=Math.min(q[j],P[k][j]);q[j+3]=Math.max(q[j+3],P[k][j]);}}
  return { M, P, id, bb, I, n }; }
// ---- generic primitive rebuild: keep verts by predicate, move kept verts (dock space), append new verts
function rebuild(node, prim, keep, move, add){ const isl=islands(node, prim); const Mi=inv(isl.M); const sem=prim.listSemantics();
  const map=new Int32Array(isl.n).fill(-1); let m=0; for(let k=0;k<isl.n;k++) if(keep(isl.bb.get(isl.id[k]))) map[k]=m++;
  const na = add ? add.p.length : 0; const N=m+na; const out={};
  for(const s of sem){ const a=prim.getAttribute(s); const T=a.getArray().constructor; const e=a.getElementSize(); const arr=new (s==='POSITION'?Float32Array:T)(N*e); const t=new Array(e).fill(0);
    for(let k=0;k<isl.n;k++){ if(map[k]<0) continue; if(s==='POSITION'){ let p=isl.P[k]; if(move) p=move(p, isl.bb.get(isl.id[k])); arr.set(mul(Mi,p),map[k]*3); } else { a.getElement(k,t); a.setElement; for(let j=0;j<e;j++) arr[map[k]*e+j]=enc(a,t[j]); } }
    for(let k=0;k<na;k++){ let v; if(s==='POSITION') v=mul(Mi,add.p[k]); else if(s==='NORMAL') v=[...add.n[k],0,0].slice(0,e); else if(s==='COLOR_0') v=add.c[k].length===3?[...add.c[k],1]:add.c[k]; else v=new Array(e).fill(0);
      for(let j=0;j<e;j++) arr[(m+k)*e+j]= s==='POSITION'? v[j] : enc(a,v[j]); }
    out[s]=doc.createAccessor().setType(a.getType()).setArray(arr).setNormalized(s==='POSITION'?false:a.getNormalized()).setBuffer(buf); }
  const idx=[]; for(let k=0;k<isl.I.length;k+=3){ const a=map[isl.I[k]],b=map[isl.I[k+1]],c=map[isl.I[k+2]]; if(a>=0&&b>=0&&c>=0) idx.push(a,b,c); }
  if(add) for(const i of add.i) idx.push(i+m);
  for(const s of sem) prim.setAttribute(s,out[s]); prim.setIndices(doc.createAccessor().setType('SCALAR').setArray(N>65535?Uint32Array.from(idx):Uint16Array.from(idx)).setBuffer(buf));
  return { kept:m, removed:isl.n-m, added:na }; }
function enc(a,x){ if(!a.getNormalized()) return x; const T=a.getArray().constructor; // normalized int encode
  if(T===Int8Array) return Math.round(Math.max(-1,Math.min(1,x))*127); if(T===Uint8Array) return Math.round(Math.max(0,Math.min(1,x))*255);
  if(T===Int16Array) return Math.round(Math.max(-1,Math.min(1,x))*32767); if(T===Uint16Array) return Math.round(Math.max(0,Math.min(1,x))*65535); return x; }
// ---- geometry builders (dock space)
const G = () => ({ p:[], n:[], c:[], i:[], j:[] });
function quad(g,a,b,c,d,nrm,col,jt){ const o=g.p.length; g.p.push(a,b,c,d); for(let k=0;k<4;k++){g.n.push(nrm);g.c.push(col);g.j.push(jt||0);} g.i.push(o,o+1,o+2,o,o+2,o+3); }
function box(g,lo,hi,col,jt){ const [x0,y0,z0]=lo,[x1,y1,z1]=hi;
  quad(g,[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],[x1,y0,z1],[1,0,0],col,jt); quad(g,[x0,y0,z1],[x0,y1,z1],[x0,y1,z0],[x0,y0,z0],[-1,0,0],col,jt);
  quad(g,[x0,y1,z0],[x0,y1,z1],[x1,y1,z1],[x1,y1,z0],[0,1,0],col,jt); quad(g,[x0,y0,z1],[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[0,-1,0],col,jt);
  quad(g,[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],[0,0,1],col,jt); quad(g,[x1,y0,z0],[x0,y0,z0],[x0,y1,z0],[x1,y1,z0],[0,0,-1],col,jt); }
function strut(g,x,w,a,b,h,col){ // box of width w (x) from a=[y,z] to b=[y,z], thickness h in the yz plane
  const dy=b[0]-a[0], dz=b[1]-a[1], L=Math.hypot(dy,dz), uy=dy/L, uz=dz/L, py=-uz*h/2, pz=uy*h/2; const x0=x-w/2,x1=x+w/2;
  const c=[[a[0]-py,a[1]-pz],[a[0]+py,a[1]+pz],[b[0]+py,b[1]+pz],[b[0]-py,b[1]-pz]]; const P=(xx,k)=>[xx,c[k][0],c[k][1]];
  const nU=[0,-uz,uy].map(v=>v), nD=nU.map(v=>-v);
  quad(g,P(x1,0),P(x1,1),P(x1,2),P(x1,3),[1,0,0],col); quad(g,P(x0,3),P(x0,2),P(x0,1),P(x0,0),[-1,0,0],col);
  quad(g,P(x0,1),P(x0,2),P(x1,2),P(x1,1),nU,col); quad(g,P(x0,0),P(x1,0),P(x1,3),P(x0,3),nD,col); }
// ---- palette (sampled from GC-1 v3 vertex colours)
const WHITE=[0.79,0.82,0.85,1], GRAPH=[0.02,0.03,0.04,1], STEEL=[0.39,0.43,0.48,1], CYAN=[0.03,0.77,1,1];
const log = {};
// 1) Base: drop Lv1 generic container stacks + GC-1 ground rails; add runway + columns
const REMOVE = [[2.7,0.1,-0.15,5.3,5.45,12.75],[-5.3,0.1,-0.15,-2.7,5.45,12.75],[6.6,-1,-2.8,7.8,1.3,14.7],[-7.8,-1,-2.8,-6.6,1.3,14.7]];
const paint=G(), cyan=G(), metal=G();
for (const sx of [-1,1]) { const X=sx*RUNWAY.x;
  box(paint,[X-0.3,RUNWAY.y0,RUNWAY.z0],[X+0.3,RUNWAY.y1,RUNWAY.z1],WHITE);                      // runway girder
  box(paint,[X-0.32,RUNWAY.y0-0.06,RUNWAY.z0],[X+0.32,RUNWAY.y0,RUNWAY.z1],GRAPH);                // bottom flange
  box(metal,[X-0.08,RUNWAY.y1,RUNWAY.z0+0.05],[X+0.08,RUNWAY.rail,RUNWAY.z1-0.05],STEEL);        // crane rail
  box(cyan,[X+sx*0.3,RUNWAY.y0+0.26,RUNWAY.z0+0.1],[X+sx*0.31,RUNWAY.y0+0.36,RUNWAY.z1-0.1],CYAN); // outer stripe
  for (const [za,zb] of [[RUNWAY.z0,RUNWAY.z0+0.3],[RUNWAY.z1-0.3,RUNWAY.z1]]) { box(paint,[X-0.4,RUNWAY.y1,za],[X+0.4,RUNWAY.y1+0.5,zb],GRAPH); box(cyan,[X-0.41,RUNWAY.y1+0.2,za-0.005],[X+0.41,RUNWAY.y1+0.3,zb+0.005],CYAN); } // end stops
  for (const z of COLS) { box(paint,[X-0.5,0.12,z-0.5],[X+0.5,0.5,z+0.5],GRAPH);                    // footing
    box(paint,[X-0.3,0.5,z-0.3],[X+0.3,RUNWAY.y0-0.26,z+0.3],WHITE);                                // column
    box(paint,[X-0.4,RUNWAY.y0-0.26,z-0.4],[X+0.4,RUNWAY.y0-0.06,z+0.4],GRAPH);                     // cap
    box(cyan,[X-sx*0.3-sx*0.01,1.6,z-0.06],[X-sx*0.3,7.6,z+0.06],CYAN); }                           // inner stripe
  // knee braces at the cantilever column (hall side + lane side)
  const zc=COLS[COLS.length-1]; strut(paint,X,0.34,[6.4,zc+0.15],[RUNWAY.y0-0.06,zc+2.9],0.34,WHITE); strut(paint,X,0.34,[6.4,zc-0.15],[RUNWAY.y0-0.06,zc-2.9],0.34,WHITE);
  // tie at the hall end + mid column
  strut(paint,X,0.26,[4.0,COLS[0]+0.3],[RUNWAY.y0-0.06,COLS[0]+2.2],0.26,WHITE); }
const baseAdd = { Base_Paint: paint, Base_GlowCyan: cyan, Base_Metal: metal };
for (const node of root.listNodes()) { const pn=node.getParentNode()?.getName()||''; if(!/^Base_/.test(pn) || !node.getMesh()) continue;
  for (const prim of node.getMesh().listPrimitives()) { const add=baseAdd[pn]; log[pn]=rebuild(node,prim,q=>!REMOVE.some(B=>inside(q,B)),null,add); } }
// 2) Tier_03 (Lv3 extra containers) would float: set them on the ground in the freed right area
{ const t3=byName('Tier_03'); const node=t3.listChildren().find(c=>c.getMesh()); const prim=node.getMesh().listPrimitives()[0];
  const isl=islands(node,prim); const groups={}; for(const q of isl.bb.values()){ const key=((q[0]+q[3])/2<0?'L':'R')+((q[2]+q[5])/2<6.31?'b':'f'); const g=groups[key]||(groups[key]=[1e9,1e9,1e9,-1e9,-1e9,-1e9]); for(let j=0;j<3;j++){g[j]=Math.min(g[j],q[j]);g[j+3]=Math.max(g[j+3],q[j+3]);} }
  const off={}; for(const [k,g] of Object.entries(groups)){ const d=TIER03[k]; off[k]=[d[0]-(g[0]+g[3])/2, 0-g[1], d[1]-(g[2]+g[5])/2]; }
  log.Tier_03={groups,off};
  rebuild(node,prim,()=>true,(p,q)=>{ const key=((q[0]+q[3])/2<0?'L':'R')+((q[2]+q[5])/2<6.31?'b':'f'); const o=off[key]; return [p[0]+o[0],p[1]+o[1],p[2]+o[2]]; }); }
// 3) GC-1 rig: reuse the v3 Crane_Gantry bridge + trolley faces, drop legs/spreader/20ft box, add hook block + ropes, skin to 3 joints
const cg=byName('Crane_Gantry'); const cgm=cg.listChildren().find(c=>c.getMesh()); const cprim=cgm.getMesh().listPrimitives()[0]; const mat=cprim.getMaterial();
const rig=G(); const cls={}; { const isl=islands(cgm,cprim); const N=cprim.getAttribute('NORMAL'), C=cprim.getAttribute('COLOR_0'); const t=[0,0,0,0];
  const classify=q=>{ const tiny=q[3]-q[0]<0.1&&q[4]-q[1]<0.1&&q[5]-q[2]<0.1; const cab=!tiny&&q[0]>=4.6&&q[3]<=6.6&&q[1]>=8.1&&q[4]<=10.1&&q[2]>=9.45&&q[5]<=11.45;
    if(q[1]<9.7&&(q[0]>6.0||q[3]<-6.0)) return 'x_leg'; if(cab) return 'bridge';
    if(q[1]<9.5) return 'x_spreader_box_rope';
    const cx=(q[0]+q[3])/2, k=Math.round((cx+6.2)/2.2); if(q[3]-q[0]<=0.13&&Math.abs(cx-(-6.2+2.2*k))<=0.07&&q[1]>=11.0&&q[4]<=11.42&&q[2]>=8.4&&q[5]<=9.6) return 'x_diaphragm';
    if(q[0]>=2.5&&q[3]<=5.5&&q[1]>=10.85) return 'trolley'; return 'bridge'; };
  const ic=new Map(); for(const [r,q] of isl.bb){ const c=classify(q); ic.set(r,c); const s=cls[c]||(cls[c]={n:0,bb:[1e9,1e9,1e9,-1e9,-1e9,-1e9]}); s.n++; for(let j=0;j<3;j++){s.bb[j]=Math.min(s.bb[j],q[j]);s.bb[j+3]=Math.max(s.bb[j+3],q[j+3]);} }
  const map=new Int32Array(isl.n).fill(-1);
  for(let k=0;k<isl.n;k++){ const c=ic.get(isl.id[k]); if(c[0]==='x') continue; map[k]=rig.p.length; const p=isl.P[k].slice(); let jt=0; if(c==='trolley'){ p[0]-=4.0; jt=1; } // trolley rest x = 0
    N.getElement(k,t); const nn=[t[0],t[1],t[2]]; C.getElement(k,t); rig.p.push(p); rig.n.push(nn); rig.c.push([t[0],t[1],t[2],C.getElementSize()>3?t[3]:1]); rig.j.push(jt); }
  for(let k=0;k<isl.I.length;k+=3){ const a=map[isl.I[k]],b=map[isl.I[k+1]],c=map[isl.I[k+2]]; if(a>=0&&b>=0&&c>=0) rig.i.push(a,b,c); } }
log.gc_classes=Object.fromEntries(Object.entries(cls).map(([k,v])=>[k,{islands:v.n,bbox:v.bb.map(x=>+x.toFixed(2))}]));
{ const hy=RIG.hook_rest, z=RIG.bridge_rest; // hook block (joint 2) at rest, Hook_Attach = block bottom
  box(rig,[-0.45,hy+0.35,z-0.3],[0.45,hy+0.8,z+0.3],GRAPH,2); box(rig,[-0.46,hy+0.52,z-0.305],[0.46,hy+0.62,z+0.305],CYAN,2);
  box(rig,[-0.25,hy+0.05,z-0.1],[0.25,hy+0.35,z+0.1],STEEL,2); box(rig,[-0.06,hy,z-0.06],[0.06,hy+0.05,z+0.06],STEEL,2);
  for(const dx of [-0.3,0.3]) for(const dz of [-0.12,0.12]) { // rope: bottom verts on hook (2), top verts on trolley (1)
    const g=G(); box(g,[dx-0.025,hy+0.8,z+dz-0.025],[dx+0.025,RIG.rope_top,z+dz+0.025],STEEL,2); const o=rig.p.length;
    g.p.forEach((p,k)=>{ rig.p.push(p); rig.n.push(g.n[k]); rig.c.push(g.c[k]); rig.j.push(p[1]>hy+1?1:2); }); g.i.forEach(i=>rig.i.push(i+o)); } }
const rigN=root.listNodes().find(n=>n.getName()==='DockTankFarm');
const gcRig=doc.createNode('GC_Rig').setExtras({ crane:'GC-1', cap_t:40, type:'overhead bridge crane on elevated runway', note:'layout v4; joints GC_Bridge (z) > GC_Trolley (x) > GC_Hook (y) > Hook_Attach; CargoBox child of Hook_Attach at (0,-1.5,0)' });
const jB=doc.createNode('GC_Bridge').setTranslation([0,0,RIG.bridge_rest]);
const jT=doc.createNode('GC_Trolley').setTranslation([0,RIG.trolley_y,0]);
const jH=doc.createNode('GC_Hook').setTranslation([0,RIG.hook_rest-RIG.trolley_y,0]);
const jA=doc.createNode('Hook_Attach').setExtras({ child_offset:[0,-1.5,0], note:'CargoBox Hook_Point sits here; parent the box at (0,-1.5,0)' });
gcRig.addChild(jB); jB.addChild(jT); jT.addChild(jH); jH.addChild(jA);
const ibm=new Float32Array([ [0,0,-RIG.bridge_rest], [0,-RIG.trolley_y,-RIG.bridge_rest], [0,-RIG.hook_rest,-RIG.bridge_rest] ].flatMap(t=>[1,0,0,0, 0,1,0,0, 0,0,1,0, t[0],t[1],t[2],1]));
const skin=doc.createSkin('GC_Skin').addJoint(jB).addJoint(jT).addJoint(jH).setSkeleton(gcRig).setInverseBindMatrices(doc.createAccessor().setType('MAT4').setArray(ibm).setBuffer(buf));
{ const n=rig.p.length; const P=new Float32Array(n*3),Nn=new Int8Array(n*3),Cc=new Uint8Array(n*4),J=new Uint8Array(n*4),W=new Uint8Array(n*4);
  for(let k=0;k<n;k++){ P.set(rig.p[k],k*3); const nn=rig.n[k]; for(let j=0;j<3;j++) Nn[k*3+j]=Math.round(nn[j]*127); for(let j=0;j<4;j++) Cc[k*4+j]=Math.round(rig.c[k][j]*255); J[k*4]=rig.j[k]; W[k*4]=255; }
  const pr=doc.createPrimitive().setMaterial(mat)
    .setAttribute('POSITION',doc.createAccessor().setType('VEC3').setArray(P).setBuffer(buf))
    .setAttribute('NORMAL',doc.createAccessor().setType('VEC3').setArray(Nn).setNormalized(true).setBuffer(buf))
    .setAttribute('COLOR_0',doc.createAccessor().setType('VEC4').setArray(Cc).setNormalized(true).setBuffer(buf))
    .setAttribute('JOINTS_0',doc.createAccessor().setType('VEC4').setArray(J).setBuffer(buf))
    .setAttribute('WEIGHTS_0',doc.createAccessor().setType('VEC4').setArray(W).setNormalized(true).setBuffer(buf))
    .setIndices(doc.createAccessor().setType('SCALAR').setArray(n>65535?Uint32Array.from(rig.i):Uint16Array.from(rig.i)).setBuffer(buf));
  const mesh=doc.createMesh('GC_Mesh').addPrimitive(pr); gcRig.addChild(doc.createNode('GC_Mesh').setMesh(mesh).setSkin(skin)); log.gc_mesh={verts:n,tris:rig.i.length/3}; }
// Lv5 second bridge: stub only
gcRig.addChild(doc.createNode('GC_Bridge2_Stub').setTranslation([0,RUNWAY.rail,RIG.bridge_min]).setExtras({ tier:5, cap_t:40, crane:'GC-2', note:'Lv5: second bridge + trolley on the same runway (hall end). Cannot pass GC-1; GC-1 keeps all truck moves. Stub only.' }));
rigN.addChild(gcRig);
// slots + stop markers
const mk=(name,t,ex)=>{ const n=doc.createNode(name).setTranslation(t); if(ex) n.setExtras(ex); rigN.addChild(n); return n; };
mk('Truck_Stop_Dock',STOP.local,{ world:STOP.world, note:'FB-05 origin at the dock stop, heading +X (moved from world 386.5 to 362.4 along the loaded lane z 13)' });
for (const [k,p] of Object.entries(PICKS)) mk('Pick_'+k,p.box_base,{ bed_slot:p.bed_slot, hook_attach:p.hook });
for (const s of SLOTS) mk(s.name,s.box_base,{ tier:s.tier, block:s.block, row:s.row, hook_attach:s.hook, yaw_deg:0 });
// 4) animations: drop crane_gantry_move, bake 80 clips (CUBICSPLINE, zero tangents = smoothstep per segment)
for (const a of root.listAnimations()) if (a.getName()==='crane_gantry_move') a.dispose();
cg.dispose(); cgm.getMesh().dispose(); cgm.dispose();
const tin=doc.createAccessor().setType('SCALAR').setArray(Float32Array.from(KT)).setBuffer(buf);
for (const c of CLIPS) { const K=clipKeys(c); const an=doc.createAnimation(c.name).setExtras({ duration_s:8.0, events:{ pick:1.95, set:5.75 }, from:c.from, to:c.to, easing:'smoothstep per segment (CUBICSPLINE, zero tangents)' });
  for (const [node,ch] of [[jB,0],[jT,1],[jH,2]]) { const out=new Float32Array(KT.length*9);
    K.forEach((k,i)=>{ const v= ch===0?[0,0,k[0]] : ch===1?[k[1],RIG.trolley_y,0] : [0,k[2]-RIG.trolley_y,0]; out.set([0,0,0],i*9); out.set(v,i*9+3); out.set([0,0,0],i*9+6); });
    const s=doc.createAnimationSampler().setInput(tin).setOutput(doc.createAccessor().setType('VEC3').setArray(out).setBuffer(buf)).setInterpolation('CUBICSPLINE');
    an.addSampler(s).addChannel(doc.createAnimationChannel().setTargetNode(node).setTargetPath('translation').setSampler(s)); } }
// 5) markers + scene extras
{ const cs=byName('Container_Stack'); const top=SLOTS.find(s=>s.name==='Slot_15'); cs.setTranslation([top.box_base[0],top.box_base[1]+1.5,top.box_base[2]]);
  const sc=root.listScenes()[0]; const ex=sc.getExtras(); const gn=JSON.parse(ex.game_nodes); delete gn.pivots.Crane_Gantry;
  const B=v=>[v[0],-v[2],v[1]]; gn.pivots.GC_Bridge=B([0,0,RIG.bridge_rest]); gn.markers.Container_Stack=B(cs.getTranslation()); gn.markers.Truck_Stop_Dock=B(STOP.local);
  for (const [k,p] of Object.entries(PICKS)) gn.markers['Pick_'+k]=B(p.box_base); for (const s of SLOTS) gn.markers[s.name]=B(s.box_base);
  sc.setExtras({ ...ex, game_nodes:JSON.stringify(gn), layout_v4:{ source:'cargo_dock_compact_v3.glb 9fb1ddbe (cae8f39)', crane:'GC-1 overhead bridge on elevated runway x +-7.2, z 2.0..22.9 local, rail top 9.75; cantilevers 6.5 m over the loaded lane (>= 8.95 m clear)', removed:['GC-1 legs/bogies/ground rails','GC-1 spreader + 20ft box','Lv1 generic container stacks','crane_gantry_move'], stop_world:STOP.world, slots:20, clips:CLIPS.length, tier03:'moved to ground x 20.5..26.5 z 6.0', lv5:'GC_Bridge2_Stub' } }); }
for (const a of root.listAccessors()) if (!a.listParents().some(p=>p!==root)) a.dispose();
await io.write(OUT, doc);
console.log(JSON.stringify(log,null,0));
