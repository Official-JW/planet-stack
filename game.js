'use strict';
// =====================================================================
// Planet Stack — Moon (steps 1–3). Canvas world + flat DOM UI.
// The cargo ship code is parked in legacy/cargo_ship_build.js (hidden this build).
// =====================================================================
const CFG={
 maxLevel:25,milestoneEvery:5,
 earlyLevels:10,earlyIncome:1.25,earlyCost:1.22,lateIncome:1.10,lateCost:1.15, // Lv1-10: +25% income, +22% cost; Lv11+: +10%, +15%
workerBonus:0.25,
 offlineCapSec:4*3600,offlineRate:0.5,
 stockCap:300,delivInterval:8,delivAmount:6,
 nukeBoost:0.30,nukeBoostPerMilestone:0.05,     // Nuclear Power boosts floors below it
 workerCapBase:3,workerCapLQ:2,workerCapPerLQLevel:1,
 tutorialLevel:3,
 rotPerSlot:Math.PI/2,                          // ~90° of Moon per building site
 surfaceScroll:6,                               // px/s
};
const SPEED=Math.max(0.1,+new URLSearchParams(location.search).get('speed')||1);
// ----- buildings & floors (add more here). Costs ~2.5x each. -----
const BUILDINGS=[
 {id:'life',name:'Life Support',floors:[
  {id:'oxy',name:'Oxygen Plant',art:'oxygen',cost:0,base:0.6,up:15,desc:'Splits water into air. Tap to collect.'},
  {id:'water',name:'Water',art:'water',cost:120,req:{floor:'oxy',lvl:3},base:0.5,up:70,stocks:'markets',desc:'Melts ice into water. Stocks the Markets.'},
  {id:'nuke',name:'Nuclear Power',art:'nuclear',cost:300,base:1.2,up:110,boostBelow:true,crew:'engineer',desc:'Powers the floors below it: +30% income (+5% per milestone).'}]},
 {id:'hab',name:'Habitat',needs:{building:'life',floors:3},floors:[
  {id:'living',name:'Living Quarters',art:'living_quarters',cost:750,base:1.5,up:250,workerCap:true,desc:'Bunks for crew. Raises the astronaut cap.'},
  {id:'markets',name:'Markets',art:'markets',cost:1875,base:4,up:600,store:true,startStock:120,desc:'Sells goods. Needs stock from Water.'}]},
 {id:'eng',name:'Engineering',soon:true,floors:[]},
 {id:'yard',name:'Shipyard',soon:true,floors:[]},
];
const F=[];BUILDINGS.forEach((b,bi)=>b.floors.forEach((d,k)=>F.push(Object.assign({b:bi,k},d))));
const IDX={};F.forEach((d,i)=>IDX[d.id]=i);
const $=s=>document.querySelector(s);
// ----- art (sizes from ART_SPEC.md; all exported at 3x) -----
const A='art/moon/';
// Sprites with a .json atlas read frame rects, fps, pivot and logical size from the JSON (never assume a strip).
const SPR={
 sky:{src:'bg/sky.webp'},stars:{src:'bg/stars.webp'},twinkle:{src:'bg/stars_twinkle.webp'},earth:{src:'bg/earth.webp'},
 globe:{src:'bg/globe.webp'},strip:{src:'bg/globe_surface_strip.webp'},shade:{src:'bg/globe_shade.webp'},
 base:{atlas:'world/tower_base'},site:{atlas:'world/site_marker'},
 coin:{atlas:'fx/coin_spin'},sparkle:{atlas:'fx/coin_sparkle'},dust:{atlas:'ship/dust_puff'},
 // ship art is loaded only when the ship is shown again (hidden this build): ship/ship, ship_damaged, ship_flame, smoke_plume, launch_pad, launch_gantry
};
// astronaut role variants: worker (orange), engineer (blue), medic (green) — only roles in use are loaded
[...new Set(['worker',...F.map(d=>d.crew||'worker')])].forEach(r=>{const p=r==='worker'?'astronaut_':`astronaut_${r}_`;['walk','idle','carry'].forEach(a=>SPR[a+'_'+r]={atlas:'astronaut/'+p+a})});
F.forEach(d=>{SPR['f_'+d.id]={floor:d.art,atlas:`floors/floor_${d.art}_anim`};if(d.store)SPR['ns_'+d.id]={src:`floors/floor_${d.art}_needs_stock.png`,w:360,h:120}});
// Art set: 3x when DPR>2 else 2x (art/moon/@3x/, @2x/); falls back to the base pack per file.
const ART_SET=Math.min(3,window.devicePixelRatio||1)>2?'@3x/':'@2x/';
async function getJSON(p){for(const base of [A+ART_SET,A]){try{const r=await fetch(base+p);if(r.ok)return{j:await r.json(),base}}catch(e){}}throw new Error('missing '+p)}
function getImg(paths){return new Promise(res=>{let i=0;const im=new Image();im.onload=()=>res(im);im.onerror=()=>{i++;if(i<paths.length)im.src=paths[i];else res(im)};im.src=paths[0]})}
async function tryJSON(p){try{const r=await fetch(p);if(r.ok)return await r.json()}catch(e){}return null}
const bmp=async im=>{try{return await createImageBitmap(im)}catch(e){return im}};   // decoded off the main thread; never draws blank
function loadArt(){const keys=Object.keys(SPR);let done=0;const tick=()=>{done++;$('#lbar').style.width=(done/keys.length*100)+'%'};
 return Promise.all(keys.map(async k=>{const s=SPR[k];
  if(s.floor){const j=await tryJSON(A+ART_SET+`floors/floor_${s.floor}.json`);
   if(j&&j.layers){const dir=A+ART_SET+'floors/';s.layered=true;s.base=await bmp(await getImg([dir+j.base]));s.pages=await Promise.all(j.layersImages.map(async n=>bmp(await getImg([dir+n]))));
    s.layers=j.layers;s.fps=j.fps;s.n=j.frames;s.w=j.logicalSize.w;s.h=j.logicalSize.h;s.px=j.pivot.x;s.py=j.pivot.y;tick();return}}
  if(s.atlas){const {j,base}=await getJSON(s.atlas+'.json'),m=j.meta,dir=s.atlas.replace(/[^/]+$/,'');
   s.frames=Object.values(j.frames).map(f=>Object.assign({page:f.page||0},f.frame));s.n=s.frames.length;s.fps=m.fps||1;s.w=m.logicalFrame.w;s.h=m.logicalFrame.h;s.px=m.pivot.x;s.py=m.pivot.y;s.loop=m.loop!==false;
   const imgs=m.images||[m.image];s.pages=await Promise.all(imgs.map(async n=>{const p=[base+dir+n];if(base!==A)p.push(A+dir+n);return bmp(await getImg(p))}));s.img=s.pages[0];tick();return}
  s.img=await bmp(await getImg([A+ART_SET+s.src.replace(/\.png$/,'.webp'),A+s.src]));tick()}))}
