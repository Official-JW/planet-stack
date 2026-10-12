'use strict';
// ================= CONFIG (edit numbers here) =================
const CFG={
 maxLevel:25,levelIncome:1.10,levelCost:1.15,milestoneEvery:5,workerBonus:0.25,
 offlineCapSec:4*3600,offlineRate:0.5,          // idle income: 4h cap, earned at 50% while away
 stockCap:300,delivInterval:8,delivAmount:6,
 yearSec:3600,                                   // 1 in-game year = 1 real hour
 risk:[ // 15-minute blocks, in order, repeating each year
  {key:'low', name:'Low',   hit:0.05,bonus:0.00},
  {key:'med', name:'Medium',hit:0.20,bonus:0.15},
  {key:'high',name:'High',  hit:0.45,bonus:0.30},
  {key:'med', name:'Medium',hit:0.20,bonus:0.15}],
 hitCargoLoss:0.60,hitRepairMult:3,
 tripSec:600,                                    // round trip to Earth
 rawUnitValue:40,refinedMult:3,
 loadSecPerUnit:25,                              // Bay level 1, 1 worker
 turnaround:[{k:'refuel',icon:'⛽',sec:30},{k:'recharge',icon:'🔋',sec:30},{k:'inspect',icon:'🔍',sec:30},{k:'repair',icon:'🔧',sec:30}],
 ship:{ // upgrades
  hold:{name:'Cargo hold',base:12,per:4,cost:400,costMult:1.6,max:10,desc:'+4 cargo slots'},
  hull:{name:'Hull',cost:600,costMult:1.7,max:5,per:0.1,desc:'-10 pts cargo loss on a hit'},
  eng:{name:'Engines',cost:800,costMult:1.8,max:5,per:0.08,desc:'-8% trip time'},
  port:{name:'Spaceport',cost:500,costMult:1.6,max:8,per:0.85,desc:'-15% turnaround'}},
 supplies:{partsShare:0.1,foodStock:120,workers:1},
};
const SPEED=Math.max(0.1,+new URLSearchParams(location.search).get('speed')||1);
// ================= DATA (buildings / floors) =================
// role: income | store (needs stock) | bay (loads cargo) | refinery (refines cargo)
const BUILDINGS=[
 {id:'life',name:'Life Support',color:'#8fd3ff',top:{kind:'pent',name:'Control Room Lounge'},floors:[
  {id:'oxy',name:'Oxygen',cost:0,base:0.6,up:10,color:[150,200,215],desc:'Makes air for the base.'},
  {id:'water',name:'Water',cost:150,base:1.2,up:80,stocks:'markets',color:[120,170,230],desc:'Makes water and food. Stocks the Markets.'},
  {id:'nuke',name:'Nuclear Power',cost:2500,base:5,up:1200,bonus:0.05,color:[170,220,130],desc:'Powers it all. Each milestone: +5% income on every floor.'}]},
 {id:'hab',name:'Habitat',color:'#7fe0b0',top:{kind:'pad',name:'Spaceport'},floors:[
  {id:'living',name:'Living Quarters',cost:100,base:1,up:60,color:[200,190,170],desc:'Rent from crew.'},
  {id:'hospital',name:'Hospital',cost:1200,base:4,up:600,color:[235,215,225],desc:'Keeps the crew healthy.'},
  {id:'markets',name:'Markets',role:'store',cost:400,base:3,up:200,startStock:120,color:[230,180,140],desc:'Sells goods. Needs stock from Water.'}]},
 {id:'eng',name:'Engineering',color:'#ffb066',top:{kind:'pent',name:'The Club'},floors:[
  {id:'cnc',name:'CNC Machining',cost:300,base:2,up:150,color:[180,185,200],desc:'Cuts metal parts.'},
  {id:'cad',name:'CAD Design',cost:800,base:3.5,up:400,color:[160,190,230],desc:'Designs parts.'},
  {id:'cam',name:'CAM Programming',cost:1800,base:6,up:900,color:[170,170,230],desc:'Programs the machines.'},
  {id:'print',name:'3D Printing',cost:4000,base:10,up:2000,color:[230,170,200],desc:'Prints parts.'},
  {id:'chem',name:'Chemistry Lab',cost:9000,base:18,up:4500,color:[170,230,190],desc:'Mixes fuels.'},
  {id:'prop',name:'Propulsion Lab',cost:20000,base:32,up:10000,color:[240,190,130],desc:'Builds engines.'}]},
 {id:'yard',name:'Shipyard',color:'#c8d2e0',top:{kind:'tower',name:'Launch Tower',note:'Unlocks Mars'},floors:[
  {id:'bay',name:'Welding & Assembly Bay',role:'bay',rows:2,cost:0,base:0,up:120,color:[150,160,180],desc:'Packs Helium-3 and platinum. Upgrades and workers load the ship faster.'},
  {id:'refinery',name:'Refinery',role:'refinery',cost:500,base:0,up:300,color:[190,170,220],desc:'Refines cargo: worth 3× raw. Upgrades raise cargo value 10%/level.'}]},
];
const SLOTS=9,SAVEKEY='planetstack_v3';
const F=[];BUILDINGS.forEach((b,bi)=>b.floors.forEach((d,k)=>F.push(Object.assign({b:bi,k,role:'income',rows:1},d))));
const IDX={};F.forEach((d,i)=>IDX[d.id]=i);
const $=s=>document.querySelector(s);
// ================= SAVE / TIME =================
// game time = saved game timestamp + real time since save * SPEED. Everything is timed from saved timestamps.
function fresh(){const now=Date.now();return{money:0,gt:now,rt:now,tut:0,
 f:Object.fromEntries(F.map(d=>[d.id,{built:d.cost===0,lvl:1,workers:1,pend:0,stock:d.startStock||0,dt:0}])),
 ship:{st:'docked',t:now,hold:0,lvl:{hold:0,hull:0,eng:0,port:0},cargo:null,hit:false,risk:null,turnDur:0}}}
