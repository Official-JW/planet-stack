import fs from 'fs';
const NM = '/home/box/apps/gltftools/node_modules';
const THREE = await import(NM + '/three/build/three.module.js');
const { GLTFLoader } = await import(NM + '/three/examples/jsm/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import(NM + '/three/examples/jsm/libs/meshopt_decoder.module.js');
await MeshoptDecoder.ready;
const b = fs.readFileSync(process.argv[2]); const l = new GLTFLoader(); l.setMeshoptDecoder(MeshoptDecoder);
const g = await new Promise((res, rej) => l.parse(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength), '', res, rej));
const S=g.scene; S.updateMatrixWorld(true); const out=[]; const v=new THREE.Vector3();
S.getObjectByName('Pad_Base').traverse(o=>{ if(!o.isMesh) return; const p=o.geometry.attributes.position, ix=o.geometry.index; const n=ix?ix.count:p.count;
 for(let i=0;i<n;i+=3){ const T=[]; for(let k=0;k<3;k++){ v.fromBufferAttribute(p, ix?ix.getX(i+k):i+k).applyMatrix4(o.matrixWorld); T.push(v.x,v.y,v.z);} 
  if(Math.min(T[1],T[4],T[7])<1.5 && Math.max(T[0],T[3],T[6])>-14 && Math.min(T[0],T[3],T[6])<10 && Math.max(T[2],T[5],T[8])>-13 && Math.min(T[2],T[5],T[8])<11) out.push(...T);} });
fs.writeFileSync(process.argv[3], Buffer.from(new Float32Array(out).buffer)); console.log('tris', out.length/9);