function drawFloor(key,t){const s=SPR[key];if(!s.layered){spr(ctx,key,fr(key,t),-180,0);return}
 ctx.drawImage(s.base,-180,-120,360,120);const gf=Math.floor(t*s.fps);
 for(const L of s.layers){const f=L.frames[((gf%L.frames.length)+L.frames.length)%L.frames.length];ctx.drawImage(s.pages[f.page||0],f.x,f.y,f.w,f.h,-180+L.x,-120+L.y,L.w,L.h)}}
// draw a frame (logical units) with its pivot at (x,y)
function spr(ctx,s,frame,x,y,sx=1,sy=1){const S=SPR[s];if(!S.frames){ctx.drawImage(S.img,x-(S.px||0)*sx,y-(S.py||0)*sy,S.w*sx,S.h*sy);return}
 const f=S.frames[Math.max(0,frame|0)%S.n];ctx.drawImage(S.pages[f.page],f.x,f.y,f.w,f.h,x-S.px*sx,y-S.py*sy,S.w*sx,S.h*sy)}
const frOnce=(s,t)=>Math.floor(t*SPR[s].fps);
const fr=(s,t)=>Math.floor(t*SPR[s].fps)%SPR[s].n;
// ----- save / time (all timing from saved timestamps) -----
const SAVEKEY=location.pathname.includes('/preview/')?'planetstack-preview':'planetstack_moon_v1';
function fresh(){const n=Date.now();return{money:0,gt:n,rt:n,step:0,f:Object.fromEntries(F.map(d=>[d.id,{built:d.cost===0,lvl:1,workers:d.cost===0?1:0,pend:0,stock:d.startStock||0,dt:0}]))}}
function load(){try{const s=JSON.parse(localStorage.getItem(SAVEKEY));if(s&&s.f){const fr0=fresh();for(const k in fr0.f)s.f[k]=Object.assign(fr0.f[k],s.f[k]);return s}}catch(e){}return fresh()}
let S=load();
const gnow=()=>S.gt+(Date.now()-S.rt)*SPEED;
function save(){S.gt=gnow();S.rt=Date.now();try{localStorage.setItem(SAVEKEY,JSON.stringify(S))}catch(e){}}
const st=i=>S.f[F[i].id];
// ----- economy -----
const ms=l=>Math.floor(l/CFG.milestoneEvery);
const floorsBuilt=bi=>BUILDINGS[bi].floors.filter(d=>S.f[d.id].built).length;
const siteOpen=bi=>{const n=BUILDINGS[bi].needs;if(BUILDINGS[bi].soon)return false;if(!n)return true;return floorsBuilt(BUILDINGS.findIndex(b=>b.id===n.building))>=n.floors};
function workerCap(){const l=S.f.living;return CFG.workerCapBase+(l.built?CFG.workerCapLQ+CFG.workerCapPerLQLevel*(l.lvl-1):0)}
const totalWorkers=()=>F.reduce((a,d)=>a+st(F.indexOf(d)).workers,0);
const floorSlots=f=>Math.min(4,1+ms(f.lvl));
function income(i){const f=st(i),d=F[i];if(!f.built)return 0;
 let x=d.base*lvlGrowth(f.lvl,CFG.earlyIncome,CFG.lateIncome)*Math.pow(2,ms(f.lvl))*(1+CFG.workerBonus*Math.max(0,f.workers-1));
 if(f.workers<1)x*=0.5;
 const bf=BUILDINGS[d.b].floors;bf.forEach((o,k)=>{if(o.boostBelow&&k>d.k&&S.f[o.id].built)x*=1+CFG.nukeBoost+CFG.nukeBoostPerMilestone*ms(S.f[o.id].lvl)});
 return x}
const totalRate=()=>F.reduce((a,d,i)=>a+(d.store&&st(i).stock<=0?0:income(i)),0);
function lvlGrowth(l,e,la){const n=Math.min(l,CFG.earlyLevels)-1,m=Math.max(0,l-CFG.earlyLevels);return Math.pow(e,n)*Math.pow(la,m)}
const upCost=i=>Math.round(F[i].up*lvlGrowth(st(i).lvl,CFG.earlyCost,CFG.lateCost));
const hireCost=i=>Math.round(Math.max(30,F[i].cost*0.4||30)*Math.pow(1.9,Math.max(0,st(i).workers-1)));
function lockReason(i){const d=F[i];const b=BUILDINGS[d.b];
 if(b.soon)return 'Coming soon';
 if(b.needs&&!siteOpen(d.b)){const nb=BUILDINGS.find(x=>x.id===b.needs.building);return `Needs ${b.needs.floors} ${nb.name} floors`}
 if(d.req){const r=d.req,o=F[IDX[r.floor]];if(S.f[r.floor].lvl<r.lvl)return `Needs ${o.name.replace(' Plant','')} level ${r.lvl}`}
 if(S.money<d.cost)return `Need ${fmt(d.cost-S.money)} more`;return null}