function load(){try{const s=JSON.parse(localStorage.getItem(SAVEKEY));if(s&&s.f&&s.ship){const fr=fresh();for(const k in fr.f)s.f[k]=Object.assign(fr.f[k],s.f[k]);s.ship.lvl=Object.assign(fr.ship.lvl,s.ship.lvl);return s}}catch(e){}return fresh()}
let S=load();
const gnow=()=>S.gt+(Date.now()-S.rt)*SPEED;
function save(){S.gt=gnow();S.rt=Date.now();localStorage.setItem(SAVEKEY,JSON.stringify(S))}
const st=i=>S.f[F[i].id];
// ================= ECONOMY =================
const ms=l=>Math.floor(l/CFG.milestoneEvery),slots=f=>1+ms(f.lvl);
function bonus(){let x=1;F.forEach((d,i)=>{if(d.bonus&&st(i).built)x+=d.bonus*ms(st(i).lvl)});return x}
const lvlMult=f=>Math.pow(CFG.levelIncome,f.lvl-1)*Math.pow(2,ms(f.lvl))*(1+CFG.workerBonus*(f.workers-1));
function income(i){const f=st(i);if(!f.built||!F[i].base)return 0;return F[i].base*lvlMult(f)*bonus()}
const upCost=i=>Math.round(F[i].up*Math.pow(CFG.levelCost,st(i).lvl-1));
const hireCost=i=>Math.round(Math.max(25,F[i].cost||60)*0.6*Math.pow(2,st(i).workers-1));
const fmt=n=>{n=Math.floor(n);if(n<1e4)return '$'+n.toLocaleString('en-US');const u=['K','M','B','T'];let k=-1;while(n>=1e3&&k<3){n/=1e3;k++}return '$'+n.toFixed(n<100?1:0)+u[k]};
const fmtR=n=>n<10?'$'+n.toFixed(1):fmt(n);
const mmss=s=>{s=Math.max(0,Math.ceil(s));return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')};
function nextUnlock(){let b=-1;F.forEach((d,i)=>{if(!st(i).built&&(b<0||d.cost<F[b].cost))b=i});return b}
// ---- ship math ----
const SH=()=>S.ship,L=()=>S.ship.lvl;
const holdCap=()=>CFG.ship.hold.base+CFG.ship.hold.per*L().hold;
const loadRate=()=>{const b=st(IDX.bay),r=st(IDX.refinery);let m=lvlMult(b);if(r.built)m*=1+CFG.workerBonus*(r.workers-1);return m/CFG.loadSecPerUnit};
const unitValue=()=>{const r=st(IDX.refinery);return CFG.rawUnitValue*(r.built?CFG.refinedMult*Math.pow(1.1,r.lvl-1):1)};
const tripSec=()=>CFG.tripSec*Math.pow(1-CFG.ship.eng.per,L().eng);
const hitLoss=()=>Math.max(0.2,CFG.hitCargoLoss-CFG.ship.hull.per*L().hull);
const portMult=()=>Math.pow(CFG.ship.port.per,L().port);
function phases(hit){return CFG.turnaround.map(p=>({...p,sec:p.sec*portMult()*(p.k==='repair'&&hit?CFG.hitRepairMult:1)}))}
function riskAt(t){const blk=CFG.yearSec/CFG.risk.length;const n=Math.floor(t/1000/blk);return{...CFG.risk[n%CFG.risk.length],left:blk-(t/1000-n*blk)}}
function holdNow(t){const s=SH();if(s.st!=='docked')return 0;return Math.min(holdCap(),s.hold+loadRate()*Math.max(0,t-s.t)/1000)}
function rebase(){const s=SH();if(s.st==='docked'){const t=gnow();s.hold=holdNow(t);s.t=t}}
function launch(){const s=SH(),t=gnow(),u=Math.floor(holdNow(t));if(s.st!=='docked'||u<1)return false;
 const r=riskAt(t);s.st='trip';s.t=t;s.cargo={units:u,value:u*unitValue()};s.risk={name:r.name,key:r.key,bonus:r.bonus,hit:r.hit};s.hit=Math.random()<r.hit;s.hold=0;save();return true}
// advance state machine from timestamps; returns events
function advanceShip(t){const s=SH(),ev=[];let guard=0;
 while(guard++<10){
  if(s.st==='trip'&&t>=s.t+tripSec()*1000){const end=s.t+tripSec()*1000;
   let v=s.cargo.value*(1+s.risk.bonus);if(s.hit)v*=1-hitLoss();v=Math.round(v);
   const parts=Math.round(v*CFG.supplies.partsShare);S.money+=v+parts;
   const m=st(IDX.markets);if(m.built)m.stock=Math.min(CFG.stockCap,m.stock+CFG.supplies.foodStock);
   let wk=0;for(let i=0;i<F.length&&wk<CFG.supplies.workers;i++){const f=st(i);if(f.built&&f.workers<slots(f)){f.workers++;wk++}}
   ev.push({type:'landed',at:end,v,parts,wk,hit:s.hit,risk:s.risk});
   s.st='turn';s.t=end;s.turnDur=phases(s.hit).reduce((a,p)=>a+p.sec,0)}
  else if(s.st==='turn'&&t>=s.t+s.turnDur*1000){s.st='docked';s.t=s.t+s.turnDur*1000;s.hold=0;s.hit=false;ev.push({type:'ready'})}
  else break}
 return ev}
// ---- floors sim (game-seconds) ----
function step(dt,live,rate=1){let e=0;
 F.forEach((d,i)=>{const f=st(i);if(!f.built)return;
  if(d.role==='store'){const run=Math.min(dt,f.stock);f.stock-=run;const g=income(i)*run*rate;f.pend+=g;e+=g}
  else{const g=income(i)*dt*rate;f.pend+=g;e+=g;
   if(d.stocks){const ti=IDX[d.stocks],t=st(ti);if(t.built){f.dt+=dt*f.workers;while(f.dt>=CFG.delivInterval){f.dt-=CFG.delivInterval;
    t.stock=Math.min(CFG.stockCap,t.stock+CFG.delivAmount);  // credited immediately: no lost crates on resume
    if(live)carryStock(i,ti)}}}}});return e}
// ================= DOM =================
const world=$('#world'),tabs=$('#tabs'),track=$('#track'),els=[],panels=[];let pad,shipEl;
function floorHTML(){return `<div class="ground"></div><div class="door"></div><div class="machine"></div><div class="lab"></div><div class="sub"></div><div class="pend"></div><div class="stockbar"><i></i></div><div class="needs">📦 Needs stock</div><button class="buildbtn"></button><div class="wk"></div>`}
function topHTML(b){if(b.top.kind==='pad')return `<div class="pad"><div class="plab">🛰 Spaceport</div><div class="holdbar"><i></i></div><div class="holdtxt"></div>
 <div class="pill"></div><button class="btn launch">🚀 Launch</button><div class="transit"></div>
 <div class="ring"><svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" fill="none" stroke="#0006" stroke-width="5"/><circle class="arc" cx="20" cy="20" r="16" fill="none" stroke="#ff9a3c" stroke-width="5" stroke-linecap="round" stroke-dasharray="100.5" stroke-dashoffset="100.5"/></svg><div class="icons">${CFG.turnaround.map(p=>`<span>${p.icon}</span>`).join('')}</div><div class="rt"></div></div>
 <div class="shipwrap"><div class="ship"><div class="fin" style="left:-8px"></div><div class="fin" style="right:-8px"></div><div class="hullp"></div><div class="win"></div><div class="flame"></div></div></div><div class="deck"></div></div>`;
 return `<div class="pent"><div class="glass"></div><div class="room"></div><div class="title">🔒 ${b.top.name}<small>${b.top.note||'Penthouse · coming soon'}</small></div></div>`}
function build(){BUILDINGS.forEach((b,bi)=>{
 const p=document.createElement('div');p.className='bld';p.style.setProperty('--bc',b.color);
 p.innerHTML=`<div class="tower">${topHTML(b)}<div class="fl"></div><div class="bname">${b.name.toUpperCase()}</div></div>`;
 track.appendChild(p);panels.push(p);
 const t=document.createElement('button');t.textContent=b.name;t.onclick=()=>go(bi,true);tabs.appendChild(t);
 const fl=p.querySelector('.fl');let used=b.floors.reduce((a,d)=>a+(d.rows||1),0);
 for(let k=0;k<SLOTS-used;k++){const e=document.createElement('div');e.className='floor slot';e.innerHTML=`<div class="lab">🔒 Floor ${SLOTS-k}</div><div class="sub">Empty slot · coming soon</div>`;fl.appendChild(e)}
 for(let k=b.floors.length-1;k>=0;k--){const d=b.floors[k],i=IDX[d.id];const e=document.createElement('div');e.className='floor';e.innerHTML=floorHTML();
  if(d.rows>1)e.style.height=(120*d.rows)+'px';
  e.querySelector('.door').style[b.id==='yard'?'right':'left']='0';
  e.onclick=ev=>{if(ev.target.classList.contains('buildbtn'))return;tap(i,ev)};
  e.querySelector('.buildbtn').onclick=ev=>{ev.stopPropagation();buy(i)};
  fl.appendChild(e);els[i]=e}});
 pad=$('.pad');shipEl=pad.querySelector('.shipwrap');
 pad.querySelector('.launch').onclick=doLaunch;shipEl.onclick=()=>openShipSheet();
 $('#chip').onclick=()=>{go(1,true);panels[1].scrollTo({top:0,behavior:'smooth'})}}
function tint(i){const c=F[i].color,m=ms(st(i).lvl),k=1-0.12*m,h=m*14;
 return `linear-gradient(rgb(${c[0]*k+h|0},${c[1]*k|0},${c[2]*k+h*.6|0}),rgb(${c[0]*k*.75|0},${c[1]*k*.75|0},${c[2]*k*.8|0}))`}
function sub(i){const d=F[i],f=st(i);if(d.role==='bay')return `Loads ${(loadRate()*60).toFixed(1)} cargo/min · 👷 ${f.workers}/${slots(f)}`;
 if(d.role==='refinery')return `Cargo ${fmt(unitValue())}/unit · 👷 ${f.workers}/${slots(f)}`;return `${fmtR(income(i))}/s · 👷 ${f.workers}/${slots(f)}`}
function render(){const nu=nextUnlock(),t=gnow();
 F.forEach((d,i)=>{const f=st(i),e=els[i],bb=e.querySelector('.buildbtn');
  e.classList.toggle('locked',!f.built);
  ['.lab','.sub','.pend','.machine','.stockbar','.ground','.door'].forEach(s=>e.querySelector(s).style.visibility=f.built?'':'hidden');
  if(!f.built){e.style.background='';e.classList.remove('empty');bb.style.display='';
   bb.textContent=i===nu?`Build ${d.name} · ${fmt(d.cost)}`:`🔒 ${d.name} · ${fmt(d.cost)}`;bb.disabled=i!==nu||S.money<d.cost;return}
  bb.style.display='none';e.style.background=tint(i);
  e.querySelector('.lab').textContent=`${d.name} · Lv ${f.lvl}`;e.querySelector('.sub').textContent=sub(i);
  const pe=e.querySelector('.pend');pe.style.display=d.base?'':'none';pe.textContent=fmt(f.pend);
  const sb=e.querySelector('.stockbar');sb.style.display=d.role==='store'?'':'none';
  if(d.role==='store'){sb.firstChild.style.width=Math.min(100,f.stock/120*100)+'%';e.classList.toggle('empty',f.stock<=0)}
  syncWorkers(i)});
 // spaceport
 const s=SH(),h=holdNow(t),cap=holdCap(),r=riskAt(t);
 pad.querySelector('.holdbar i').style.width=(s.st==='docked'?h/cap*100:0)+'%';
 const docked=s.st==='docked',turn=s.st==='turn',trip=s.st==='trip';
 pad.querySelector('.holdtxt').textContent=docked?`Hold ${Math.floor(h)}/${cap} · ${st(IDX.refinery).built?'refined':'raw'} · ≈${fmt(Math.floor(h)*unitValue()*(1+r.bonus))}`:trip?'Hold: in flight':'Hold: unloading';
 const pill=pad.querySelector('.pill');pill.style.display=docked?'':'none';pill.className='pill '+r.key;
 pill.textContent=`${r.name} risk · ${r.bonus?'+'+Math.round(r.bonus*100)+'% bonus':'no bonus'} · ${mmss(r.left/SPEED)}`;
 const lb=pad.querySelector('.launch');lb.style.display=docked?'':'none';lb.disabled=Math.floor(h)<1||launching;
 lb.textContent=Math.floor(h)>=cap?'🚀 Launch (full)':'🚀 Launch';
 const tr=pad.querySelector('.transit');tr.style.display=trip?'block':'none';
 if(trip){const left=s.t/1000+tripSec()-t/1000;tr.innerHTML=`🚀 To Earth and back: <b>${mmss(left/SPEED)}</b> left<br>${s.cargo.units} units · ${s.risk.name} risk`}
 const ring=pad.querySelector('.ring');ring.style.display=turn?'block':'none';
 if(turn){const el=(t-s.t)/1000,ph=phases(s.hit);let acc=0,cur=ph.length-1;for(let k=0;k<ph.length;k++){if(el<acc+ph[k].sec){cur=k;break}acc+=ph[k].sec}
  ring.querySelector('.arc').style.strokeDashoffset=100.5*(1-Math.min(1,el/s.turnDur));
  [...ring.querySelectorAll('.icons span')].forEach((sp,k)=>{sp.className=k<cur?'done':k===cur?'on':''});
  ring.querySelector('.rt').textContent=`${ph[cur].k[0].toUpperCase()+ph[cur].k.slice(1)}${s.hit&&ph[cur].k==='repair'?' (damage ×3)':''} · ${mmss((s.turnDur-el)/SPEED)}`}
 shipEl.style.visibility=trip&&!launching?'hidden':'visible';
 $('#chip').textContent=docked?`🚀 ${Math.floor(h)}/${cap}`:trip?`🚀 ${mmss((s.t/1000+tripSec()-t/1000)/SPEED)}`:'🔧 Turnaround';
 $('#money').textContent=fmt(S.money);
 $('#tip').style.display=S.tut===0&&!$('#modal').classList.contains('on')?'block':'none'}
// ---- workers walking ----
const W=[];
function syncWorkers(i){const wk=els[i].querySelector('.wk');while(wk.children.length<st(i).workers){const w=document.createElement('div');w.className='worker walk';w.innerHTML='<b></b>';wk.appendChild(w);
 W.push({el:w,x:40+Math.random()*240,v:(Math.random()<.5?-1:1)*(30+Math.random()*25),pause:0})}}
function walk(dt){for(const w of W){if(w.pause>0){w.pause-=dt;if(w.pause<=0)w.el.classList.add('walk')}
 else{w.x+=w.v*dt;if(w.x<30||w.x>300){w.v=-w.v;w.x=Math.max(30,Math.min(300,w.x))}if(Math.random()<dt*.15){w.pause=.6+Math.random();w.el.classList.remove('walk')}}
 w.el.style.transform=`translateX(${w.x}px) scaleX(${w.v<0?-1:1})`}}
// ---- carriers (purely visual) ----
const C=[],ease=x=>x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;
function mk(parent,kind){const c=document.createElement('div');c.className='carry '+(kind||'');c.innerHTML='<b></b><i></i>';parent.appendChild(c);return c}
function mover(parent,kind,a,b,dur,fadeIn,fadeOut,end){if(C.length>40)return;C.push({el:mk(parent,kind),a,b,t:0,dur,fadeIn,fadeOut,end})}
function carryStock(from,to){mover(els[from],'',40+Math.random()*80,10,1.3,false,true,()=>mover(els[to],'',10,150+Math.random()*100,1.2,true,false))}
function moveCarriers(dt){for(let k=C.length-1;k>=0;k--){const o=C[k];o.t+=dt/o.dur;
 if(o.t>=1){o.el.remove();C.splice(k,1);o.end&&o.end();continue}
 const e=ease(o.t);o.el.style.transform=`translateX(${o.a+(o.b-o.a)*e}px)${o.b<o.a?' scaleX(-1)':''}`;
 o.el.style.opacity=o.fadeOut&&o.t>.85?(1-o.t)/.15:o.fadeIn&&o.t<.15?o.t/.15:1}}
let lastUnits=-1;
function loadingVisuals(t){const s=SH();if(s.st!=='docked'){lastUnits=-1;return}const u=Math.floor(holdNow(t));
 if(lastUnits>=0&&u>lastUnits&&u-lastUnits<=2){const kind=u%2?'can':'roll';const src=st(IDX.refinery).built?els[IDX.refinery]:els[IDX.bay];
  mover(src,kind,60+Math.random()*100,350,1.1,false,true);
  mover(pad,kind,10,170,1.6,true,false,()=>{shipEl.classList.remove('lock');void shipEl.offsetWidth;shipEl.classList.add('lock')})}
 lastUnits=u}
function unloadVisuals(){for(let k=0;k<4;k++)setTimeout(()=>mover(pad,'supply',190,-10,1.8,false,true),k*450)}
// ---- ship animations ----
let launching=false;
function doLaunch(){if(launching||!launch())return;launching=true;closeSheet();
 const sq=shipEl.querySelector('.ship').animate([{transform:'scale(1,1)'},{transform:'scale(1.12,.84) translateX(-2px)'},{transform:'scale(1.12,.84) translateX(2px)'},{transform:'scale(1.1,.86) translateX(-2px)'},{transform:'scale(.95,1.08)'}],{duration:400,easing:'ease-in-out'});
 sq.onfinish=()=>{shipEl.classList.add('fire');const up=shipEl.animate([{transform:'translateY(0)'},{transform:'translateY(-1100px)'}],{duration:1500,easing:'cubic-bezier(.55,0,1,.45)',fill:'forwards'});
  up.onfinish=()=>{launching=false;shipEl.classList.remove('fire');up.cancel();render()}};
 toast(`🚀 Launched ${SH().cargo.units} units at ${SH().risk.name} risk`);render()}
function landAnim(){shipEl.style.visibility='visible';shipEl.classList.add('fire');
 const a=shipEl.animate([{transform:'translateY(-1100px)',easing:'cubic-bezier(.15,.7,.3,1)'},{transform:'translateY(0)',offset:.78,easing:'ease-out'},{transform:'translateY(-12px)',offset:.88,easing:'ease-in'},{transform:'translateY(0)'}],{duration:1800});
 setTimeout(()=>shipEl.classList.remove('fire'),1300);a.onfinish=()=>{dust();unloadVisuals()}}
function dust(){const d=document.createElement('div');d.className='dust';pad.appendChild(d);setTimeout(()=>d.remove(),950)}
function landedMsg(e){return `${e.hit?'💥 Hit by debris! Lost '+Math.round(hitLoss()*100)+'% of cargo. ':'✅ Safe trip! '}Earned ${fmt(e.v)} + ${fmt(e.parts)} parts${e.wk?' · +'+e.wk+' worker':''} · food restocked`}
// ---- ui ----
let toastT;function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(toastT);toastT=setTimeout(()=>t.classList.remove('on'),3500)}
function pop(el,x,y,txt){const p=document.createElement('div');p.className='pop';p.textContent=txt;p.style.left=x+'px';p.style.top=y+'px';el.closest('.tower').appendChild(p);setTimeout(()=>p.remove(),650)}
function popAt(i,txt){pop(els[i],180,els[i].offsetTop+60,txt)}
function bumpMoney(){const m=$('#money');m.classList.add('bump');setTimeout(()=>m.classList.remove('bump'),150)}
function tap(i,ev){const f=st(i);if(!f.built)return;
 if(f.pend>=1){const g=Math.floor(f.pend);S.money+=g;f.pend-=g;const r=els[i].closest('.tower').getBoundingClientRect();pop(els[i],(ev.clientX-r.left)/sc,(ev.clientY-r.top)/sc-10,'+'+fmt(g));bumpMoney()}
 S.tut=1;openSheet(i);render();save()}
