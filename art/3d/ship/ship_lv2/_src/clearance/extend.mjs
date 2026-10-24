// SCRATCH ONLY: extend crew_climb by DH (repeat one periodic climb span per crew) so the Lv1 boarding clip reaches the Lv2 hatch.
import {NodeIO} from '@gltf-transform/core'; import {ALL_EXTENSIONS} from '@gltf-transform/extensions'; import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const [inF,outF,DHs]=process.argv.slice(2); const DH=+DHs, RATE=1.2, DT=DH/RATE;
const doc=await io.read(inF); const an=doc.getRoot().listAnimations().find(a=>a.getName()==='crew_climb');
const chans=an.listChannels(); const crewOf=ch=>(ch.getTargetNode().getName().match(/^C(\d)_/)||[])[1];
const sampleAt=(s,tt)=>{const t=F(s.getInput()),v=F(s.getOutput()),e=s.getOutput().getElementSize();let i=0;while(i<t.length-1&&t[i+1]<tt)i++;
  if(tt<=t[0])return Array.from(v.slice(0,e)); if(tt>=t[t.length-1])return Array.from(v.slice((t.length-1)*e,t.length*e));
  const f=(tt-t[i])/(t[i+1]-t[i]); const a=v.slice(i*e,i*e+e),b=v.slice(i*e+e,i*e+2*e);
  if(e===4){let d=0;for(let k=0;k<4;k++)d+=a[k]*b[k];const sg=d<0?-1:1;const o=[];for(let k=0;k<4;k++)o.push(a[k]*(1-f)+sg*b[k]*f);const L=Math.hypot(...o);return o.map(x=>x/L);}
  return Array.from(a).map((x,k)=>x*(1-f)+b[k]*f);};
// normalized (quantized) accessors: dequantize to floats before any maths (Crew_1 root scale/rotation are int-normalized -> garbage otherwise)
const F=acc=>{const a=acc.getArray(); if(!acc.getNormalized()) return Float32Array.from(a); const m=a instanceof Int8Array?127:a instanceof Uint8Array?255:a instanceof Int16Array?32767:a instanceof Uint16Array?65535:1; return Float32Array.from(a,x=>Math.max(x/m,-1));};
const TA={};
for(const ch of chans){const n=ch.getTargetNode().getName(); if(!/_Root$/.test(n)||ch.getTargetPath()!=='translation')continue;
  const s=ch.getSampler(),t=F(s.getInput()),v=F(s.getOutput()); let ta=null; for(let i=0;i<t.length;i++) if(v[i*3+1]>=6.0){ta=t[i];break;}
  TA[crewOf(ch)]=ta; const y0=sampleAt(s,ta)[1],y1=sampleAt(s,ta+DT)[1]; console.log(n,'t_a',ta.toFixed(3),'rise over',DT,'s =',(y1-y0).toFixed(4)); }
let worst=0;
for(const ch of chans){const k=crewOf(ch); if(!k)continue; const s=ch.getSampler(); if(ch.getTargetPath()==='translation'&&!/_Root$/.test(ch.getTargetNode().getName())) {}
  const a=sampleAt(s,TA[k]),b=sampleAt(s,TA[k]+DT); let d=0; const isRootT=/_Root$/.test(ch.getTargetNode().getName())&&ch.getTargetPath()==='translation';
  for(let q=0;q<a.length;q++){ if(isRootT&&q===1)continue; const dd=a.length===4?Math.min(Math.abs(a[q]-b[q]),Math.abs(a[q]+b[q])):Math.abs(a[q]-b[q]); d=Math.max(d,dd);} worst=Math.max(worst,d);}
console.log('periodicity: max channel diff between t_a and t_a+DT (excl. root y) =',worst.toFixed(5));
const done=new Set();
for(const ch of chans){const k=crewOf(ch); const s=ch.getSampler(); if(done.has(s))continue; done.add(s);
  const ta=k?TA[k]:null; const t=Array.from(F(s.getInput())),v=Array.from(F(s.getOutput())),e=s.getOutput().getElementSize();
  const isRootT=k&&/_Root$/.test(ch.getTargetNode().getName())&&ch.getTargetPath()==='translation';
  const nt=[],nv=[];
  if(ta==null){ // non-crew channel: just hold; extend time
    for(let i=0;i<t.length;i++){nt.push(t[i]);nv.push(...v.slice(i*e,i*e+e));}
  } else { const tb=ta+DT;
    for(let i=0;i<t.length;i++) if(t[i]<tb-1e-4){nt.push(t[i]);nv.push(...v.slice(i*e,i*e+e));}
    nt.push(tb); nv.push(...sampleAt(s,tb));
    const ins=[ta,...t.filter(x=>x>ta+1e-4)];
    for(const x of ins){ if(x===ta) continue; const val=x===ta?sampleAt(s,ta):sampleAt(s,x); if(isRootT)val[1]+=DH; nt.push(x+DT); nv.push(...val);} }
  // last: ensure the clip lasts +DT for everyone
  const last=nt[nt.length-1]; const lastTarget=36.2+DT; if(last<lastTarget-1e-4){nt.push(lastTarget);nv.push(...nv.slice(nv.length-e));}
  // inputs/outputs can be SHARED between samplers (gltfpack): give each sampler its own accessors, else a shared time array is extended once per crew
  const buf=doc.getRoot().listBuffers()[0];
  s.setInput(doc.createAccessor().setType('SCALAR').setArray(new Float32Array(nt)).setBuffer(buf));
  s.setOutput(doc.createAccessor().setType(s.getOutput().getType()).setArray(new Float32Array(nv)).setBuffer(buf)); }
await io.write(outF,doc); console.log('wrote',outF,'climb +',DT,'s');