function nextFloor(bi){return BUILDINGS[bi].floors.find(d=>!S.f[d.id].built)}
const fmt=n=>{n=Math.floor(n);if(n<1e4)return '$'+n.toLocaleString('en-US');const u=['K','M','B','T'];let k=-1;while(n>=1e3&&k<3){n/=1e3;k++}return '$'+n.toFixed(n<100?1:0)+u[k]};
const fmtR=n=>n<10?'$'+n.toFixed(1):fmt(n);
function step(dt,live,rate=1){let e=0;
 F.forEach((d,i)=>{const f=st(i);if(!f.built)return;
  if(d.store){const run=Math.min(dt,f.stock);f.stock-=run;const g=income(i)*run*rate;f.pend+=g;e+=g}
  else{const g=income(i)*dt*rate;f.pend+=g;e+=g;
   if(d.stocks){const t=S.f[d.stocks];if(t.built){f.dt+=dt*Math.max(1,f.workers);while(f.dt>=CFG.delivInterval){f.dt-=CFG.delivInterval;t.stock=Math.min(CFG.stockCap,t.stock+CFG.delivAmount);if(live)deliverFx(i,IDX[d.stocks])}}}}});return e}
// ----- tutorial goals -----
const GOALS=[
 {d:'Tap the Oxygen Plant to collect',p:()=>S.money>0||S.f.oxy.pend<0?1:0},
 {d:`Upgrade the Oxygen Plant to level ${CFG.tutorialLevel}`,p:()=>Math.min(1,(S.f.oxy.lvl-1)/(CFG.tutorialLevel-1))},
 {d:'Build Water',p:()=>S.f.water.built?1:Math.min(.99,S.money/F[IDX.water].cost)},
 {d:'Build Nuclear Power',p:()=>S.f.nuke.built?1:Math.min(.99,S.money/F[IDX.nuke].cost)},
 {d:'Swipe to the Habitat site and build Living Quarters',p:()=>S.f.living.built?1:Math.min(.99,S.money/F[IDX.living].cost)},
 {d:'Build the Markets',p:()=>S.f.markets.built?1:Math.min(.99,S.money/F[IDX.markets].cost)},
 {d:'Moon base online! Keep upgrading.',p:()=>1,last:true}];
function goalTick(){let g=GOALS[S.step];if(!g.last&&g.p()>=1){S.step++;g=GOALS[S.step];const el=$('#goal');el.classList.add('pop');setTimeout(()=>el.classList.remove('pop'),350);toast('✅ Goal complete!')}
 $('#gd').textContent=g.d;$('#gp').style.width=(g.p()*100)+'%'}
// =====================================================================
// RENDERING
// =====================================================================
const cv=$('#cv'),ctx=cv.getContext('2d',{alpha:false});
const DEV_DPR=Math.min(3,window.devicePixelRatio||1);   // never lowered
let W=390,H=844,DPR=DEV_DPR,SC=1,OY=0,OX=0;
const snap=v=>Math.round(v*DPR*SC)/(DPR*SC);   // align to whole device pixels
function smooth(c){c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high'}
const C={x:195,y:1320},R=760,HOR=560;
function resize(){DPR=DEV_DPR;W=innerWidth;H=innerHeight;cv.width=Math.round(W*DPR);cv.height=Math.round(H*DPR);  // backing store = CSS size × DPR
 SC=Math.max(0.5,Math.round(W/390*DPR*4)/(4*DPR));if(390*SC>W)SC=Math.floor(W/390*DPR*4)/(4*DPR);
 OX=snap((W/SC-390)/2);OY=snap(H/SC-844);smooth(ctx);if(typeof skyC!=='undefined')skyC=null;band.width=0;dbgText()}
const DBG=new URLSearchParams(location.search).has('dbg');
function dbgText(fps){if(!DBG)return;let el=document.getElementById('dbg');if(!el){el=document.createElement('div');el.id='dbg';el.style.cssText='position:fixed;right:6px;top:calc(env(safe-area-inset-top) + 150px);z-index:60;background:rgba(0,0,0,.75);color:#7ff3ff;font:600 11px ui-monospace,Menlo,monospace;padding:6px 8px;border-radius:8px;pointer-events:none;white-space:pre';document.body.appendChild(el)}
 el.textContent=`devicePixelRatio ${window.devicePixelRatio}\nDPR used ${DPR}\ncanvas ${cv.width}×${cv.height} (${(cv.width/innerWidth).toFixed(2)}× CSS)\nCSS ${innerWidth}×${innerHeight}\nSC ${SC}  art ${ART_SET}${fps?`\nfps ${fps}`:''}`}
addEventListener('resize',resize);
// camera
const cam={rot:0,y:0,anim:null};
// strip offscreen (bent surface band)
const band=document.createElement('canvas'),bctx=band.getContext('2d');const BAND_TOP=HOR-6,BAND_H=190;
function drawBand(u0){const s=Math.min(2,DPR)*SC;if(band.width!==(390*s|0)){band.width=390*s|0;band.height=BAND_H*s|0;smooth(bctx)}
 const b=bctx;b.setTransform(1,0,0,1,0,0);b.clearRect(0,0,band.width,band.height);b.setTransform(s,0,0,s,0,-BAND_TOP*s);
 const img=SPR.strip.img,SW=3;
 for(let x=-60;x<=450;x+=SW){const a=Math.asin((x+SW/2-C.x)/R),px=C.x+R*Math.sin(a),py=C.y-R*Math.cos(a);
  let u=((R*a+u0)%1200+1200)%1200;b.save();b.translate(px,py);b.rotate(a);
  const sw=Math.min(SW+0.6,1200-u);b.drawImage(img,u*3,0,sw*3,480,-SW/2-0.3,0,sw,160);
  if(sw<SW+0.6)b.drawImage(img,0,0,(SW+0.6-sw)*3,480,-SW/2-0.3+sw,0,SW+0.6-sw,160);b.restore()}
 // soft fade of the band's lower edge into the globe, clip to circle
 b.globalCompositeOperation='destination-in';const g=b.createRadialGradient(C.x,C.y,R-150,C.x,C.y,R-100);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'#000');
 b.fillStyle=g;b.beginPath();b.arc(C.x,C.y,R,0,Math.PI*2);b.fill();b.globalCompositeOperation='source-over'}