function buy(i){const d=F[i];if(i!==nextUnlock()||S.money<d.cost)return;rebase();S.money-=d.cost;st(i).built=true;popAt(i,'Built!');render();save()}
let sheet=null;
function openSheet(i){sheet={floor:i};drawSheet(true);$('#sheet').classList.add('open');$('#shade').classList.add('on')}
function openShipSheet(){sheet={ship:1};drawSheet(true);$('#sheet').classList.add('open');$('#shade').classList.add('on')}
function closeSheet(){sheet=null;$('#sheet').classList.remove('open');$('#shade').classList.remove('on')}
$('#shade').onclick=closeSheet;
function drawSheet(){if(!sheet)return;const sh=$('#sheet');let html;
 if(sheet.ship){const lv=L(),rows=Object.entries(CFG.ship).map(([k,u])=>{const c=Math.round(u.cost*Math.pow(u.costMult,lv[k])),mx=lv[k]>=u.max;
   return `<div class="row"><button class="btn" data-up="${k}" ${mx||S.money<c?'disabled':''}>${u.name} Lv ${lv[k]} · ${u.desc}<br>${mx?'MAX':fmt(c)}</button></div>`}).join('');
  html=`<h2>Cargo Ship</h2><p>Hold ${holdCap()} · trip ${mmss(tripSec())} · hit loss ${Math.round(hitLoss()*100)}% · turnaround ${mmss(phases(false).reduce((a,p)=>a+p.sec,0))}</p>${rows}<div class="row"><button class="btn ghost" id="bClose">Close</button></div>`;
  if(sh.dataset.h===html)return;sh.innerHTML=html;sh.dataset.h=html;
  sh.querySelectorAll('[data-up]').forEach(b=>b.onclick=()=>{const k=b.dataset.up,u=CFG.ship[k],c=Math.round(u.cost*Math.pow(u.costMult,lv[k]));if(lv[k]>=u.max||S.money<c)return;
   rebase();S.money-=c;lv[k]++;if(k==='port'&&SH().st==='turn'){/*keep current turnaround*/}render();drawSheet();save()});
  $('#bClose').onclick=closeSheet;return}
 const i=sheet.floor,f=st(i),d=F[i],max=f.lvl>=CFG.maxLevel,full=f.workers>=slots(f);
 html=`<h2>${d.name} · Lv ${f.lvl}</h2><p>${d.desc}<br>${sub(i)}${max?' · MAX LEVEL':`<br>Next milestone in ${5-f.lvl%5} lv (×2, new worker slot)`}${d.role==='store'?`<br>Stock: ${Math.ceil(f.stock)}s`:''}</p>
 <div class="row"><button class="btn" id="bUp" ${max||S.money<upCost(i)?'disabled':''}>⬆ Upgrade<br>${max?'MAX':fmt(upCost(i))}</button>
 <button class="btn" id="bHire" ${full||S.money<hireCost(i)?'disabled':''}>👷 Hire<br>${full?'Slots full':fmt(hireCost(i))}</button></div>
 <div class="row"><button class="btn ghost" id="bClose">Close</button></div>`;
 if(sh.dataset.h===html)return;sh.innerHTML=html;sh.dataset.h=html;
 $('#bUp').onclick=()=>{const c=upCost(i);if(f.lvl>=CFG.maxLevel||S.money<c)return;rebase();S.money-=c;f.lvl++;popAt(i,f.lvl%5===0?'★ Milestone!':'Level '+f.lvl);render();drawSheet();save()};
 $('#bHire').onclick=()=>{const c=hireCost(i);if(f.workers>=slots(f)||S.money<c)return;rebase();S.money-=c;f.workers++;render();drawSheet();save()};
 $('#bClose').onclick=closeSheet}
