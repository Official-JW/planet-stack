// Replica of Coder's bridge_check.cjs visibility test (raycast camera -> sample point; any other visible mesh in between = occluded,
// the part's own faces (dominant bone of face.a) don't count). Offline: Refinery (tiers hidden) + bridge under its root + RC-1 at rest.
import fs from 'fs'; import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
await MeshoptDecoder.ready;
const load=f=>{const b=fs.readFileSync(f); const l=new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder); return new Promise((r,j)=>l.parse(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'',r,j));};
const A='/workspace/planet-stack/art/3d/';
const GLB=process.argv[2]||A+'buildings/refinery/refinery_bridge.glb'; const OUT=process.argv[3]||'vis_out.json';
const NS=+(process.env.NS||121);
const [CX,CY,CZ,FW]=(process.env.CAM||'318.9,2.08,13.55,38.25').split(',').map(Number);
const ref=await load(A+'buildings/refinery/refinery_game.glb'), br=await load(GLB), cr=await load(A+'props/crane_refinery/crane_refinery_game.glb');
const RS=ref.scene; RS.position.set(320,0,0); RS.traverse(n=>{ if(/^Tier_/.test(n.name)||n.userData.hidden_by_default) n.visible=false; }); RS.add(br.scene); cr.scene.position.set(311,0,17.5);
const scene=new THREE.Scene(); scene.add(RS); scene.add(cr.scene); scene.updateMatrixWorld(true);
const BR=br.scene; const under=(m,R)=>{ for(let q=m;q;q=q.parent) if(q===R) return true; return false; };
const visq=m=>{ for(let q=m;q;q=q.parent) if(!q.visible) return false; return true; };
const cams=[[393,852],[375,667]].map(([W,H])=>{ const c=new THREE.PerspectiveCamera(38,W/H,0.5,3000); const d=(FW/2)/(Math.tan(THREE.MathUtils.degToRad(19))*c.aspect), e=THREE.MathUtils.degToRad(18); c.position.set(CX,CY+d*Math.sin(e),CZ+d*Math.cos(e)); c.lookAt(CX,CY,CZ); c.updateMatrixWorld(); c.updateProjectionMatrix(); return {W,H,c}; });
const staticOcc=[]; scene.traverse(m=>{ if(m.isMesh&&!m.isInstancedMesh&&visq(m)&&!under(m,BR)) staticOcc.push(m); });
const bm=[]; BR.traverse(m=>{ if(m.isMesh&&visq(m)) bm.push(m); });
const clip=br.animations.find(a=>a.name==='box_path'); const mx=new THREE.AnimationMixer(BR); mx.clipAction(clip).play();
let car=null, box1=null; BR.traverse(n=>{ if(n.name==='Lift_Carriage') car=n; if(n.name==='Box_1') box1=n; });
const dom=(m,i)=>{ if(!m.isSkinnedMesh) return null; const si=m.geometry.attributes.skinIndex, sw=m.geometry.attributes.skinWeight; let b=-1,bw=-1; for(let j=0;j<4;j++){ const w=sw.getComponent(i,j); if(w>bw){bw=w;b=si.getComponent(i,j);} } return m.skeleton.bones[b]; };
const v=new THREE.Vector3();
// per sample: world tris of bridge meshes with owner bone (dom of face.a) + mesh name
function soup(){ const T=[]; for(const m of bm){ const P=m.geometry.attributes.position, I=m.geometry.index, n=I?I.count:P.count; const W=new Array(P.count);
    for(let i=0;i<P.count;i++){ m.getVertexPosition(i,v); W[i]=v.clone().applyMatrix4(m.matrixWorld); }
    for(let k=0;k<n;k+=3){ const a=I?I.getX(k):k,b=I?I.getX(k+1):k+1,c=I?I.getX(k+2):k+2; T.push({a:W[a],b:W[b],c:W[c],own:dom(m,a),name:m.name}); } } return T; }