// tower geometry: building k sits at Moon angle k*90°, camera rot shifts it
const FOOT_MID=13.7;    // tower_base: bottom edge middle is 13.7px from top (measured from art) → hugs the arc
function towerAngle(bi){return bi*CFG.rotPerSlot-cam.rot}
function towerFrame(bi){const a=towerAngle(bi);return{a,x:C.x+R*Math.sin(a),y:C.y-R*Math.cos(a)}}
const floorBottom=k=>-FOOT_MID+4-k*120;      // local y of floor k bottom (slab overlaps footing top 0..4)
// effects state
const FX=[];        // {type,t,dur,...}
const floorFx={};   // id -> {build:t0, up:t0, tap:t0}
const crew={};      // id -> [astronauts]
function crewSync(){F.forEach((d,i)=>{const f=st(i),arr=crew[d.id]||(crew[d.id]=[]);
 while(arr.length<Math.min(4,f.workers))arr.push({x:40+Math.random()*280,v:(Math.random()<.5?-1:1)*30,idle:0,t:Math.random()*5});arr.length=Math.min(arr.length,Math.min(4,f.workers))})}
let T=0;
let skyC=null;
function skyLayer(){const w=W*DPR|0,h=H*DPR|0;if(skyC&&skyC.width===w&&skyC.height===h)return skyC;skyC=document.createElement('canvas');skyC.width=w;skyC.height=h;{const c=skyC.getContext('2d');smooth(c);c.drawImage(SPR.sky.img,0,0,w,h)};return skyC}
function render(){ctx.setTransform(DPR,0,0,DPR,0,0);smooth(ctx);
 // sky + stars cached into one layer; twinkle on top (parallax 0.05, tiled only when offset)
 ctx.setTransform(DPR*SC,0,0,DPR*SC,Math.round(OX*DPR*SC),0);
 const yb=OY+cam.y,rx=cam.rot*R;
 const sx=((-rx*0.05)%390+390)%390,syy=OY*0.5+cam.y*0.05;
 ctx.drawImage(skyLayer(),-OX,0,W/SC,H/SC);                       // sky: parallax 0, never tiled (nebula band isn't seamless)
 ctx.save();ctx.translate(0,syy);ctx.drawImage(SPR.stars.img,sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars.img,sx-390,0,390,844);ctx.restore();
 const tw=0.675+0.325*Math.sin(T*Math.PI*2/2.4);
 ctx.save();ctx.translate(0,syy);
 ctx.globalAlpha=tw;ctx.drawImage(SPR.twinkle.img,sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.twinkle.img,sx-390,0,390,844);
 ctx.globalAlpha=1.35-tw;ctx.scale(-1,1);ctx.drawImage(SPR.twinkle.img,-390-sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.twinkle.img,-sx,0,390,844);
 ctx.restore();ctx.globalAlpha=1;
 // earth (0.1) with slow drift
 const ex=40-rx*0.1,eyy=90+OY*0.4+cam.y*0.1+Math.sin(T*Math.PI*2/20)*2;
 ctx.drawImage(SPR.earth.img,ex,eyy,120,120);
 // ground layer
 ctx.save();ctx.translate(0,snap(yb));
 ctx.drawImage(SPR.globe.img,0,0,390,844);                       // base craters below the band
 drawBand(T*CFG.surfaceScroll+rx);ctx.drawImage(band,0,BAND_TOP,390,BAND_H);
 ctx.drawImage(SPR.shade.img,0,0,390,844);
 // buildings
 BUILDINGS.forEach((b,bi)=>{const tf=towerFrame(bi);if(Math.abs(tf.a)>0.75)return;
  ctx.save();if(Math.abs(tf.a)<0.001)ctx.translate(snap(tf.x),snap(tf.y));else{ctx.translate(tf.x,tf.y);ctx.rotate(tf.a)}   // at rest: no rotation, pixel-snapped
  const n=floorsBuilt(bi);
  if(n===0)drawSite(bi);else drawTower(bi,n);
  ctx.restore()});
 // world FX (coins, sparkles, dust, text) in ground space
 drawFX();
 ctx.restore()}