// ================= SWIPE =================
let cur=0,sc=1,trackX=0,anim=null,suppressClick=0;
function layout(){const vw=world.clientWidth;sc=Math.min(1,(vw-56)/360);document.documentElement.style.setProperty('--s',sc);
 panels.forEach(p=>p.style.setProperty('--h',(p.firstChild.offsetHeight*(1-sc))+'px'));setX(baseX(cur))}
const pitch=()=>384*sc,baseX=i=>(world.clientWidth-360*sc)/2-i*pitch();
function setX(x){trackX=x;track.style.transform=`translate3d(${x}px,0,0)`}
function go(i,smooth){cur=Math.max(0,Math.min(BUILDINGS.length-1,i));[...tabs.children].forEach((t,j)=>t.classList.toggle('on',j===cur));
 const to=baseX(cur);if(!smooth){setX(to);return}const from=trackX,t0=performance.now(),D=380;cancelAnimationFrame(anim);
 (function a(n){const k=Math.min(1,(n-t0)/D),e=1-Math.pow(1-k,3);setX(from+(to-from)*e);if(k<1)anim=requestAnimationFrame(a)})(t0)}
let g0=null;
world.addEventListener('touchstart',e=>{const t=e.touches[0];if(e.touches.length>1){g0=null;return}
 g0={x:t.clientX,y:t.clientY,x0:trackX,axis:null,edge:t.clientX<20||t.clientX>world.clientWidth-20,lx:t.clientX,lt:performance.now(),v:0}},{passive:true});