const e1=new THREE.Vector3(),e2=new THREE.Vector3(),pv=new THREE.Vector3(),tv=new THREE.Vector3(),qv=new THREE.Vector3();
function hitT(o,d,t){ e1.subVectors(t.b,t.a); e2.subVectors(t.c,t.a); pv.crossVectors(d,e2); const det=e1.dot(pv); if(Math.abs(det)<1e-12) return -1; const inv=1/det; tv.subVectors(o,t.a); const u=tv.dot(pv)*inv; if(u<0||u>1) return -1; qv.crossVectors(tv,e1); const w=d.dot(qv)*inv; if(w<0||u+w>1) return -1; return e2.dot(qv)*inv; }
const ray=new THREE.Raycaster();
function frac(pts,self,T,C){ let seen=0; const bad={}; const camP=C.c.position;
  for(const pt of pts){ const d0=pt.clone().sub(camP), dd=d0.length(); const d=d0.normalize(); const far=dd-.03; let hit=null;
    for(const t of T){ if(t.own===self) continue; const s=hitT(camP,d,t); if(s>0&&s<far){ hit=t; break; } }
    if(!hit&&process.env.STATIC){ ray.set(camP,d); ray.far=far; const h=ray.intersectObjects(staticOcc,false); if(h.length) hit={name:h[0].object.name,own:null,static:true}; }
    const q=pt.clone().project(C.c), sx=(q.x+1)/2*C.W, sy=(1-q.y)/2*C.H, on=sx>=0&&sx<=C.W&&sy>=0&&sy<=C.H&&q.z<1;
    if(!hit&&on) seen++; else { const key=hit?(hit.static?'REF:'+hit.name:(hit.name+'/'+(hit.own?hit.own.name:'-')+'@'+[hit.a.x+hit.b.x+hit.c.x,hit.a.y+hit.b.y+hit.c.y,hit.a.z+hit.b.z+hit.c.z].map(x=>(x/3-(x===0?0:0)).toFixed(1)).join(','))):'offscreen'; bad[key]=(bad[key]||0)+1; } }
  return {f:pts.length?seen/pts.length:1,n:pts.length,bad}; }
const rows=[];
for(let k=0;k<NS;k++){ const tau=.2+(33.85-.2)*k/(NS-1); mx.setTime(tau); scene.updateMatrixWorld(true); bm.forEach(m=>m.isSkinnedMesh&&m.skeleton.update());
  const T=soup();
  const cpts=[]; for(const m of bm){ if(!m.isSkinnedMesh) continue; const pa=m.geometry.attributes.position; for(let i=0;i<pa.count;i++) if(dom(m,i)===car&&i%3===0){ m.getVertexPosition(i,v); cpts.push(v.clone().applyMatrix4(m.matrixWorld)); } }
  const inv=new THREE.Matrix4().copy(box1.matrixWorld).invert(), lb=new THREE.Box3();
  for(const m of bm){ if(!m.isSkinnedMesh) continue; const pa=m.geometry.attributes.position; for(let i=0;i<pa.count;i++) if(dom(m,i)===box1){ m.getVertexPosition(i,v); lb.expandByPoint(v.clone().applyMatrix4(m.matrixWorld).applyMatrix4(inv)); } }
  const c=lb.getCenter(new THREE.Vector3()), h=lb.getSize(new THREE.Vector3()).multiplyScalar(.49), bp=[];
  for(const x of [-1,0,1]) for(const y of [-1,0,1]) for(const z of [-1,0,1]){ if(!x&&!y&&!z) continue; bp.push(new THREE.Vector3(c.x+x*h.x,c.y+y*h.y,c.z+z*h.z).applyMatrix4(box1.matrixWorld)); }
  const bw=box1.getWorldPosition(new THREE.Vector3()), cw=car.getWorldPosition(new THREE.Vector3());
  const row={tau:+tau.toFixed(3),carY:+cw.y.toFixed(3),boxY:+bw.y.toFixed(3),dy:+(bw.y-cw.y).toFixed(3),dxz:+Math.hypot(bw.x-cw.x,bw.z-cw.z).toFixed(3),carN:cpts.length};
  for(const C of cams){ const a=frac(cpts,car,T,C), b=frac(bp,box1,T,C); row['car'+C.W]=+a.f.toFixed(4); row['carBad'+C.W]=a.bad; row['box'+C.W]=+b.f.toFixed(4); row['boxBad'+C.W]=b.bad; }
  rows.push(row); }
const refR=rows.reduce((a,r)=>Math.abs(r.tau-22.5)<Math.abs(a.tau-22.5)?r:a); const onCar=rows.filter(r=>Math.abs(r.dy-refR.dy)<.05&&r.dxz<2);
const S={glb:GLB,md5:null,samples:rows.length,onCarN:onCar.length,onCarTau:[onCar[0]?.tau,onCar.at(-1)?.tau]};
for(const W of [393,375]){ const wc=rows.reduce((a,r)=>r['car'+W]<a['car'+W]?r:a); const wb=onCar.reduce((a,r)=>r['box'+W]<a['box'+W]?r:a);
  S['car'+W]={min:wc['car'+W],tau:wc.tau,carY:wc.carY,by:wc['carBad'+W]}; S['box'+W]={min:wb['box'+W],tau:wb.tau,y:wb.boxY,by:wb['boxBad'+W],below1:onCar.filter(r=>r['box'+W]<1).length}; }
fs.writeFileSync(OUT,JSON.stringify({summary:S,rows},null,1));
console.log(JSON.stringify(S,null,1));