function drawSite(bi){const open=siteOpen(bi),p=1+0.03*Math.max(0,Math.sin(T*Math.PI*2/1.6));
 spr(ctx,'site',fr('site',T),0,-6,p,p);
 const b=BUILDINGS[bi],nf=nextFloor(bi);
 label(0,-112,b.name,'#c9d3e6',14);
 if(b.soon)label(0,-94,'Coming soon','#8794ad',12);
 else if(!open){const n=b.needs;label(0,-94,`🔒 Needs ${n.floors} floors in ${BUILDINGS.find(x=>x.id===n.building).name}`,'#8794ad',12)}
 else{const why=lockReason(IDX[nf.id]);pillBtn(0,-134,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(0,-104,'🔒 '+why,'#ffb04d',12)}}
function drawTower(bi,n){
 spr(ctx,'base',0,0,-FOOT_MID+SPR.base.h);          // footing middle-bottom on the surface
 const fl=BUILDINGS[bi].floors;
 for(let k=0;k<n;k++){const d=fl[k],f=S.f[d.id],yB=floorBottom(k),fx=floorFx[d.id]||{};
  ctx.save();ctx.translate(0,yB);
  // construction: grow up from the slab with overshoot; upgrade: squash & stretch; tap: quick squish
  let sx=1,sy=1;
  if(fx.build!=null){const t=(T-fx.build)/0.65;if(t<1){sy=easeOutBack(Math.min(1,t));sx=1+0.04*Math.sin(t*Math.PI)}}
  if(fx.up!=null){const t=(T-fx.up)/0.4;if(t<1){const w=Math.sin(t*Math.PI)*(1-t);sx*=1+0.05*w;sy*=1-0.06*w}}
  if(fx.tap!=null){const t=(T-fx.tap)/0.16;if(t<1){const w=Math.sin(t*Math.PI);sx*=1-0.015*w;sy*=1-0.03*w}}
  ctx.scale(sx,sy);
  drawFloor('f_'+d.id,T+k*0.3);
  if(d.store){const tgt=f.stock<=0?1:0;fx.ns=(fx.ns||0)+(tgt-(fx.ns||0))*Math.min(1,dtG/0.25*1.6);floorFx[d.id]=fx;
   if(fx.ns>0.01){ctx.globalAlpha=Math.min(1,fx.ns);ctx.drawImage(SPR['ns_'+d.id].img,-180,-120,360,120);ctx.globalAlpha=1}}
  if(fx.up!=null){const t=(T-fx.up)/0.35;if(t<1){ctx.globalAlpha=0.55*(1-t);ctx.fillStyle='#fff';ctx.fillRect(-180,-120,360,120);ctx.globalAlpha=1}}
  // crew at walk line y=104 (relative to floor top)
  (crew[d.id]||[]).forEach(a=>{const y=-120+104;
   ctx.globalAlpha=.25;ctx.fillStyle='#000';ctx.beginPath();ctx.ellipse(a.x-180,y,5,1,0,0,7);ctx.fill();ctx.globalAlpha=1;
   ctx.save();ctx.translate(snap(a.x-180),y);if(a.v<0)ctx.scale(-1,1);{const k=(a.idle>0?'idle_':'walk_')+(d.crew||'worker');spr(ctx,k,fr(k,T+a.t),0,0)};ctx.restore()});
  // floor name + level chip, pending coin bubble
  chip(-170,-112,`${d.name}  Lv ${f.lvl}`);
  if(f.pend>=1){const bob=Math.sin(T*3+k)*2;coinBubble(150,-92+bob,fmt(f.pend))}
  ctx.restore()}
 // next floor slot (ghost + build button) or roof cap
 const nf=fl[n];const yTop=floorBottom(n);
 if(nf){ctx.save();ctx.globalAlpha=.55;ctx.setLineDash([8,6]);ctx.lineWidth=2;ctx.strokeStyle='#8794ad';ctx.strokeRect(-176,yTop-116,352,112);ctx.restore();
  const why=lockReason(IDX[nf.id]);pillBtn(0,yTop-66,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(0,yTop-34,'🔒 '+why,'#ffb04d',13)}
}
function easeOutBack(t){const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)}
const easeOutCubic=t=>1-Math.pow(1-t,3);
function label(x,y,txt,col,size){ctx.font=`700 ${size}px system-ui,-apple-system,sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='rgba(0,0,0,.5)';ctx.fillText(txt,x,y+1);ctx.fillStyle=col;ctx.fillText(txt,x,y)}
function rr(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath()}
function chip(x,y,txt){ctx.font='700 11px system-ui,-apple-system,sans-serif';const w=ctx.measureText(txt).width+12;ctx.fillStyle='rgba(10,14,26,.62)';rr(x,y,w,17,8);ctx.fill();ctx.fillStyle='#e6ecf7';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,x+6,y+9)}
function coinBubble(x,y,txt){ctx.font='800 12px system-ui,-apple-system,sans-serif';const w=ctx.measureText(txt).width+30;ctx.fillStyle='rgba(232,112,26,.95)';rr(x-w/2,y-11,w,22,11);ctx.fill();
 ctx.fillStyle='#ffd08a';ctx.fillRect(x-w/2+8,y+9,w-16,1.5);spr(ctx,'coin',fr('coin',T),x-w/2+12,y,0.8,0.8);ctx.fillStyle='#3a1600';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,x-w/2+22,y+1)}
const BTN=[];   // hit boxes drawn this frame are recomputed in hitTest from same geometry
function pillBtn(x,y,txt,on){const pulse=on?1+0.03*Math.sin(T*5):1;ctx.save();ctx.translate(x,y);ctx.scale(pulse,pulse);
 ctx.font='800 14px system-ui,-apple-system,sans-serif';const w=ctx.measureText(txt).width+32;
 const g=ctx.createLinearGradient(0,-18,0,18);if(on){g.addColorStop(0,'#ffb04d');g.addColorStop(1,'#e8701a')}else{g.addColorStop(0,'#5b667e');g.addColorStop(1,'#3a4258')}
 ctx.fillStyle=on?'#a84c0c':'#23293a';rr(-w/2,-17,w,38,19);ctx.fill();ctx.fillStyle=g;rr(-w/2,-19,w,36,18);ctx.fill();
 ctx.fillStyle=on?'#3a1600':'#c9d3e6';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(txt,0,0);ctx.restore()}
// ----- FX -----
function toGround(bi,lx,ly){const tf=towerFrame(bi),c=Math.cos(tf.a),s=Math.sin(tf.a);return{x:tf.x+lx*c-ly*s,y:tf.y+lx*s+ly*c}}
function coinFx(gx,gy,amt){FX.push({type:'sparkle',x:gx,y:gy,t:T});FX.push({type:'coin',x:gx,y:gy,t:T,amt})}
function burst(gx,gy,n,txt){for(let i=0;i<n;i++)FX.push({type:'sparkle',x:gx+(Math.random()-.5)*300,y:gy+(Math.random()-.5)*90,t:T+Math.random()*.25});if(txt)FX.push({type:'text',x:gx,y:gy,t:T,txt})}
function dustFx(gx,gy){FX.push({type:'dust',x:gx,y:gy,t:T})}
function drawFX(){for(let i=FX.length-1;i>=0;i--){const o=FX[i],t=T-o.t;if(t<0)continue;
 if(o.type==='coin'){if(t>0.6){FX.splice(i,1);continue}
  const y=o.y-40*easeOutCubic(t/0.6);let s=t<0.25?0.6+0.5*easeOutBack(t/0.25):t<0.4?1.1-0.1*((t-0.25)/0.15):1;const a=t<0.4?1:1-(t-0.4)/0.2;
  ctx.globalAlpha=Math.max(0,a);spr(ctx,'coin',fr('coin',t),o.x-14*s,y,s*1.2,s*1.2);
  ctx.font=`900 ${16*s}px system-ui,-apple-system,sans-serif`;ctx.textAlign='left';ctx.textBaseline='middle';ctx.lineWidth=3;ctx.strokeStyle='#5a2a00';ctx.strokeText('+'+fmt(o.amt),o.x,y);ctx.fillStyle='#ffe2b0';ctx.fillText('+'+fmt(o.amt),o.x,y);ctx.globalAlpha=1}
 else if(o.type==='sparkle'){const f=frOnce('sparkle',t);if(f>=SPR.sparkle.n){FX.splice(i,1);continue}spr(ctx,'sparkle',f,o.x,o.y)}
 else if(o.type==='dust'){const f=frOnce('dust',t);if(f>=SPR.dust.n){FX.splice(i,1);continue}spr(ctx,'dust',f,o.x,o.y)}
 else if(o.type==='text'){if(t>1){FX.splice(i,1);continue}const y=o.y-(o.pill?14:50)*easeOutCubic(t),s=t<.2?easeOutBack(t/.2):1;ctx.globalAlpha=t>.7?(1-t)/.3:1;
  ctx.save();ctx.translate(o.x,y);ctx.scale(s,s);ctx.font='900 22px system-ui,-apple-system,sans-serif';
  if(o.pill){const w=ctx.measureText(o.txt).width+28;ctx.fillStyle='rgba(10,14,26,.88)';rr(-w/2,-17,w,34,17);ctx.fill();ctx.strokeStyle='#ffb04d';ctx.lineWidth=2;ctx.stroke()}   // banner sits above the floor on its own backing, never over floor text
ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineWidth=4;ctx.strokeStyle='#5a2a00';ctx.strokeText(o.txt,0,0);ctx.fillStyle='#ffd08a';ctx.fillText(o.txt,0,0);ctx.restore();ctx.globalAlpha=1}
 else if(o.type==='courier'){ // carry astronaut leaving Water
  const d=1.6;if(t>d){FX.splice(i,1);continue}const tf=towerFrame(o.bi);if(Math.abs(tf.a)>0.75)continue;
  ctx.save();ctx.translate(tf.x,tf.y);ctx.rotate(tf.a);const x=-180+o.x0+(350-o.x0)*(t/d);ctx.translate(x,floorBottom(o.k)-16);ctx.globalAlpha=t>d-0.3?(d-t)/0.3:1;spr(ctx,'carry_worker',fr('carry_worker',t),0,0);ctx.restore();ctx.globalAlpha=1}}}
function deliverFx(from){const d=F[from];if(FX.length<60)FX.push({type:'courier',bi:d.b,k:d.k,x0:60+Math.random()*120,t:T})}
// ----- crew AI -----
function crewTick(dt){for(const id in crew)for(const a of crew[id]){if(a.idle>0){a.idle-=dt;continue}
 a.x+=a.v*dt;if(a.x<16||a.x>344){a.v=-a.v;a.x=Math.max(16,Math.min(344,a.x))}if(Math.random()<dt*0.12)a.idle=1+Math.random()*2}}
// =====================================================================
// INPUT: drag sideways rotates the Moon (direction-locked), vertical pans, tap hits
// =====================================================================
const toLogical=(cx,cy)=>({x:cx/SC-OX,y:cy/SC});
let g0=null;
function gStart(e,fromShade){cancelAnimationFrame(cam.anim);cam.anim=null;
 g0={x:e.clientX,y:e.clientY,rot0:cam.rot,y0:cam.y,axis:null,edge:e.clientX<20||e.clientX>W-20,lx:e.clientX,lt:performance.now(),v:0,fromShade}}
cv.addEventListener('pointerdown',e=>gStart(e,false));
$('#shade').addEventListener('pointerdown',e=>gStart(e,true));
addEventListener('pointermove',e=>{if(!g0)return;const dx=e.clientX-g0.x,dy=e.clientY-g0.y;
 if(!g0.axis){if(Math.hypot(dx,dy)<9)return;g0.axis=Math.abs(dx)>Math.abs(dy)&&!g0.edge?'x':'y';
  if(g0.fromShade){closeSheet();if(g0.axis==='y'){g0=null;return}}}      // swipe on an open sheet: close it AND rotate
 if(g0.axis==='x'){const per=CFG.rotPerSlot/(W*0.6);let r=g0.rot0-dx*per;const mx=(BUILDINGS.length-1)*CFG.rotPerSlot;if(r<0)r*=0.35;if(r>mx)r=mx+(r-mx)*0.35;cam.rot=r;
  const n=performance.now();g0.v=(e.clientX-g0.lx)/Math.max(1,n-g0.lt);g0.lx=e.clientX;g0.lt=n}
 else cam.y=Math.max(0,Math.min(maxCamY(),g0.y0+dy/SC))},{passive:true});
addEventListener('pointerup',e=>{if(!g0)return;const g=g0;g0=null;
 if(!g.axis){if(g.fromShade){if(performance.now()-sheetOpenedAt>400)closeSheet()}else tapAt(toLogical(e.clientX,e.clientY));return}
 if(g.axis==='x'){let k=Math.round(cam.rot/CFG.rotPerSlot);const cur=Math.round(g.rot0/CFG.rotPerSlot);if(k===cur&&Math.abs(g.v)>0.2)k=cur+(g.v<0?1:-1);snapTo(k)}});
addEventListener('pointercancel',()=>{if(g0&&g0.axis==='x')snapTo(Math.round(cam.rot/CFG.rotPerSlot));g0=null});
let site=0;
function snapTo(k){k=Math.max(0,Math.min(BUILDINGS.length-1,k));site=k;updateSite();const from=cam.rot,to=k*CFG.rotPerSlot,fy=cam.y,ty=Math.min(cam.y,maxCamY(k)),t0=performance.now(),D=520;
 const a=n=>{const t=Math.min(1,(n-t0)/D),e=easeOutCubic(t);cam.rot=from+(to-from)*e;cam.y=fy+(ty-fy)*e;if(t<1)cam.anim=requestAnimationFrame(a);else cam.anim=null};cam.anim=requestAnimationFrame(a)}
function maxCamY(bi=site){const n=floorsBuilt(bi)+1;const top=HOR-FOOT_MID-n*120-30;return Math.max(0,150-top-OY*0)}
function updateSite(){$('#sname').textContent=BUILDINGS[site].name.toUpperCase();[...$('#dots').children].forEach((d,i)=>d.classList.toggle('on',i===site))}
function tapAt(p){const gp={x:p.x,y:p.y-(OY+cam.y)};
 const bi=site,tf=towerFrame(bi),c=Math.cos(-tf.a),s=Math.sin(-tf.a),dx=gp.x-tf.x,dy=gp.y-tf.y,lx=dx*c-dy*s,ly=dx*s+dy*c;
 const n=floorsBuilt(bi),fl=BUILDINGS[bi].floors;
 if(n===0){const nf=nextFloor(bi);if(siteOpen(bi)&&nf&&Math.abs(lx)<150&&ly>-160&&ly<0)buyFloor(IDX[nf.id]);else if(Math.abs(lx)<90&&ly>-130&&ly<0)toast(BUILDINGS[bi].soon?'🚧 Coming soon':'🔒 '+(BUILDINGS[bi].needs?`Needs ${BUILDINGS[bi].needs.floors} Life Support floors`:''));return}
 if(Math.abs(lx)>182)return;
 for(let k=0;k<=n;k++){const yb=floorBottom(k);if(ly<=yb&&ly>yb-120){
  if(k===n){const nf=fl[n];if(nf)buyFloor(IDX[nf.id]);return}
  tapFloor(IDX[fl[k].id],gp);return}}}
function tapFloor(i,gp){const f=st(i),d=F[i];(floorFx[d.id]=floorFx[d.id]||{}).tap=T;
 if(f.pend>=1){const g=Math.floor(f.pend);S.money+=g;f.pend-=g;coinFx(gp.x,gp.y,g);bumpMoney();if(S.step===0)S.step=0}
 openSheet(i);save()}
function buyFloor(i){const d=F[i],f=st(i);if(f.built)return;const why=lockReason(i);if(why){toast('🔒 '+why);return}
 S.money-=d.cost;f.built=true;f.workers=totalWorkers()<workerCap()?1:0;(floorFx[d.id]=floorFx[d.id]||{}).build=T;crewSync();
 const p=toGround(d.b,0,floorBottom(d.k));dustFx(p.x,p.y+4);const m=toGround(d.b,0,floorBottom(d.k)-60);burst(m.x,m.y,7,'Built!');shake=0.25;
 toast(`🏗 ${d.name} built!`);if(d.k===0)setTimeout(()=>snapTo(d.b),50);save()}
let shake=0;
// =====================================================================
// FLAT UI
// =====================================================================
let sheetI=-1;
let sheetOpenedAt=0;
function openSheet(i){sheetI=i;sheetOpenedAt=performance.now();$('#sheet').dataset.h='';drawSheet();$('#sheet').classList.add('open');$('#shade').classList.add('on')}
function closeSheet(){sheetI=-1;$('#sheet').classList.remove('open');$('#shade').classList.remove('on')}

function drawSheet(){if(sheetI<0)return;const i=sheetI,f=st(i),d=F[i],max=f.lvl>=CFG.maxLevel,cap=workerCap(),tw=totalWorkers();
 const fullFloor=f.workers>=floorSlots(f),fullCap=tw>=cap,uc=upCost(i),hc=hireCost(i);const toMs=CFG.milestoneEvery-f.lvl%CFG.milestoneEvery;
 const html=`<div class="grab"></div><h2>${d.name}</h2><div class="meta">${d.desc}</div>
 <div class="stats"><div class="stat">Level<b>${f.lvl}</b></div><div class="stat">Income<b>${fmtR(income(i))}/s</b></div><div class="stat">Crew<b>${f.workers}/${floorSlots(f)}</b></div>${d.store?`<div class="stat">Stock<b>${Math.ceil(f.stock)}s</b></div>`:''}</div>
 <div style="font-size:11px;color:#9fb0cc">${max?'Max level':`Milestone in ${toMs} level${toMs>1?'s':''}: income ×2 + crew slot`}</div><div class="mbar"><i style="width:${max?100:((f.lvl%5)/5*100)}%"></i></div>
 <div class="row"><button class="btn" id="bUp" ${max||S.money<uc?'disabled':''}>Upgrade · ${max?'MAX':fmt(uc)}<small>${max?'Max level reached':S.money<uc?`Need ${fmt(uc-S.money)} more`:`Lv ${f.lvl} → ${f.lvl+1}`}</small></button>
 <button class="btn" id="bHire" ${fullFloor||fullCap||S.money<hc?'disabled':''}>Hire · ${fmt(hc)}<small>${fullFloor?`Floor full · more room at Lv ${(ms(f.lvl)+1)*5}`:fullCap?`Crew cap ${tw}/${cap} · ${S.f.living.built?'upgrade':'build'} Living Quarters`:S.money<hc?`Need ${fmt(hc-S.money)} more`:'+25% income'}</small></button></div>`;
 const sh=$('#sheet');if(sh.dataset.h===html)return;sh.innerHTML=html;sh.dataset.h=html;
 $('#bUp').onclick=()=>{const c=upCost(i);if(f.lvl>=CFG.maxLevel||S.money<c)return;S.money-=c;f.lvl++;const fx=floorFx[d.id]=floorFx[d.id]||{};fx.up=T;
  const m=toGround(d.b,0,floorBottom(d.k)-60),mile=f.lvl%5===0;{const top=toGround(d.b,0,floorBottom(d.k)-120-18);burst(m.x,m.y,mile?12:5);FX.push({type:'text',x:top.x,y:top.y,t:T,txt:mile?'★ MILESTONE!':'LV '+f.lvl,pill:true})}if(mile){shake=0.2;crewSync()}drawSheet();save()};
 $('#bHire').onclick=()=>{const c=hireCost(i);if(f.workers>=floorSlots(f)||totalWorkers()>=workerCap()||S.money<c)return;S.money-=c;f.workers++;crewSync();
  const m=toGround(d.b,0,floorBottom(d.k)-30);burst(m.x,m.y,3,'+1 crew');drawSheet();save()}}
function bumpMoney(){const m=$('#money');m.classList.add('bump');setTimeout(()=>m.classList.remove('bump'),180)}
let toastT;function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(toastT);toastT=setTimeout(()=>t.classList.remove('on'),2200)}
function hud(){$('#mval').textContent=fmt(S.money);$('#rate').textContent=fmtR(totalRate())+'/s'}
// =====================================================================
// CATCH-UP (from timestamps) & LOOP
// =====================================================================
let lastG;
function catchUp(){const t=gnow(),gap=(t-lastG)/1000;lastG=t;if(gap<=0)return;
 const sec=Math.min(gap,CFG.offlineCapSec*SPEED),rate=gap>30?CFG.offlineRate:1;let e=0,l=sec;while(l>0){const s=Math.min(5,l);e+=step(s,false,rate);l-=s}
 if(gap>30){const real=gap/SPEED,h=Math.floor(real/3600),m=Math.floor(real%3600/60);
  $('#wbtext').textContent=`Away ${h?h+'h ':''}${m}m${real>=CFG.offlineCapSec?' (4h max)':''}. Your crew earned:`;$('#wbamt').textContent=fmt(e);$('#modal').classList.add('on');
  $('#wbok').onclick=()=>{let g=0;for(const k in S.f){g+=S.f[k].pend;S.money+=S.f[k].pend;S.f[k].pend=0}$('#modal').classList.remove('on');bumpMoney();
   const p=toGround(0,0,floorBottom(0)-60);coinFx(p.x,p.y,g);save()}}
 save()}
let perfN=0,perfT=0,lastF=0,acc=0,saveT=0,dtG=0;
function frame(now){const dt=Math.max(0,Math.min(0.1,(now-lastF)/1000||0));lastF=now;T+=dt;dtG=dt;
 if(!document.hidden){const t=gnow(),gd=(t-lastG)/1000;if(gd>2)catchUp();else{lastG=t;if(!$('#modal').classList.contains('on'))step(gd,true)}}
 crewTick(dt);
 if(shake>0){shake-=dt}
 ctx.save();render();ctx.restore();
 if(shake>0){cv.style.transform=`translate(${(Math.random()-.5)*4*shake/0.25}px,${(Math.random()-.5)*4*shake/0.25}px)`}else if(cv.style.transform)cv.style.transform='';
 // adaptive resolution: if a device can't hold ~50fps, step the canvas resolution down
 perfN++;perfT+=dt;if(perfT>=1){dbgText(Math.round(perfN/perfT));perfN=0;perfT=0}   // no resolution fallback: DPR is never lowered
 acc+=dt;saveT+=dt;if(acc>0.2){acc=0;hud();goalTick();drawSheet()}if(saveT>5){saveT=0;save()}
 requestAnimationFrame(frame)}
document.addEventListener('visibilitychange',()=>{if(document.hidden)save();else catchUp()});
addEventListener('pagehide',save);
// boot
resize();BUILDINGS.forEach(()=>$('#dots').appendChild(document.createElement('i')));updateSite();
loadArt().then(()=>{lastG=S.gt;crewSync();catchUp();hud();goalTick();$('#load').style.opacity=0;setTimeout(()=>$('#load').remove(),500);lastF=performance.now();requestAnimationFrame(frame)});
window.PS={_render:()=>render(),_band:u=>drawBand(u),S,F,CFG,cam,save,gnow,snapTo,closeSheet,reset:()=>{localStorage.removeItem(SAVEKEY);location.reload()}};