world.addEventListener('touchmove',e=>{if(!g0)return;const t=e.touches[0],dx=t.clientX-g0.x,dy=t.clientY-g0.y;
 if(!g0.axis){if(Math.hypot(dx,dy)<9)return;g0.axis=Math.abs(dx)>Math.abs(dy)&&!g0.edge?'x':'y';if(g0.axis==='x')cancelAnimationFrame(anim)}
 if(g0.axis==='x'){e.preventDefault();let x=g0.x0+dx;const mn=baseX(BUILDINGS.length-1),mx=baseX(0);if(x>mx)x=mx+(x-mx)*.35;if(x<mn)x=mn+(x-mn)*.35;setX(x);
  const n=performance.now();g0.v=(t.clientX-g0.lx)/Math.max(1,n-g0.lt);g0.lx=t.clientX;g0.lt=n}},{passive:false});
world.addEventListener('touchend',()=>{if(!g0)return;if(g0.axis==='x'){suppressClick=performance.now();
 const moved=(g0.x0-trackX)/pitch();let i=cur+Math.round(moved);if(Math.abs(g0.v)>.4&&Math.round(moved)===0)i=cur+(g0.v<0?1:-1);go(i,true)}g0=null});
world.addEventListener('click',e=>{if(performance.now()-suppressClick<300){e.stopPropagation();e.preventDefault()}},true);
window.addEventListener('resize',layout);
// ================= CATCH-UP (offline / resume) =================
let lastG=gnow();
function catchUp(showSummary){const t=gnow(),gap=(t-lastG)/1000;lastG=t;if(gap<=0)return;
 const m0=S.money;
 // income: simulate in chunks; ship events applied in order (first step capped at 4h)
 const incomeSec=Math.min(gap,CFG.offlineCapSec*SPEED);let e=0,l=incomeSec;const rate=gap>30?CFG.offlineRate:1;
 while(l>0){const s=Math.min(5,l);e+=step(s,false,rate);l-=s}
 const ev=advanceShip(t);
 if(gap>30&&showSummary!==false){const real=gap/SPEED,h=Math.floor(real/3600),mi=Math.floor(real%3600/60);
  const land=ev.find(x=>x.type==='landed');
  $('#wbtext').innerHTML=`You were away ${h?h+'h ':''}${mi}m${real>=CFG.offlineCapSec?' (income capped at 4h)':''}. Your floors earned:${land?'<br><br>'+landedMsg(land):''}`;
  $('#wbamt').textContent=fmt(e);$('#modal').classList.add('on');
  $('#wbok').onclick=()=>{for(const k in S.f){S.money+=S.f[k].pend;S.f[k].pend=0}$('#modal').classList.remove('on');render();save()}}
 const ld=ev.find(x=>x.type==='landed');if(ld){setTimeout(dust,300);if(!(gap>30&&showSummary!==false))setTimeout(()=>toast(landedMsg(ld)),400)}   // finished while closed: straight on pad + dust puff
 save()}
// ================= LOOP =================
build();catchUp();render();layout();go(0,false);panels.forEach(p=>p.scrollTop=p.scrollHeight);panels[1].scrollTop=0;
let lastF=performance.now(),acc=0,saveT=0;
function frame(now){const fdt=Math.min(.1,(now-lastF)/1000);lastF=now;
 if(!document.hidden&&!$('#modal').classList.contains('on')){const t=gnow(),gdt=(t-lastG)/1000;
  if(gdt>2){catchUp()}else{lastG=t;step(gdt,true);
   const ev=advanceShip(t);ev.forEach(x=>{if(x.type==='landed'){landAnim();toast(landedMsg(x))}if(x.type==='ready')toast('🛰 Ship ready. Loading cargo…')});if(ev.length)save()}
  loadingVisuals(t);acc+=fdt;saveT+=fdt;if(acc>.2){acc=0;render();drawSheet()}if(saveT>5){saveT=0;save()}}
 walk(fdt);moveCarriers(fdt);requestAnimationFrame(frame)}
requestAnimationFrame(frame);
document.addEventListener('visibilitychange',()=>{if(document.hidden)save();else{lastF=performance.now();catchUp()}});
window.addEventListener('pagehide',save);
window.PS={S,F,CFG,SPEED,save,gnow,launch:doLaunch,reset:()=>{localStorage.removeItem(SAVEKEY);location.reload()}};
