'use strict';
// =====================================================================
// Planet Stack — Moon. Resource economy, 5 buildings, elevators, starter cargo ship.
// Canvas world + flat DOM UI. All tuning lives in CFG / BUILDINGS below.
// =====================================================================
const CFG={
 maxLevel:50,tierLevels:[10,20,30,40,50],tierMult:2,                 // output ×2 only at tier levels
 earlyLevels:10,earlyGrowth:1.25,earlyCost:1.22,lateGrowth:1.10,lateCost:1.20,
 tierUtility:0.10,tierIndustrial:0.10,eliteBuilding:0.10,masteredPlanet:0.10,oxygenCrewSpeed:0.10,autoCollectSec:30,
 tierColors:['#c98b4a','#9fd6ff','#ff9a3c','#c08cff','#ffd34d'],
 offlineCapSec:4*3600,offlineRate:0.5,tutorialLevel:3,
 maxFloors:10,siteAngleDeg:72,rotPerSlot:0.5,neighbourSink:900,surfaceScroll:6,towerScale:0.93,
 econ:{startGrant:500,stipendPerResident:0.25,arrivalSec:20,leaveSec:10,
  pod:{housing:4,oxygen:0,water:4,energy:8},kwPerPerson:1,staffBonus:0.25,
  padCrateCap:60,crateValue:40,refinedMult:3},
 elevator:{maxLevel:100,speedPerLevel:1.03,baseCapacity:1,capacityEvery:5,cost:25,costMult:1.12,lookEvery:10,bonusPerLevel:0.01,
  travelBaseMs:220,travelPerFloorMs:90,
  looks:['cage','steel','glass','maglev','cargo','panorama','hauler','twin_deck','neon','platinum','gold_express']},
 ship:{holdCrates:12,tripSec:600,turnaroundSec:60},
};
const QS=new URLSearchParams(location.search);
const SPEED=Math.max(0.1,+QS.get('speed')||1),DBG=QS.has('dbg');
// ----- buildings (order on the Moon). Max 10 floors each. -----
const BUILDINGS=[
 {id:'life',name:'Life Support',art:'life',floors:[
  {id:'oxy',name:'Oxygen Plant',art:'oxygen',role:'resource',res:'oxygen',cost:0,out:3,use:1,up:15,desc:'Makes oxygen. More oxygen supports more people.'},
  {id:'water',name:'Water',art:'water',role:'resource',res:'water',cost:120,req:{floor:'oxy',lvl:3},out:4,use:1,up:70,desc:'Makes water. More water supports more people.'},
  {id:'nuke',name:'Nuclear Power',art:'nuclear',role:'resource',res:'energy',cost:300,out:12,use:0,up:110,crew:'engineer',desc:'Makes energy for every floor and every person.'}]},
 {id:'mine',name:'He & Pt Mine',full:'Helium & Platinum Mine',art:'mine',needs:{building:'life',floors:3},pad:true,floors:[
  {id:'rover',name:'Rover Bay',art:'mine_rover_bay',role:'mine',cost:1000,out:2,use:2,up:300,ph:'#5a4a3a',desc:'Rovers drive out, scoop regolith and dump it in the hopper. Higher levels add rovers and speed.'},
  {id:'crusher',name:'Crusher',art:'mine_crusher',role:'mine',cost:2500,out:2.2,use:1,up:700,ph:'#4a4a5a',desc:'Crushes regolith into fines.'},
  {id:'separator',name:'Separator',art:'mine_separator',role:'mine',cost:6250,out:2.4,use:3,up:1800,ph:'#2f4a5a',crew:'engineer',desc:'Separates Helium-3 and platinum. Uses a lot of energy.'},
  {id:'packing',name:'Packing',art:'mine_packing',role:'mine',cost:15600,out:2.6,use:1,up:4500,ph:'#4a3f2a',desc:'Packs LOADED crates. They stack on the launch pad for the cargo ship.'}]},
 {id:'hab',name:'Habitat',art:'hab',needs:{building:'life',floors:3},floors:[
  {id:'living',name:'Living Quarters',art:'living_quarters',role:'housing',cost:750,out:6,use:2,up:250,desc:'Beds. Sets the population cap.'},
  {id:'markets',name:'Markets',art:'markets',role:'shop',cost:1875,out:0.12,use:3,up:600,desc:'Residents shop here: earns per resident.'}]},
 {id:'yard',name:'Shipyard',soon:true,note:'Refinery: LOADED crates ×3',floors:[]},
 {id:'eng',name:'Engineering',soon:true,floors:[]},
];
BUILDINGS.forEach(b=>{if(b.floors.length>CFG.maxFloors)throw new Error(b.name+': max 10 floors')});
// camera stops: each building, plus the Mine's starter launch pad between Mine and Habitat
const STOPS=[];BUILDINGS.forEach((b,bi)=>{STOPS.push({kind:'tower',bi,name:b.full||b.name});if(b.pad)STOPS.push({kind:'pad',bi,name:'Mine Launch Pad'})});
const RES={oxygen:{label:'Oxygen',pick:'pickup_o2'},water:{label:'Water',pick:'pickup_water'},energy:{label:'Energy',pick:'pickup_energy'}};
const TIER_DEFAULTS={
 10:{name:'Upgraded',effect:'Second crew station',art:'Upgraded fit-out'},
 20:{name:'Advanced',effect:'+10% output on this floor',art:'Advanced equipment'},
 30:{name:'Industrial',shopName:'Premium',effect:'+10% output',shopEffect:'Auto-collects every 30 s',art:'Automation'},
 40:{name:'Elite',effect:'+10% output for the whole building',art:'Elite trim'},
 50:{name:'Mastered',effect:'Badge + 10% output for the whole planet',art:'Mastered finish'}};
const FLOOR_TIERS={oxy:{10:{art:'Second electrolysis tank'},20:{effect:'Astronauts 10% faster on all floors',art:'CO₂ scrubber wall'},30:{art:'Industrial pipes'},40:{art:'Glowing O₂ core'},50:{art:'Gold dome'}}};
const F=[];BUILDINGS.forEach((b,bi)=>b.floors.forEach((d,k)=>{d.b=bi;d.k=k;d.role=d.role||'income';F.push(d)}));
const IDX={};F.forEach((d,i)=>IDX[d.id]=i);
F.forEach(d=>{d.tierInfo={};CFG.tierLevels.forEach(L=>{const t=Object.assign({},TIER_DEFAULTS[L],(FLOOR_TIERS[d.id]||{})[L]);if(d.role==='shop'){if(t.shopName)t.name=t.shopName;if(t.shopEffect)t.effect=t.shopEffect}d.tierInfo[L]=t})});
const $=s=>document.querySelector(s);
// =====================================================================
// ART: @3x or @2x WebP set by DPR; lazy groups per building
// =====================================================================
const DEV_DPR=Math.min(3,window.devicePixelRatio||1);
const ART=`art/moon/${DEV_DPR>2?'@3x':'@2x'}/`;
const SPR={};   // key → {path, group, atlas?|floor?} ; filled when loaded
function def(key,path,group,kind){SPR[key]={path,group,kind:kind||'atlas'}}
// core (first screen)
['sky','stars','stars_twinkle','earth','globe','globe_shade','globe_surface_strip'].forEach(n=>def(n,'bg/'+n,'core','img'));
def('base400','world/tower_base_400','core');def('site','world/site_marker','core');
['walk','idle','wave','carry'].forEach(a=>def(a+'_worker','astronaut/astronaut_'+a,'core'));
['walk','idle'].forEach(a=>def(a+'_engineer','astronaut/astronaut_engineer_'+a,'core'));
['coin_spin','coin_sparkle','pickup_o2_spin','pickup_o2_sparkle','pickup_water_spin','pickup_water_sparkle','pickup_energy_spin','pickup_energy_sparkle','pickup_people_spin','pickup_people_sparkle','fx_collect_sparkle','fx_upgrade_burst','floor_low_power','icon_low_power_blink','fx_door_hiss','fx_welcome_sparkle'].forEach(n=>def(n,'fx/'+n,'core'));
['shaft_tile','shaft_top','shaft_pit','cable_tile','rider','capacity_badge'].forEach(n=>def('el_'+n,'elevator/'+n,'core','img'));
def('el_call_panel','elevator/call_panel','core');def('el_floor_indicator','elevator/floor_indicator','core');
// heavy fx: loaded right after the first screen
['fx_floor_unlock','fx_tierup_flash_rays','fx_gold_shimmer','fx_elevator_tierup'].forEach(n=>def(n,'fx/'+n,'fx2'));
CFG.tierLevels.forEach(L=>def('banner_'+L,'fx/tier_banner_l'+L,'fx2','img'));
// per building floors
const MINE=`../mine/${DEV_DPR>2?'@3x':'@2x'}/`;   // art/moon/mine/@Nx (loaded only when the Mine unlocks)
F.filter(d=>d.art).forEach(d=>{const m=d.role==='mine';def('f_'+d.id,(m?MINE:'')+'floors/floor_'+d.art,BUILDINGS[d.b].art,'floor');if(m)SPR['f_'+d.id].lowpower=true});
['rover_drive','rover_scoop','rover_dump'].forEach(n=>def(n,MINE+'rover/'+n,'mine'));
['loaded_box_pulse','loaded_box_sealed','loaded_box_stack3'].forEach(n=>def(n,MINE+'box/'+n,'mine'));
def('mine_pad',MINE+'pad/mine_pad','mine');def('surface_hopper',MINE+'pad/surface_hopper','mine','img');
// mine + ship (starter ship lives at the Mine)
['ship','ship_flame','smoke_plume','dust_puff'].forEach(n=>def(n,'ship/'+n,'mine'));
def('walk_medic','astronaut/astronaut_medic_walk','hab');def('idle_medic','astronaut/astronaut_medic_idle','hab');
const groupState={};
async function tryJSON(p){try{const r=await fetch(p);if(r.ok)return await r.json()}catch(e){}return null}
function getImg(src){return new Promise(res=>{const im=new Image();im.onload=()=>res(im);im.onerror=()=>res(null);im.src=src})}
const bmp=async im=>{if(!im)return null;try{return await createImageBitmap(im)}catch(e){return im}};
let loadedBytes=0;
async function loadSprite(key){const s=SPR[key];if(s.ready||s.loading)return s.loading;
 s.loading=(async()=>{
  if(s.kind==='img'){s.img=await bmp(await getImg(ART+s.path+'.webp'));if(s.img){s.w=s.img.width/(DEV_DPR>2?3:2);s.h=s.img.height/(DEV_DPR>2?3:2);if(key==='surface_hopper'){s.px=30;s.py=40}}}
  else if(s.kind==='floor'){const j=await tryJSON(ART+s.path+'.json');if(j){const dir=ART+s.path.replace(/[^/]+$/,'');
    s.base=await bmp(await getImg(dir+j.base));s.pages=await Promise.all(j.layersImages.map(async n=>bmp(await getImg(dir+n))));s.layers=j.layers;s.fps=j.fps;s.n=j.frames;if(s.lowpower)s.lp=await bmp(await getImg(ART+s.path+'_lowpower.webp'))}}
  else{const j=await tryJSON(ART+s.path+'.json');if(j){const m=j.meta,dir=ART+s.path.replace(/[^/]+$/,'');
    s.frames=Object.values(j.frames).map(f=>Object.assign({page:f.page||0},f.frame));s.n=s.frames.length;s.fps=m.fps||1;s.w=m.logicalFrame.w;s.h=m.logicalFrame.h;s.px=m.pivot.x;s.py=m.pivot.y;s.loop=m.loop!==false;
    s.pages=await Promise.all((m.images||[m.image]).map(async n=>bmp(await getImg(dir+n))));s.img=s.pages[0]}}
  s.ready=!!(s.img||s.base);s.missing=!s.ready})();return s.loading}
function loadGroup(g,onTick){if(groupState[g])return groupState[g];const keys=Object.keys(SPR).filter(k=>SPR[k].group===g);let done=0;
 return groupState[g]=Promise.all(keys.map(k=>loadSprite(k).then(()=>{done++;onTick&&onTick(done/keys.length)})))}
function ensureBuildingArt(bi){const b=BUILDINGS[bi];if(b.art)loadGroup(b.art);if(b.pad)loadGroup('mine')}
// tier layers (cumulative): floors/tiers/floor_<art>_t<L>
function tierKey(d,L){return 't_'+d.id+'_'+L}
function ensureTier(d,L){const k=tierKey(d,L);if(!SPR[k]){def(k,`floors/tiers/floor_${d.art}_t${L}`,'tier','floor');loadSprite(k)}return SPR[k]}
function ensureLook(look){const kb='car_'+look+'_back',kd='car_'+look+'_doors';if(!SPR[kb]){def(kb,'elevator/'+kb,'look','img');def(kd,'elevator/'+kd,'look');loadSprite(kb);loadSprite(kd)}return SPR[kb].ready&&SPR[kd].ready}
const ok=k=>SPR[k]&&SPR[k].ready;
function spr(c,key,frame,x,y,sx=1,sy=1){const S=SPR[key];if(!S||!S.ready)return;if(!S.frames){c.drawImage(S.img,x-(S.px||0)*sx,y-(S.py||0)*sy,S.w*sx,S.h*sy);return}
 const f=S.frames[((frame|0)%S.n+S.n)%S.n];c.drawImage(S.pages[f.page],f.x,f.y,f.w,f.h,x-S.px*sx,y-S.py*sy,S.w*sx,S.h*sy)}
const fr=(k,t)=>SPR[k]&&SPR[k].ready?Math.floor(t*SPR[k].fps)%SPR[k].n:0;
const frOnce=(k,t)=>SPR[k]&&SPR[k].ready?Math.floor(t*SPR[k].fps):99;
function drawLayers(c,s,t,paused){if(!s||!s.ready||!s.layers)return;const gf=paused?0:Math.floor(t*s.fps);
 for(const L of s.layers){const q=L.frames[((gf%L.frames.length)+L.frames.length)%L.frames.length];c.drawImage(s.pages[q.page||0],q.x,q.y,q.w,q.h,L.x,L.y-120,L.w,L.h)}}
// =====================================================================
// SAVE / TIME — everything runs from saved timestamps
// =====================================================================
const SAVEKEY=location.pathname.includes('/preview/')?'planetstack-preview':'planetstack_moon_v2';
function fresh(){const n=Date.now();return{money:CFG.econ.startGrant,pop:1,arr:0,crates:0,crateAcc:0,gt:n,rt:n,step:0,hint:0,tapped:0,
 elev:Object.fromEntries(BUILDINGS.map(b=>[b.id,1])),ship:{st:'docked',t:n,cargo:0},
 f:Object.fromEntries(F.map(d=>[d.id,{built:d.cost===0,lvl:1,workers:d.cost===0?1:0,pend:0,ac:0}]))}}
function load(){try{const s=JSON.parse(localStorage.getItem(SAVEKEY));if(s&&s.f){const z=fresh();for(const k in z.f)s.f[k]=Object.assign(z.f[k],s.f[k]);s.elev=Object.assign(z.elev,s.elev);s.ship=Object.assign(z.ship,s.ship);return Object.assign(z,s,{f:s.f})}}catch(e){}return fresh()}
let S=load();
const gnow=()=>S.gt+(Date.now()-S.rt)*SPEED;
function save(){S.gt=gnow();S.rt=Date.now();try{localStorage.setItem(SAVEKEY,JSON.stringify(S))}catch(e){}}
const st=i=>S.f[F[i].id];
// =====================================================================
// ECONOMY — floors make resources; money comes from people (and cargo)
// =====================================================================
const tiersReached=l=>CFG.tierLevels.filter(L=>l>=L).length;
const tierOf=l=>{let t=0;CFG.tierLevels.forEach(L=>{if(l>=L)t=L});return t};
const nextTier=l=>CFG.tierLevels.find(L=>l<L);
function growth(l,e,la){return Math.pow(e,Math.min(l,CFG.earlyLevels)-1)*Math.pow(la,Math.max(0,l-CFG.earlyLevels))}
const upCost=(i,lv=st(i).lvl)=>Math.round(F[i].up*growth(lv,CFG.earlyCost,CFG.lateCost));
const floorsBuilt=bi=>BUILDINGS[bi].floors.filter(d=>S.f[d.id].built).length;
const siteOpen=bi=>{const b=BUILDINGS[bi];if(b.soon)return false;if(!b.needs)return true;return floorsBuilt(BUILDINGS.findIndex(x=>x.id===b.needs.building))>=b.needs.floors};
const floorSlots=f=>f.lvl>=10?2:1;
const totalWorkers=()=>F.reduce((a,d)=>a+S.f[d.id].workers,0);
const idleResidents=()=>Math.max(0,Math.floor(S.pop)-totalWorkers());
const elevLvl=bi=>S.elev[BUILDINGS[bi].id]||1;
const elevSpeedMul=bi=>Math.pow(CFG.elevator.speedPerLevel,elevLvl(bi)-1);
const elevCap=bi=>CFG.elevator.baseCapacity+Math.floor(elevLvl(bi)/CFG.elevator.capacityEvery);
const elevCost=bi=>Math.round(CFG.elevator.cost*Math.pow(CFG.elevator.costMult,elevLvl(bi)-1));
const elevLook=bi=>CFG.elevator.looks[Math.min(CFG.elevator.looks.length-1,Math.floor(elevLvl(bi)/CFG.elevator.lookEvery))];
const crewMul=()=>S.f.oxy.lvl>=20?1+CFG.oxygenCrewSpeed:1;
// output at full power for a given level/crew (people supported · kW · beds · $/resident/s · crates/min)
function rawOut(i,lv,w){const f=st(i),d=F[i];lv=lv||f.lvl;w=w==null?f.workers:w;if(!f.built||w<1)return 0;
 let x=d.out*growth(lv,CFG.earlyGrowth,CFG.lateGrowth)*Math.pow(CFG.tierMult,tiersReached(lv))*(1+CFG.econ.staffBonus*(w-1));
 if(lv>=20&&d.id!=='oxy')x*=1+CFG.tierUtility;if(lv>=30&&d.role!=='shop')x*=1+CFG.tierIndustrial;
 BUILDINGS[d.b].floors.forEach(o=>{if(S.f[o.id].built&&S.f[o.id].lvl>=40)x*=1+CFG.eliteBuilding});
 F.forEach(o=>{if(S.f[o.id].built&&S.f[o.id].lvl>=50)x*=1+CFG.masteredPlanet});
 return x*(1+CFG.elevator.bonusPerLevel*(elevLvl(d.b)-1))}
let E={};
function econ(){const P=CFG.econ.pod,e={oxygen:P.oxygen,water:P.water,energy:P.energy,housing:P.housing,floorUse:0,shop:0};
 F.forEach((d,i)=>{if(d.res==='energy')e.energy+=rawOut(i);if(st(i).built&&st(i).workers>0)e.floorUse+=d.use||0});
 const pop=Math.floor(S.pop);e.demand=e.floorUse+pop*CFG.econ.kwPerPerson;e.power=e.demand>0?Math.min(1,e.energy/e.demand):1;
 F.forEach((d,i)=>{const o=rawOut(i)*(d.use?e.power:1);d._out=o;if(d.res==='oxygen')e.oxygen+=o;if(d.res==='water')e.water+=o;if(d.role==='housing')e.housing+=o;if(d.role==='shop')e.shop+=o*pop});
 e.energySupport=Math.max(0,e.energy-e.floorUse)/CFG.econ.kwPerPerson;
 const lim={Beds:e.housing,Oxygen:e.oxygen,Water:e.water,Energy:e.energySupport};
 e.cap=Math.floor(Math.min(...Object.values(lim)));e.limit=Object.keys(lim).reduce((a,k)=>lim[k]<lim[a]?k:a,'Beds');e.lim=lim;
 e.mine=S.f.packing.built?Math.min(...['rover','crusher','separator','packing'].map(id=>F[IDX[id]]._out)):0;   // crates/min = slowest stage
 e.stipend=pop*CFG.econ.stipendPerResident;e.rate=e.stipend+e.shop;E=e;return e}
let stipendAcc=0,lastStipendFx=0;
function step(dt,live,rate=1){const e=econ();let earned=0;
 if(S.pop<e.cap){S.arr+=dt;while(S.arr>=CFG.econ.arrivalSec&&S.pop<e.cap){S.arr-=CFG.econ.arrivalSec;S.pop++;if(live)residentArrives()}}
 else if(S.pop>e.cap){S.arr+=dt;if(S.arr>=CFG.econ.leaveSec){S.arr=0;S.pop=Math.max(e.cap,S.pop-1);if(live)toast(`👋 A resident left: not enough ${e.limit.toLowerCase()}`)}}else S.arr=0;
 let over=totalWorkers()-Math.floor(S.pop);for(let i=F.length-1;i>=0&&over>0;i--){const f=st(i);while(f.workers>0&&over>0&&!(i===0&&f.workers===1)){f.workers--;over--}}
 // auto-assign idle residents to unstaffed floors (Life Support first)
 for(let i=0;i<F.length&&idleResidents()>0;i++){const f=st(i);if(f.built&&f.workers<1){f.workers=1;if(live){crewSync();toast(`👩‍🚀 A resident now staffs ${F[i].name}`)}}}
 const sti=e.stipend*dt*rate;S.money+=sti;earned+=sti;
 F.forEach((d,i)=>{if(d.role==='shop'){const g=d._out*Math.floor(S.pop)*dt*rate;st(i).pend+=g;earned+=g}});
 if(e.mine>0&&S.crates<CFG.econ.padCrateCap){S.crateAcc+=e.mine*dt/60;while(S.crateAcc>=1&&S.crates<CFG.econ.padCrateCap){S.crateAcc--;S.crates++;if(live){const d=F[IDX.packing],p=floorPt(d,300,104);FX.push({type:'sprite',key:'loaded_box_sealed',si:p.si,x:p.x,y:p.y,t:T})}}}
 if(live){stipendAcc+=sti;if(stipendAcc>=1&&T-lastStipendFx>3){stipendFx(Math.floor(stipendAcc));stipendAcc=0;lastStipendFx=T}}
 return earned}
// ----- starter cargo ship (timestamps) -----
const crateWorth=()=>CFG.econ.crateValue;   // Refinery (Shipyard, later) will multiply by refinedMult
function shipTick(t,live){const s=S.ship,ev=[];
 if(s.st==='trip'&&t>=s.t+CFG.ship.tripSec*1000){const v=Math.round(s.cargo*crateWorth());S.money+=v;ev.push({type:'landed',v});s.st='turn';s.t+=CFG.ship.tripSec*1000;s.cargo=0}
 if(s.st==='turn'&&t>=s.t+CFG.ship.turnaroundSec*1000){s.st='docked';s.t+=CFG.ship.turnaroundSec*1000;ev.push({type:'ready'})}
 return ev}
function launchShip(){const s=S.ship;if(s.st!=='docked'||S.crates<1)return false;const n=Math.min(CFG.ship.holdCrates,S.crates);S.crates-=n;s.cargo=n;s.st='trip';s.t=gnow();save();return true}
const fmt=n=>{n=Math.floor(n);if(n<1e4)return '$'+n.toLocaleString('en-US');const u=['K','M','B','T'];let k=-1;while(n>=1e3&&k<3){n/=1e3;k++}return '$'+n.toFixed(n<100?1:0)+u[k]};
const num=n=>n<10?n.toFixed(1):n<1e4?Math.floor(n).toLocaleString('en-US'):fmt(n).slice(1);
const mmss=s=>{s=Math.max(0,Math.ceil(s));return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')};
function lockReason(i){const d=F[i],b=BUILDINGS[d.b];if(b.soon)return 'Coming soon';
 if(b.needs&&!siteOpen(d.b)){const nb=BUILDINGS.find(x=>x.id===b.needs.building);return `Needs ${b.needs.floors} ${nb.name} floors`}
 if(d.req&&S.f[d.req.floor].lvl<d.req.lvl)return `Needs ${F[IDX[d.req.floor]].name.replace(' Plant','')} level ${d.req.lvl}`;
 if(S.money<d.cost)return `Need ${fmt(d.cost-S.money)} more`;return null}
const nextFloor=bi=>BUILDINGS[bi].floors.find(d=>!S.f[d.id].built);
// meter line shown on each floor
function meter(i){const d=F[i],o=d._out||0;if(!st(i).workers)return 'No crew';
 if(d.res==='oxygen')return `Oxygen: supports ${Math.floor(o)} people`;if(d.res==='water')return `Water: supports ${Math.floor(o)} people`;
 if(d.res==='energy')return `Energy: ${num(E.energy||0)} kW · using ${num(E.demand||0)}`;if(d.role==='housing')return `Beds: ${Math.floor(o)}`;
 if(d.role==='shop')return `${fmt(o*Math.floor(S.pop)*60)}/min from ${Math.floor(S.pop)} residents`;if(d.role==='mine')return `${num(o)} crates/min`;return ''}
// ----- goals -----
const GOALS=[
 {d:'Tap the Oxygen Plant',p:()=>S.tapped?1:0},
 {d:`Upgrade the Oxygen Plant to level ${CFG.tutorialLevel}`,p:()=>Math.min(1,(S.f.oxy.lvl-1)/(CFG.tutorialLevel-1))},
 {d:'Build Water',p:()=>S.f.water.built?1:Math.min(.99,S.money/F[IDX.water].cost)},
 {d:'Build Nuclear Power',p:()=>S.f.nuke.built?1:Math.min(.99,S.money/F[IDX.nuke].cost)},
 {d:'Swipe to the Habitat and build Living Quarters',p:()=>S.f.living.built?1:Math.min(.99,S.money/F[IDX.living].cost)},
 {d:'Build the Markets',p:()=>S.f.markets.built?1:Math.min(.99,S.money/F[IDX.markets].cost)},
 {d:'Open the Mine: build the Rover Bay',p:()=>S.f.rover.built?1:Math.min(.99,S.money/F[IDX.rover].cost)},
 {d:'Grow the base: more residents, more income',p:()=>1,last:true}];
function goalTick(){let g=GOALS[S.step];if(!g.last&&g.p()>=1){S.step++;g=GOALS[S.step];const el=$('#goal');el.classList.add('pop');setTimeout(()=>el.classList.remove('pop'),350);toast('✅ Goal complete!')}
 $('#gd').textContent=g.d;$('#gp').style.width=(g.p()*100)+'%'}
// =====================================================================
// RENDER
// =====================================================================
const cv=$('#cv'),ctx=cv.getContext('2d',{alpha:false});
let W=390,H=844,DPR=DEV_DPR,SC=1,OY=0,OX=0,TS=0.93;
const snap=v=>Math.round(v*DPR*SC)/(DPR*SC);
function smooth(c){c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high'}
const C={x:195,y:1320},R=760,HOR=560,FOOT_MID=13.67,FX0=-200;   // tower_base_400: middle of the curved bottom is 13.67pt below its top
function resize(){DPR=DEV_DPR;W=innerWidth;H=innerHeight;cv.width=Math.round(W*DPR);cv.height=Math.round(H*DPR);   // never lowered
 SC=Math.max(0.5,Math.round(W/390*DPR*4)/(4*DPR));if(390*SC>W)SC=Math.floor(W/390*DPR*4)/(4*DPR);
 OX=snap((W/SC-390)/2);OY=snap(H/SC-844);
 TS=Math.round(Math.min(CFG.towerScale,(W/SC-6)/412)*DPR*SC*4)/(4*DPR*SC);   // tower group fits 390 and lands on a clean device-pixel ratio
 smooth(ctx);skyC=null;band.width=0;for(const k in towerCache)delete towerCache[k];dbgText()}
addEventListener('resize',resize);
function dbgText(fps){if(!DBG)return;let el=$('#dbg');if(!el){el=document.createElement('div');el.id='dbg';document.body.appendChild(el)}
 el.textContent=`devicePixelRatio ${window.devicePixelRatio}\nDPR used ${DPR}\ncanvas ${cv.width}×${cv.height} (${(cv.width/innerWidth).toFixed(2)}×)\nSC ${SC}  tower ${TS.toFixed(4)}\nart ${ART}${fps?`\nfps ${fps}`:''}`}
const cam={rot:0,y:0,vy:0,anim:null};
let skyC=null;
function skyLayer(){const w=W*DPR|0,h=H*DPR|0;if(skyC&&skyC.width===w&&skyC.height===h)return skyC;skyC=document.createElement('canvas');skyC.width=w;skyC.height=h;const c=skyC.getContext('2d');smooth(c);if(ok('sky'))c.drawImage(SPR.sky.img,0,0,w,h);return skyC}
const band=document.createElement('canvas'),bctx=band.getContext('2d'),BAND_TOP=HOR-6,BAND_H=190;
function drawBand(u0){const s=Math.min(2,DPR)*SC;if(band.width!==(390*s|0)){band.width=390*s|0;band.height=BAND_H*s|0;smooth(bctx)}
 const b=bctx,img=SPR.globe_surface_strip.img,k=img.width/1200,SW=3;b.setTransform(1,0,0,1,0,0);b.clearRect(0,0,band.width,band.height);b.setTransform(s,0,0,s,0,-BAND_TOP*s);
 for(let x=-60;x<=450;x+=SW){const a=Math.asin((x+SW/2-C.x)/R),px=C.x+R*Math.sin(a),py=C.y-R*Math.cos(a);let u=((R*a+u0)%1200+1200)%1200;
  b.save();b.translate(px,py);b.rotate(a);const sw=Math.min(SW+0.6,1200-u);b.drawImage(img,u*k,0,sw*k,160*k,-SW/2-0.3,0,sw,160);
  if(sw<SW+0.6)b.drawImage(img,0,0,(SW+0.6-sw)*k,160*k,-SW/2-0.3+sw,0,SW+0.6-sw,160);b.restore()}
 b.globalCompositeOperation='destination-in';const g=b.createRadialGradient(C.x,C.y,R-150,C.x,C.y,R-100);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'#000');b.fillStyle=g;b.beginPath();b.arc(C.x,C.y,R,0,7);b.fill();b.globalCompositeOperation='source-over'}
// ----- stop geometry -----
const stopOfTower=bi=>STOPS.findIndex(s=>s.kind==='tower'&&s.bi===bi);
function stopFrame(si){const a=si*CFG.rotPerSlot-cam.rot,sink=Math.abs(a)>0.02?CFG.neighbourSink*(1-Math.cos(a)):0;
 return{a,x:C.x+(R-sink)*Math.sin(a),y:C.y-(R-sink)*Math.cos(a)}}
const floorBottom=k=>-FOOT_MID+4-k*120;
let T=0,dtG=0,site=0;
const floorFx={},crew={},elev={};
function crewSync(){F.forEach((d,i)=>{const f=st(i),arr=crew[d.id]||(crew[d.id]=[]);
 while(arr.length<Math.min(4,f.workers))arr.push({x:40+Math.random()*260,v:(Math.random()<.5?-1:1)*30,idle:0,t:Math.random()*5});arr.length=Math.min(arr.length,f.workers)})}
function crewTick(dt){const m=crewMul();for(const id in crew)for(const a of crew[id]){if(a.idle>0){a.idle-=dt;continue}a.x+=a.v*dt*m;if(a.x<16||a.x>344){a.v=-a.v;a.x=Math.max(16,Math.min(344,a.x))}if(Math.random()<dt*.12)a.idle=1+Math.random()*2}}
function render(){ctx.setTransform(DPR,0,0,DPR,0,0);smooth(ctx);
 ctx.setTransform(DPR*SC,0,0,DPR*SC,Math.round(OX*DPR*SC),0);
 const rx=cam.rot*R,sx=((-rx*0.05)%390+390)%390,syy=OY*0.5+cam.y*0.05;
 ctx.drawImage(skyLayer(),-OX,0,W/SC,H/SC);
 ctx.save();ctx.translate(0,syy);if(ok('stars')){ctx.drawImage(SPR.stars.img,sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars.img,sx-390,0,390,844)}
 if(ok('stars_twinkle')){const tw=0.675+0.325*Math.sin(T*Math.PI*2/2.4);ctx.globalAlpha=tw;ctx.drawImage(SPR.stars_twinkle.img,sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars_twinkle.img,sx-390,0,390,844);
  ctx.globalAlpha=1.35-tw;ctx.scale(-1,1);ctx.drawImage(SPR.stars_twinkle.img,-390-sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars_twinkle.img,-sx,0,390,844)}
 ctx.restore();ctx.globalAlpha=1;
 if(ok('earth'))ctx.drawImage(SPR.earth.img,40-rx*0.1,90+OY*0.4+cam.y*0.1+Math.sin(T*Math.PI*2/20)*2,120,120);
 ctx.save();ctx.translate(0,snap(OY+cam.y));
 const vis=STOPS.map((s,si)=>({s,si,f:stopFrame(si)})).filter(o=>Math.abs(o.f.a)<0.9);
 vis.filter(o=>Math.abs(o.f.a)>=0.02).forEach(drawStop);                 // neighbours sink behind the horizon
 if(ok('globe'))ctx.drawImage(SPR.globe.img,0,0,390,844);
 if(ok('globe_surface_strip')){drawBand(T*CFG.surfaceScroll+rx);ctx.drawImage(band,0,BAND_TOP,390,BAND_H)}
 if(ok('globe_shade'))ctx.drawImage(SPR.globe_shade.img,0,0,390,844);
 vis.filter(o=>Math.abs(o.f.a)<0.02).forEach(drawStop);
 drawFX();ctx.restore()}
function drawStop(o){const {s,f}=o;ctx.save();
 if(Math.abs(f.a)<0.001)ctx.translate(snap(f.x),snap(f.y));else{ctx.translate(f.x,f.y);ctx.rotate(f.a)}
 ctx.scale(TS,TS);const atRest=Math.abs(f.a)<0.001;
 if(s.kind==='pad')drawPad(s.bi,atRest);else{const n=floorsBuilt(s.bi);if(n===0)drawSite(s.bi);else drawTower(s.bi,n,atRest)}
 ctx.restore()}
function label(x,y,txt,col,size){ctx.font=`700 ${size}px Inter,system-ui,-apple-system,sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='rgba(0,0,0,.55)';ctx.fillText(txt,x,y+1);ctx.fillStyle=col;ctx.fillText(txt,x,y)}
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath()}
function chip(x,y,txt,bg,fg,font){ctx.font=font||'700 11px Inter,system-ui,-apple-system,sans-serif';const w=ctx.measureText(txt).width+12;ctx.fillStyle=bg||'rgba(10,14,26,.66)';rr(ctx,x,y,w,17,8);ctx.fill();ctx.fillStyle=fg||'#eaf2ff';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,x+6,y+9);return w}
function pillBtn(x,y,txt,on){const p=on?1+0.03*Math.sin(T*5):1;ctx.save();ctx.translate(x,y);ctx.scale(p,p);ctx.font='800 15px Rajdhani,Inter,system-ui,sans-serif';const w=ctx.measureText(txt).width+34;
 const g=ctx.createLinearGradient(0,-18,0,18);if(on){g.addColorStop(0,'#ffb347');g.addColorStop(1,'#ff8a2a')}else{g.addColorStop(0,'#3a4560');g.addColorStop(1,'#2a3247')}
 ctx.fillStyle=on?'#a84c0c':'#161b27';rr(ctx,-w/2,-17,w,38,19);ctx.fill();ctx.fillStyle=g;rr(ctx,-w/2,-19,w,36,18);ctx.fill();if(!on){ctx.strokeStyle='#5b667e';ctx.lineWidth=1.5;ctx.stroke()}
 ctx.fillStyle=on?'#3a1600':'#eaf2ff';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(txt,0,0);ctx.restore()}
function drawSite(bi){const b=BUILDINGS[bi],open=siteOpen(bi),p=1+0.03*Math.max(0,Math.sin(T*Math.PI*2/1.6));
 spr(ctx,'site',fr('site',T),0,-6,p,p);label(0,-112,b.full||b.name,'#c9d3e6',15);
 if(b.soon)label(0,-93,b.note?`Coming soon · ${b.note}`:'Coming soon','#8fa3c4',12);
 else if(!open){label(0,-93,`🔒 Needs ${b.needs.floors} floors in ${BUILDINGS.find(x=>x.id===b.needs.building).name}`,'#ffb347',13)}
 else{const nf=nextFloor(bi),why=lockReason(IDX[nf.id]);pillBtn(0,-138,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(0,-106,'🔒 '+why,'#ffb347',13)}}
// ----- floors -----
function floorScale(fx){let sx=1,sy=1;
 if(fx.build!=null){const t=(T-fx.build)/0.65;if(t<1){sy=easeOutBack(Math.min(1,t));sx=1+0.04*Math.sin(t*Math.PI)}}
 if(fx.up!=null){const t=(T-fx.up)/0.4;if(t<1){const w=Math.sin(t*Math.PI)*(1-t);sx*=1+0.05*w;sy*=1-0.06*w}}
 if(fx.tap!=null){const t=(T-fx.tap)/0.16;if(t<1){const w=Math.sin(t*Math.PI);sx*=1-0.015*w;sy*=1-0.03*w}}return[sx,sy]}
const lowPower=d=>(d.use||0)>0&&E.power<0.999;
function tierLayers(d,f){if(d.id!=='oxy')return[];const out=[];CFG.tierLevels.forEach(L=>{if(f.lvl>=L){const s=ensureTier(d,L);if(s.ready)out.push({L,s})}});return out}
function floorStatic(c,d,f){const s=SPR['f_'+d.id];
 if(s&&s.ready)c.drawImage(lowPower(d)&&s.lp?s.lp:s.base,0,-120,360,120);else placeholderStatic(c,d);
 tierLayers(d,f).forEach(o=>{const dt=(floorFx[d.id]||{}).tierDrop;if(!(dt&&dt.L===o.L&&T-dt.t<0.45))c.drawImage(o.s.base,0,-120,360,120)});
 const L=tierOf(f.lvl);if(L&&d.id!=='oxy'){const col=CFG.tierColors[CFG.tierLevels.indexOf(L)];c.save();c.strokeStyle=col;c.lineWidth=3;c.globalAlpha=.9;c.strokeRect(2.5,-117.5,355,111);c.restore()}}
function floorAnim(d,f,k){const s=SPR['f_'+d.id],lp=lowPower(d),t=T+k*0.3;
 if(s&&s.ready)drawLayers(ctx,s,t,lp);else placeholderAnim(d,f,t,lp);
 tierLayers(d,f).forEach(o=>{const dt=(floorFx[d.id]||{}).tierDrop;
  if(dt&&dt.L===o.L&&T-dt.t<0.45){const q=Math.max(0,Math.min(1,(T-dt.t-0.15)/0.26));if(q>0){ctx.save();ctx.globalAlpha=q;ctx.translate(0,-24*(1-easeOutBack(q,1.7)));ctx.drawImage(o.s.base,0,-120,360,120);drawLayers(ctx,o.s,T,lp);ctx.restore()}}
  else drawLayers(ctx,o.s,T,lp)});
 if(f.lvl>=50&&ok('fx_gold_shimmer')&&d.id!=='oxy'){spr(ctx,'fx_gold_shimmer',fr('fx_gold_shimmer',T),0,0)}
 if(lp){spr(ctx,'floor_low_power',fr('floor_low_power',T),0,0);spr(ctx,'icon_low_power_blink',fr('icon_low_power_blink',T),340,-120+22)}
 if(!f.workers){ctx.fillStyle='rgba(5,8,15,.45)';ctx.fillRect(0,-120,360,120);label(180,-60,'Needs crew · tap to assign a resident','#ffb347',13)}
 const fx=floorFx[d.id]||{};if(fx.up!=null){const q=(T-fx.up)/0.25;if(q<1){ctx.globalAlpha=0.6*(1-q);ctx.fillStyle='#fff';ctx.fillRect(0,-120,360,120);ctx.globalAlpha=1}}
 (crew[d.id]||[]).forEach(a=>{const y=-120+104,role=(d.crew&&ok('walk_'+d.crew))?d.crew:'worker',key=(a.idle>0?'idle_':'walk_')+role;
  ctx.globalAlpha=.25;ctx.fillStyle='#000';ctx.beginPath();ctx.ellipse(a.x,y,6,1.2,0,0,7);ctx.fill();ctx.globalAlpha=1;
  ctx.save();ctx.translate(snap(a.x),y);if(a.v<0)ctx.scale(-1,1);spr(ctx,key,lp&&a.idle<=0?0:fr(key,T+a.t),0,0);ctx.restore()});
 const w=chip(8,-114,`${d.name}  Lv ${f.lvl}`);
 const L=tierOf(f.lvl);if(L)chip(8+w+4,-114,(L===50?'🏅 ':'★ ')+d.tierInfo[L].name,CFG.tierColors[CFG.tierLevels.indexOf(L)],'#1a1205','800 11px Inter,system-ui,sans-serif');
 chip(8,-95,(lp?'⚡ LOW POWER · ':'')+meter(IDX[d.id]),lp?'rgba(90,20,20,.8)':'rgba(10,14,26,.55)',lp?'#ffb0a8':'#bfe9ff','600 10.5px Inter,system-ui,sans-serif');
 if(f.pend>=1&&d.role==='shop'){const bob=Math.sin(T*3+k)*2;coinBubble(318,-88+bob,fmt(f.pend))}}
function coinBubble(x,y,txt){ctx.font='800 12px Rajdhani,Inter,system-ui,sans-serif';const w=ctx.measureText(txt).width+30;ctx.fillStyle='rgba(255,138,42,.95)';rr(ctx,x-w/2,y-11,w,22,11);ctx.fill();
 spr(ctx,'coin_spin',fr('coin_spin',T),x-w/2+12,y,0.8,0.8);ctx.fillStyle='#3a1600';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,x-w/2+22,y+1)}
// ----- Mine placeholders (until the rover/box art arrives) -----
function placeholderStatic(c,d){const g=c.createLinearGradient(0,-120,0,0);g.addColorStop(0,d.ph||'#3a4258');g.addColorStop(1,'#1c2130');c.fillStyle=g;c.fillRect(0,-120,360,120);
 c.fillStyle='#2a3245';c.fillRect(0,-8,360,8);c.fillStyle='#e8a11a';for(let x=0;x<360;x+=24)c.fillRect(x,-8,12,3);
 c.strokeStyle='rgba(255,255,255,.08)';c.lineWidth=1;for(let x=60;x<360;x+=60){c.beginPath();c.moveTo(x,-118);c.lineTo(x,-10);c.stroke()}
 c.fillStyle='#232a3b';c.fillRect(0,-120,360,6);c.fillStyle='rgba(255,255,255,.35)';c.font='600 9px Inter,system-ui,sans-serif';c.textAlign='right';c.textBaseline='alphabetic';c.fillText('placeholder art',352,-12);
 if(d.id==='rover'){c.fillStyle='#11151f';c.fillRect(0,-84,40,76);c.fillStyle='#4a4030';c.beginPath();c.moveTo(270,-60);c.lineTo(340,-60);c.lineTo(325,-20);c.lineTo(285,-20);c.closePath();c.fill()}
 if(d.id==='crusher'){c.fillStyle='#3d4352';c.fillRect(130,-96,100,80)}
 if(d.id==='separator'){c.fillStyle='#22303d';c.beginPath();c.arc(180,-56,36,0,7);c.fill()}
 if(d.id==='packing'){c.fillStyle='#3a3f4c';c.fillRect(20,-30,320,8)}}
function loadedCrate(c,x,y,s,t){s=s||1;c.save();c.translate(x,y);c.scale(s,s);c.fillStyle='#2f3a2c';rr(c,-11,-18,22,18,2);c.fill();c.strokeStyle='#8fa070';c.lineWidth=1;c.stroke();
 c.fillStyle='#e8c84a';c.font='800 5.5px Inter,system-ui,sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText('LOADED',0,-8);
 const on=Math.floor((t||T)*2)%2===0;c.fillStyle=on?'#5be08a':'#1d3a26';c.beginPath();c.arc(7,-14,1.6,0,7);c.fill();c.restore()}
function placeholderAnim(d,f,t,lp){const sp=lp?0.3:1,lv=f.lvl;
 if(d.id==='rover'){const n=Math.min(3,1+Math.floor(lv/10));for(let r=0;r<n;r++){const cyc=8/(1+lv*0.03),p=((t*sp+r*cyc/n)%cyc)/cyc;let x,load=false;
   if(p<0.4)x=40-p/0.4*80;else if(p<0.5){x=-40;load=true}else if(p<0.9){x=-40+(p-0.5)/0.4*300;load=true}else x=260;
   if(x>-10){ctx.save();ctx.translate(x,-14);ctx.fillStyle='#d8dde6';rr(ctx,0,-16,54,12,3);ctx.fill();ctx.fillStyle=load?'#7a6a52':'#5b667e';ctx.fillRect(28,-24,24,9);ctx.fillStyle='#ff8a2a';ctx.fillRect(4,-22,12,7);
    ctx.fillStyle='#1a1d26';for(let w=0;w<6;w++){ctx.beginPath();ctx.arc(6+w*8.4,-3,3.4,0,7);ctx.fill()}ctx.restore()}
   if(p>0.9&&p<0.93)spr(ctx,'dust_puff',Math.floor((p-0.9)/0.03*6),305,-20,0.5,0.5)}}
 if(d.id==='crusher'){const a=Math.sin(t*6*sp)*6;ctx.fillStyle='#8794ad';ctx.fillRect(140+a,-90,20,64);ctx.fillRect(200-a,-90,20,64);ctx.fillStyle='rgba(180,160,130,.6)';for(let i=0;i<6;i++){ctx.fillRect(165+((t*40+i*13)%30),-28+((t*30*sp+i*7)%14),3,3)}}
 if(d.id==='separator'){ctx.save();ctx.translate(180,-56);ctx.rotate(t*4*sp);ctx.strokeStyle='#3ad0ff';ctx.lineWidth=3;for(let i=0;i<3;i++){ctx.rotate(2.094);ctx.beginPath();ctx.arc(0,0,26,0,1.2);ctx.stroke()}ctx.restore();
  ctx.globalAlpha=.25+.2*Math.sin(t*3);ctx.fillStyle='#7ff3ff';ctx.beginPath();ctx.arc(180,-56,14,0,7);ctx.fill();ctx.globalAlpha=1}
 if(d.id==='packing'){for(let i=0;i<5;i++){const x=((t*30*sp+i*70)%340)+10;loadedCrate(ctx,x,-30,1.1,t+i*.3)}}}
// ----- elevator -----
function elevState(bi){return elev[bi]||(elev[bi]={pos:0,from:0,to:0,t0:0,dur:0,phase:'hold',hold:1,doors:1,riders:1})}
function elevTick(bi,n,dt){const e=elevState(bi);const close=0.333,open=0.333;
 if(e.phase==='hold'){e.hold-=dt;e.doors=Math.min(1,e.doors+dt/open);if(e.hold<=0&&n>1){e.phase='closing'}}
 else if(e.phase==='closing'){e.doors-=dt/close;if(e.doors<=0){e.doors=0;e.from=e.pos;let to=e.forced!=null?e.forced:Math.floor(Math.random()*n);if(to===e.pos)to=(to+1)%n;e.forced=null;e.to=to;e.t0=T;e.dur=(CFG.elevator.travelBaseMs+CFG.elevator.travelPerFloorMs*Math.abs(to-e.from))/1000/elevSpeedMul(bi);e.phase='travel';e.riders=1+Math.floor(Math.random()*Math.min(3,elevCap(bi)))}}
 else if(e.phase==='travel'){const q=Math.min(1,(T-e.t0)/e.dur);e.pos=e.from+(e.to-e.from)*easeInOutCubic(q);if(q>=1){e.pos=e.to;e.phase='settle';e.t0=T}}
 else if(e.phase==='settle'){if(T-e.t0>0.31){e.phase='hold';e.hold=1.2+Math.random()*1.5}}
 if(e.phase==='settle'&&T-e.t0>0.15)e.doors=Math.min(1,e.doors+dt/open)}
function drawShaftStatic(c,bi,n){const top=floorBottom(n-1)-120;for(let k=0;k<n;k++){const y=floorBottom(k)-120;if(ok('el_shaft_tile'))c.drawImage(SPR.el_shaft_tile.img,160,y,40,120);if(ok('el_cable_tile'))c.drawImage(SPR.el_cable_tile.img,178,y,4,120)}
 if(ok('el_shaft_top'))c.drawImage(SPR.el_shaft_top.img,160,top-30,40,30)}
function drawCar(bi,n){const e=elevState(bi),look=elevLook(bi);
 for(let k=0;k<n;k++)spr(ctx,'el_call_panel',Math.abs(e.pos-k)<0.05?1:0,162,floorBottom(k)-60);
 if(!ensureLook(look))return;const settle=e.phase==='settle'?2*Math.sin(Math.min(1,(T-e.t0)/0.16)*Math.PI)*(1-Math.min(1,(T-e.t0)/0.31)):0;
 const y=floorBottom(0)-16-e.pos*120+settle,x=180;ctx.drawImage(SPR['car_'+look+'_back'].img,x-17,y-56,34,56);
 const r=Math.min(e.riders,3);if(ok('el_rider'))for(let i=0;i<(elevCap(bi)>3?2:r);i++)ctx.drawImage(SPR.el_rider.img,x-17+8+i*5,y-56+52-16,9,16);
 if(elevCap(bi)>3&&ok('el_capacity_badge')){ctx.drawImage(SPR.el_capacity_badge.img,x+1,y-56,16,10);ctx.fillStyle='#fff';ctx.font='800 7px Inter,sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(elevCap(bi),x+9,y-51)}
 spr(ctx,'car_'+look+'_doors',Math.round(e.doors*7),x,y)}
// ----- tower cache (static footing + shaft + floor bases) -----
const towerCache={};let cacheHits=0;
function towerKey(bi,n){const fl=BUILDINGS[bi].floors;let k=[DPR,SC,TS,n,E.power<0.999].join('|');for(let i=0;i<n;i++){const d=fl[i],f=S.f[d.id];k+='|'+tierOf(f.lvl)+(SPR['f_'+d.id]&&SPR['f_'+d.id].ready?'a':'p')+tierLayers(d,f).length}return k}
function towerNeedsLive(bi,n){const fl=BUILDINGS[bi].floors;for(let i=0;i<n;i++){const fx=floorFx[fl[i].id]||{};if(fx.build!=null&&T-fx.build<0.7||fx.up!=null&&T-fx.up<0.45||fx.tap!=null&&T-fx.tap<0.2||fx.tierDrop&&T-fx.tierDrop.t<0.5)return true}return false}
function getTowerCache(bi,n){const key=towerKey(bi,n);let c=towerCache[bi];if(c&&c.key===key)return c;
 const s=DPR*SC*TS,top=Math.floor((floorBottom(n-1)-160)*s)/s,w=420,h=Math.ceil((50-top)*s)/s;
 const cv2=document.createElement('canvas');cv2.width=Math.ceil(w*s);cv2.height=Math.ceil(h*s);const x=cv2.getContext('2d');smooth(x);x.setTransform(s,0,0,s,w/2*s,-top*s);
 spr(x,'base400',0,0,-FOOT_MID+44);drawShaftStatic(x,bi,n);
 const fl=BUILDINGS[bi].floors;for(let i=0;i<n;i++){x.save();x.translate(FX0,floorBottom(i));floorStatic(x,fl[i],S.f[fl[i].id]);x.restore()}
 return towerCache[bi]={key,cv:cv2,top,w,h}}
function drawTower(bi,n,atRest){const fl=BUILDINGS[bi].floors,live=!atRest||towerNeedsLive(bi,n);
 if(!live){const c=getTowerCache(bi,n);ctx.drawImage(c.cv,-c.w/2,c.top,c.w,c.h);cacheHits++}
 else{spr(ctx,'base400',0,0,-FOOT_MID+44);drawShaftStatic(ctx,bi,n)}
 for(let k=0;k<n;k++){const d=fl[k],f=S.f[d.id];ctx.save();ctx.translate(FX0,floorBottom(k));
  if(live){const [sx,sy]=floorScale(floorFx[d.id]||{});ctx.scale(sx,sy);floorStatic(ctx,d,f)}floorAnim(d,f,k);ctx.restore()}
 drawCar(bi,n);
 const nf=fl[n],yTop=floorBottom(n);
 if(nf&&n<CFG.maxFloors){ctx.save();ctx.globalAlpha=.55;ctx.setLineDash([8,6]);ctx.lineWidth=2;ctx.strokeStyle='#8fa3c4';ctx.strokeRect(FX0+4,yTop-116,352,112);ctx.restore();
  const why=lockReason(IDX[nf.id]);pillBtn(FX0+180,yTop-66,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(FX0+180,yTop-32,'🔒 '+why,'#ffb347',13)}}
// ----- Mine launch pad + starter ship -----
const shipAnim={mode:null,t0:0};
const PADX=40;   // mine_pad centre in the pad stop (local pt)
function roverAt(t){   // MINE_SPEC loop ≈10 s: bay → dig (3 s @24pt/s) → scoop 1.33 s → to hopper → dump 1.33 s → back to bay
 const BAY=-300,DIG=BAY+72,HOP=-150,DUMPX=HOP+58,v=24,t1=3,t2=t1+1.333,t3=t2+(DUMPX-DIG)/v*0.5,t4=t3+1.333,t5=t4+(DUMPX-BAY)/v*0.5,c=t%t5;
 if(c<t1)return{x:BAY+v*c,k:'rover_drive',f:fr('rover_drive',c),flip:false};
 if(c<t2)return{x:DIG,k:'rover_scoop',f:Math.min(15,frOnce('rover_scoop',c-t1)),flip:false,dig:c-t1};
 if(c<t3)return{x:DIG+(DUMPX-DIG)*(c-t2)/(t3-t2),k:'rover_drive',f:fr('rover_drive',c),flip:false};
 if(c<t4)return{x:DUMPX,k:'rover_dump',f:Math.min(15,frOnce('rover_dump',c-t3)),flip:false,dump:c-t3};
 return{x:DUMPX-(DUMPX-BAY)*(c-t4)/(t5-t4),k:'rover_drive',f:fr('rover_drive',c),flip:true}}
const surfY=x=>{const X=x*TS;return(R-Math.sqrt(R*R-X*X))/TS-FOOT_MID+8};   // globe surface in pad-stop local pt
function drawPad(bi,atRest){const open=floorsBuilt(bi)>0;
 if(!open){spr(ctx,'site',fr('site',T),0,-6);label(0,-112,'Mine Launch Pad','#c9d3e6',15);label(0,-93,'🔒 Opens with the Mine','#ffb347',13);return}
 const sc=1,padY=surfY(PADX);   // pad, ship, rover and boxes at their spec sizes
 // hopper + rover (works only while the Rover Bay is staffed and powered)
 const hx=-150;spr(ctx,'surface_hopper',0,hx,surfY(hx)+2,sc,sc);
 if(S.f.rover.workers>0){const r=roverAt(T*(E.power<0.999?0.5:1)*Math.min(1.6,1+S.f.rover.lvl*0.02));ctx.save();ctx.translate(r.x,surfY(r.x)+2);if(r.flip)ctx.scale(-1,1);spr(ctx,r.k,r.f,0,0,sc,sc);ctx.restore()}
 ctx.save();ctx.translate(PADX,padY);ctx.scale(sc,sc);
 spr(ctx,'mine_pad',fr('mine_pad',T),0,0);
 // CARGO STAGE x 118–172, deck y=10 → stack3 pivot at (147,10) in pad-image coords
 const toPad=(x,y)=>[x-90,y-36],full=Math.floor(S.crates/3),rem=S.crates%3;
 const [cx,cy]=toPad(147,10);for(let i=0;i<Math.min(full,4);i++)spr(ctx,'loaded_box_stack3',fr('loaded_box_stack3',T+i*.3),cx,cy-i*44);
 if(rem&&full<4)for(let j=0;j<rem;j++)spr(ctx,'loaded_box_pulse',fr('loaded_box_pulse',T+j*.4),cx-15+j*30,cy-Math.min(full,4)*44);
 ctx.restore();
 if(full>4){for(let i=4;i<Math.min(full,10);i++){const x=PADX+90*sc+20+((i-4)%3)*40,y=surfY(x)-Math.floor((i-4)/3)*30;spr(ctx,'loaded_box_stack3',fr('loaded_box_stack3',T+i*.3),x,y,0.7*sc,0.7*sc)}}
 const s=S.ship,[sx0,sy0]=[PADX+(62-90)*sc,padY+(10-36)*sc];let y=sy0,sx=1,sy=1,jx=0,flame=0,vis=s.st!=='trip';const a=shipAnim,t=T-a.t0;
 if(a.mode==='launch'){vis=true;if(t<0.4){const q=t/0.4;sy=1-0.06*Math.sin(q*Math.PI);sx=1+0.04*Math.sin(q*Math.PI);jx=(Math.floor(t/0.04)%2?1.5:-1.5);flame=1;if(!a.smoke){a.smoke=1;padFx('smoke_plume')}}
  else if(t<1.9){const q=(t-0.4)/1.5;y=sy0-1100*q*q;flame=1}else{a.mode=null;vis=false}}
 if(a.mode==='land'){vis=true;if(t<1.8){const q=t/1.8;y=sy0-1100*(1-easeOutCubic(q));flame=t>1.5?(1.8-t)/0.3:1}
  else if(t<2.13){const q=(t-1.8);sy=q<0.08?0.95:1;y=sy0-4*Math.sin(Math.min(1,(q-0.08)/0.25)*Math.PI);if(!a.dust){a.dust=1;padFx('dust_puff')}}else a.mode=null}
 if(vis&&ok('ship')){ctx.save();ctx.translate(sx0+jx,y);ctx.scale(sx,sy);if(flame>0&&ok('ship_flame')){ctx.globalAlpha=Math.max(0,Math.min(1,flame));spr(ctx,'ship_flame',fr('ship_flame',T),0,-24);ctx.globalAlpha=1}spr(ctx,'ship',fr('ship',T),0,0);ctx.restore()}
 FX.filter(o=>o.type==='pad').forEach(o=>{const q=frOnce(o.key,T-o.t);if(SPR[o.key]&&q<SPR[o.key].n)spr(ctx,o.key,q,sx0,sy0+6)});
 if(s.st==='docked'&&a.mode!=='launch'){const n=Math.min(CFG.ship.holdCrates,S.crates);pillBtn(0,-330,n?`🚀 Launch ${n} crate${n>1?'s':''} · ${fmt(n*crateWorth())}`:'Waiting for LOADED crates',n>0)}
 else if(s.st==='trip')label(0,-330,`🚀 To Earth: ${mmss((s.t/1000+CFG.ship.tripSec-gnow()/1000)/SPEED)} · ${s.cargo} crates`,'#eaf2ff',15);
 else if(s.st==='turn')label(0,-330,`🔧 Turnaround ${mmss((s.t/1000+CFG.ship.turnaroundSec-gnow()/1000)/SPEED)}`,'#eaf2ff',15);
 label(0,-300,`Pad: ${S.crates}/${CFG.econ.padCrateCap} LOADED crates · ${num(E.mine||0)}/min`,'#bfe9ff',12)}
function padFx(key){FX.push({type:'pad',key,t:T})}
function easeOutBack(t,c1=1.70158){const c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)}
const easeOutCubic=t=>1-Math.pow(1-t,3),easeInOutCubic=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
// =====================================================================
// FX (positions in tower-local coords of a stop, so they ride the rotation)
// =====================================================================
const FX=[];
function stopXf(si){const f=stopFrame(si);return f}
function withStop(si,fn){const f=stopFrame(si);if(Math.abs(f.a)>0.9)return;ctx.save();ctx.translate(f.x,f.y);ctx.rotate(f.a);ctx.scale(TS,TS);fn();ctx.restore()}
function pop(si,x,y,key,txt,delay=0){FX.push({type:'pop',si,x,y,key,txt,t:T+delay})}
function floorPt(d,x,y){return{si:stopOfTower(d.b),x:FX0+x,y:floorBottom(d.k)-120+y}}
function drawFX(){for(let i=FX.length-1;i>=0;i--){const o=FX[i],t=T-o.t;if(t<0)continue;let done=false;
 if(o.type==='pad'){if(t>3)done=true}
 else if(o.type==='pop'){const D=o.rise||0.6;done=t>D+0.5;withStop(o.si,()=>{if(t<D){const q=t/D,sc=t<0.18?0.6+0.5*(t/0.18):(t<0.28?1.1-0.1*((t-0.18)/0.1):1);
   ctx.globalAlpha=t>D-0.15?(D-t)/0.15:1;const y=o.y-(o.dist||28)*easeOutCubic(q);spr(ctx,o.key+'_spin',fr(o.key+'_spin',t),o.x,y,sc,sc);
   if(o.txt){ctx.font='700 15px Rajdhani,Inter,system-ui,sans-serif';ctx.textAlign='left';ctx.textBaseline='middle';ctx.lineWidth=3;ctx.strokeStyle='rgba(0,0,0,.6)';ctx.strokeText(o.txt,o.x+13,y);ctx.fillStyle=o.key==='coin'?'#ffd34d':'#eaf2ff';ctx.fillText(o.txt,o.x+13,y)}ctx.globalAlpha=1}
  else{const q=frOnce(o.key+'_sparkle',t-D);spr(ctx,o.key+'_sparkle',q,o.x,o.y-(o.dist||28))}})}
 else if(o.type==='sprite'){const q=frOnce(o.key,t);done=!SPR[o.key]||!SPR[o.key].ready||q>=SPR[o.key].n*(o.loops||1);if(!done)withStop(o.si,()=>spr(ctx,o.key,q,o.x,o.y))}
 else if(o.type==='banner'){done=t>1.35;withStop(o.si,()=>{if(!ok(o.key))return;const s=t<0.15?0.6+0.48*(t/0.15):t<0.25?1.08-0.08*((t-0.15)/0.1):1;ctx.globalAlpha=t>1.15?Math.max(0,(1.35-t)/0.2):1;
   ctx.save();ctx.translate(o.x,o.y);ctx.scale(s,s);ctx.drawImage(SPR[o.key].img,-110,-22,220,44);ctx.restore();ctx.globalAlpha=1})}
 else if(o.type==='arrive'){done=t>4.5;withStop(o.si,()=>drawArrive(o,t))}
 if(done)FX.splice(i,1)}}
// new resident: car doors → hiss → walk out → wave → sparkle → people + stipend icons
function residentArrives(){const si=stopOfTower(0);const e=elevState(0);if(e.phase==='hold'&&Math.abs(e.pos)<0.01)e.hold=Math.max(e.hold,2);else e.forced=0;
 FX.push({type:'arrive',si,t:T+(e.pos>0.01?1.6:0),x:180,y:floorBottom(0)-16})}
function drawArrive(o,t){const ex=o.x-17;
 if(t>0.15&&t<0.68)spr(ctx,'fx_door_hiss',frOnce('fx_door_hiss',t-0.15),ex,o.y-8,-1,1);
 let ax=ex,key='idle_worker',f=0,flip=true;if(t>=0.4&&t<0.9){ax=ex-18*easeOutCubic((t-0.4)/0.5);key='walk_worker';f=fr(key,t)}else if(t>=0.9){ax=ex-18;if(t<1.73){key='wave_worker';f=Math.min(9,frOnce('wave_worker',t-0.9))}else if(t<2.2){key='idle_worker';f=fr(key,t)}else{ax=ex-18-40*(t-2.2);key='walk_worker';f=fr(key,t)}}
 if(t>=0.3){ctx.save();ctx.globalAlpha=t>4?Math.max(0,(4.5-t)/0.5):1;ctx.translate(ax,o.y);if(flip&&key!=='wave_worker')ctx.scale(-1,1);spr(ctx,key,f,0,0);ctx.restore();ctx.globalAlpha=1}
 if(t>0.95&&t<1.6)spr(ctx,'fx_welcome_sparkle',frOnce('fx_welcome_sparkle',t-0.95),ex-18,o.y-48);
 if(t>1.0&&!o.p1){o.p1=1;FX.push({type:'pop',si:o.si,x:ex-18,y:o.y-50,key:'pickup_people',txt:'+1',t:T,rise:0.7,dist:30})}
 if(t>1.15&&!o.p2){o.p2=1;FX.push({type:'pop',si:o.si,x:ex+2,y:o.y-44,key:'coin',txt:'+'+fmt(CFG.econ.stipendPerResident*60)+'/min',t:T,rise:0.7,dist:10})}
 if(t>1.6&&!o.p3){o.p3=1;tickMeter('people');tickMeter('coin')}}
function stipendFx(v){const bi=STOPS[site].kind==='tower'?STOPS[site].bi:-1;if(bi<0)return;const fl=BUILDINGS[bi].floors.filter(d=>S.f[d.id].built&&(crew[d.id]||[]).length);if(!fl.length)return;
 const d=fl[Math.floor(Math.random()*fl.length)],a=crew[d.id][0],p=floorPt(d,a.x,104-46);pop(p.si,p.x,p.y,'coin','+'+fmt(v))}
function tickMeter(k){const el=document.querySelector(`.m[data-k="${k}"]`)||(k==='coin'?$('#money'):null);if(!el)return;el.classList.remove('tick');void el.offsetWidth;el.classList.add('tick')}
// =====================================================================
// ACTIONS
// =====================================================================
function bump(){const m=$('#money');m.classList.add('bump');setTimeout(()=>m.classList.remove('bump'),160)}
function buyFloor(i){const d=F[i];if(lockReason(i))return false;S.money-=d.cost;const f=st(i);f.built=true;f.lvl=1;if(idleResidents()>0)f.workers=1;
 ensureBuildingArt(d.b);(floorFx[d.id]=floorFx[d.id]||{}).build=T;const p=floorPt(d,0,120);FX.push({type:'sprite',key:'fx_floor_unlock',si:p.si,x:p.x,y:p.y,t:T});
 toast(f.workers?`🏗️ ${d.name} built!`:`🏗️ ${d.name} built: needs a resident to staff it`);crewSync();save();hud();return true}
function upgradeN(i,n){let c=0,k=0,lv=st(i).lvl;while(k<n&&lv+k<CFG.maxLevel){const x=upCost(i,lv+k);if(c+x>S.money)break;c+=x;k++}return{k,c}}
function doUpgrade(i,n){const {k,c}=upgradeN(i,n);if(!k)return;const f=st(i),d=F[i],before=f.lvl;S.money-=c;f.lvl+=k;const fx=floorFx[d.id]=floorFx[d.id]||{};fx.up=T;
 const p=floorPt(d,180,60);FX.push({type:'sprite',key:'fx_upgrade_burst',si:p.si,x:p.x,y:p.y,t:T});
 CFG.tierLevels.forEach(L=>{if(before<L&&f.lvl>=L)tierUp(i,L)});crewSync();save();hud();openSheet(i,true)}
function tierUp(i,L){const d=F[i],p=floorPt(d,0,120),fx=floorFx[d.id]=floorFx[d.id]||{};fx.tierDrop={L,t:T};loadGroup('fx2');if(d.id==='oxy')ensureTier(d,L);
 FX.push({type:'sprite',key:'fx_tierup_flash_rays',si:p.si,x:p.x,y:p.y,t:T});FX.push({type:'banner',key:'banner_'+L,si:p.si,x:p.x+180,y:p.y-150,t:T+0.3});
 if(L===50)FX.push({type:'sprite',key:'fx_gold_shimmer',si:p.si,x:p.x,y:p.y,t:T,loops:2});toast(`★ ${d.name}: ${d.tierInfo[L].name}!`)}
const hireCost=i=>Math.round(25*Math.pow(3,st(i).workers));
function hire(i){const f=st(i);if(f.workers>=floorSlots(f)||idleResidents()<1||S.money<hireCost(i))return;S.money-=hireCost(i);f.workers++;crewSync();save();hud();openSheet(i,true);toast('👩‍🚀 Resident assigned')}
function collect(i){const f=st(i),d=F[i];if(f.pend<1)return 0;const v=Math.floor(f.pend);f.pend-=v;S.money+=v;bump();const p=floorPt(d,318,32);pop(p.si,p.x,p.y,'coin','+'+fmt(v));
 FX.push({type:'sprite',key:'fx_collect_sparkle',si:p.si,x:p.x,y:p.y,t:T});return v}
function autoCollect(dt){F.forEach((d,i)=>{const f=st(i);if(d.role==='shop'&&f.lvl>=30&&f.built){f.ac+=dt;if(f.ac>=CFG.autoCollectSec){f.ac=0;collect(i)}}})}
function tapFloor(i){const d=F[i],f=st(i);(floorFx[d.id]=floorFx[d.id]||{}).tap=T;
 if(!f.workers&&idleResidents()>0){f.workers=1;crewSync();toast(`👩‍🚀 A resident now staffs ${d.name}`);save();return}
 if(d.role==='shop'&&f.pend>=1){collect(i);return}
 if(d.res){const p=floorPt(d,180,50);pop(p.si,p.x,p.y,RES[d.res].pick,meter(i).split(': ')[1]||'');if(d.id==='oxy'&&!S.tapped){S.tapped=1;save()}}
 openSheet(i)}
function elevUpgrade(bi){if(elevLvl(bi)>=CFG.elevator.maxLevel||S.money<elevCost(bi))return;const before=elevLook(bi);S.money-=elevCost(bi);S.elev[BUILDINGS[bi].id]++;
 if(elevLook(bi)!==before){loadGroup('fx2');FX.push({type:'sprite',key:'fx_elevator_tierup',si:stopOfTower(bi),x:180,y:floorBottom(0)-0,t:T});toast('🛗 New elevator: '+elevLook(bi).replace('_',' '))}save();hud();openElev(bi)}
// =====================================================================
// SHEET
// =====================================================================
let sheetFor=null,sheetOpenedAt=0,mult=1;const ui=n=>ART+'ui/'+n+'.webp';
const resIcon=d=>d.res==='oxygen'?'ui_icon_oxygen':d.res==='water'?'ui_icon_water':d.res==='energy'?'ui_icon_energy':d.role==='housing'?'ui_icon_people':d.role==='shop'?'ui_icon_coin':'ui_icon_power';
function statRows(i){const d=F[i],f=st(i),lv=f.lvl,{k}=upgradeN(i,mult),nl=Math.min(CFG.maxLevel,lv+Math.max(1,k)),a=rawOut(i,lv),b=rawOut(i,nl),pw=d.use?E.power:1,rows=[];
 const arrow=(x,y)=>`${x} <em>→ ${y}</em>`;
 if(d.res==='oxygen'||d.res==='water'){rows.push(['ui_icon_people','Supports',arrow(Math.floor(a*pw)+' people',Math.floor(b*pw))]);rows.push([resIcon(d),(d.res==='oxygen'?'O₂':'Water')+' output',arrow((a*0.8).toFixed(1)+' kg/h',(b*0.8).toFixed(1)+' kg/h')])}
 if(d.res==='energy'){rows.push(['ui_icon_energy','Energy output',arrow(num(a)+' kW',num(b)+' kW')]);rows.push(['ui_icon_power','Base demand',`${num(E.demand)} kW`+(E.power<1?' <span class="bad">· short</span>':'')])}
 if(d.role==='housing')rows.push(['ui_icon_people','Beds',arrow(Math.floor(a),Math.floor(b))]);
 if(d.role==='shop')rows.push(['ui_icon_income','Income',arrow(fmt(a*Math.floor(S.pop)*60)+'/min',fmt(b*Math.floor(S.pop)*60)+'/min')]);
 if(d.role==='mine')rows.push(['ui_icon_income','Throughput',arrow(num(a*pw)+'/min',num(b*pw)+'/min')]);
 if(d.use)rows.push(['ui_icon_low_power','Power use',`${d.use} kW`+(E.power<1?` <span class="bad">· ${Math.round(E.power*100)}% power</span>`:'')]);
 rows.push(['ui_icon_worker','Crew',`${f.workers} / ${floorSlots(f)}`]);return rows}
function openSheet(i,refresh){const d=F[i],f=st(i),el=$('#sheet'),lv=f.lvl,nt=nextTier(lv),prev=tierOf(lv),b=BUILDINGS[d.b];sheetFor={i};
 const {k,c}=upgradeN(i,mult===999?CFG.maxLevel:mult),one=upCost(i),max=lv>=CFG.maxLevel,can=k>0;
 const need=max?'':fmt(Math.max(0,(mult===1?one:upCost(i))-S.money));
 const slots=floorSlots(f),free=slots-f.workers,hc=hireCost(i),idle=idleResidents();
 const hireWhy=free<=0?(lv<10?'Second station at Lv 10':'All stations staffed'):idle<1?`No idle residents (${E.limit} limit)`:S.money<hc?`Need ${fmt(hc-S.money)} more`:'';
 el.innerHTML=`<div class="grab"></div>
 <div class="hdr"><div class="flash"></div><div class="ico"><img src="${ui(resIcon(d))}"></div><div><h2>${d.name}</h2><div class="sub">${b.full||b.name} · Floor ${d.k+1}</div></div><div class="lv" id="lvb">LV ${lv}</div><button class="x" id="sx">✕</button></div>
 <div class="tierhd"><span>${nt?`NEXT TIER · LV ${nt}`:'MASTERED'}</span><b>${nt?`${lv-prev} / ${nt-prev}`:'50 / 50'}</b></div>
 <div class="track"><i style="width:${lv/CFG.maxLevel*100}%"></i>${CFG.tierLevels.map(L=>`<span class="pip ${lv>=L?'done':''}" style="left:${L/CFG.maxLevel*100}%"></span>`).join('')}</div>
 <div class="pipl">${CFG.tierLevels.map(L=>`<span class="${lv>=L?'done':''}" style="left:${Math.min(97,L/CFG.maxLevel*100)}%">${L}</span>`).join('')}</div>
 ${statRows(i).map(r=>`<div class="srow"><img src="${ui(r[0])}"><span>${r[1]}</span><span class="v">${r[2]}</span></div>`).join('')}
 <div class="hire"><div class="av"><img src="${ui('ui_icon_worker')}"></div><div><b>Assign resident</b><small>+${Math.round(CFG.econ.staffBonus*100)}% output · ${Math.max(0,free)} slot${free===1?'':'s'} free · ${idle} idle</small></div>
  <button id="hb" ${hireWhy?'disabled':''}>${hireWhy||`<img src="${ui('ui_icon_coin')}">${fmt(hc).slice(1)}`}</button></div>
 <div class="ctl"><div class="tog" id="tog"><div class="knob" style="transform:translateX(${[0,41,83][[1,10,999].indexOf(mult)]}px)"></div><span data-m="1" class="${mult===1?'on':''}">x1</span><span data-m="10" class="${mult===10?'on':''}">x10</span><span data-m="999" class="${mult===999?'on':''}">MAX</span></div>
 <button class="up ${can?'glow':''}" id="ub" ${can?'':'disabled'}>${max?'MAX LEVEL':can?`UPGRADE${k>1?' ×'+k:''}<small><img src="${ui('ui_icon_coin')}">${fmt(c).slice(1)}</small>`:`UPGRADE<small>Need ${need} more</small>`}</button></div>
 <div class="tiers">${CFG.tierLevels.map(L=>`<div class="${lv>=L?'done':''}"><b>${lv>=L?'✓':'Lv'} ${L}</b><span><strong>${d.tierInfo[L].name}</strong> · ${d.tierInfo[L].effect}<br><span style="color:var(--dim)">${d.tierInfo[L].art}</span></span></div>`).join('')}</div>
 <div class="desc">${d.desc||''}</div>`;
 $('#sx').onclick=closeSheet;$('#ub').onclick=()=>doUpgrade(i,mult===999?CFG.maxLevel:mult);$('#hb').onclick=()=>hire(i);
 el.querySelectorAll('#tog span').forEach(s=>s.onclick=()=>{mult=+s.dataset.m;openSheet(i,true)});
 if(refresh&&sheetFor&&sheetFor.lastLv!=null&&sheetFor.lastLv<lv){const fl=el.querySelector('.flash');fl.animate([{opacity:.6},{opacity:0}],250);$('#lvb').animate([{transform:'scale(1)'},{transform:'scale(1.3)'},{transform:'scale(1)'}],300)}
 sheetFor.lastLv=lv;if(!refresh){el.classList.add('open');$('#shade').classList.add('on');sheetOpenedAt=performance.now()}}
function openElev(bi){const el=$('#sheet'),lv=elevLvl(bi),max=lv>=CFG.elevator.maxLevel,c=elevCost(bi),can=!max&&S.money>=c,b=BUILDINGS[bi];sheetFor={elev:bi};ensureLook(elevLook(bi));
 const nextLookLv=(Math.floor(lv/CFG.elevator.lookEvery)+1)*CFG.elevator.lookEvery;
 el.innerHTML=`<div class="grab"></div><div class="hdr"><div class="ico"><img src="${ui('ui_arrow_next')}" style="transform:rotate(-90deg)"></div><div><h2>Elevator</h2><div class="sub">${b.full||b.name} · ${elevLook(bi).replace('_',' ')} car</div></div><div class="lv">LV ${lv}</div><button class="x" id="sx">✕</button></div>
 <div class="tierhd"><span>${max?'MAX':'NEW LOOK · LV '+nextLookLv}</span><b>${lv} / ${CFG.elevator.maxLevel}</b></div><div class="track"><i style="width:${lv}%"></i></div><div style="height:8px"></div>
 <div class="srow"><img src="${ui('ui_icon_income')}"><span>Speed</span><span class="v">${elevSpeedMul(bi).toFixed(2)}× <em>→ ${(elevSpeedMul(bi)*CFG.elevator.speedPerLevel).toFixed(2)}×</em></span></div>
 <div class="srow"><img src="${ui('ui_icon_people')}"><span>Capacity</span><span class="v">${elevCap(bi)} <em>→ ${CFG.elevator.baseCapacity+Math.floor((lv+1)/CFG.elevator.capacityEvery)}</em></span></div>
 <div class="srow"><img src="${ui('ui_icon_power')}"><span>Building output</span><span class="v">+${lv-1}% <em>→ +${lv}%</em></span></div>
 <div class="ctl"><button class="up ${can?'glow':''}" id="ub" ${can?'':'disabled'}>${max?'MAX LEVEL':can?`UPGRADE<small><img src="${ui('ui_icon_coin')}">${fmt(c).slice(1)}</small>`:`UPGRADE<small>Need ${fmt(c-S.money)} more</small>`}</button></div>
 <div class="desc">Faster cars move crew between floors: +1% output for every floor in this building per level. +1 capacity every 5 levels, a new car every 10.</div>`;
 $('#sx').onclick=closeSheet;$('#ub').onclick=()=>elevUpgrade(bi);el.classList.add('open');$('#shade').classList.add('on');sheetOpenedAt=performance.now()}
function closeSheet(){sheetFor=null;$('#sheet').classList.remove('open');$('#shade').classList.remove('on')}
$('#shade').onclick=()=>{if(performance.now()-sheetOpenedAt>400)closeSheet()};
let tt=0;function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(tt);tt=setTimeout(()=>t.classList.remove('on'),2200)}
// =====================================================================
// HUD
// =====================================================================
let shownMoney=0;
function hud(){const e=E;$('#mval').textContent=fmt(S.money);$('#rate').textContent=`+${fmt(e.rate*60)}/min`;
 const lim=e.limit,low=e.power<0.999,m=[['people','ui_icon_people',`${Math.floor(S.pop)}/${e.cap}`,lim==='Beds'],['oxygen','ui_icon_oxygen',Math.floor(e.oxygen),lim==='Oxygen'],['water','ui_icon_water',Math.floor(e.water),lim==='Water'],['energy','ui_icon_energy',`${num(e.energy)}/${num(e.demand)}`,lim==='Energy']];
 const box=$('#meters');if(!box.children.length)box.innerHTML=m.map(r=>`<div class="m glass" data-k="${r[0]}"><img src="${ui(r[1])}"><span></span></div>`).join('');
 m.forEach((r,j)=>{const el=box.children[j];el.querySelector('span').textContent=r[2];el.classList.toggle('lim',!!r[3]&&r[0]!=='energy');el.classList.toggle('low',r[0]==='energy'&&low)});
 goalTick();const s=STOPS[site];$('#sname').textContent=s.name.toUpperCase();
 const dots=$('#dots');if(dots.children.length!==STOPS.length)dots.innerHTML=STOPS.map(()=>'<i></i>').join('');[...dots.children].forEach((d,j)=>d.classList.toggle('on',j===site));
 if(sheetFor&&sheetFor.i!=null&&!document.activeElement.closest?.('#sheet')){const k=JSON.stringify([S.money>=upCost(sheetFor.i),Math.floor(S.money/50),st(sheetFor.i).lvl,idleResidents()]);if(k!==sheetFor.k){sheetFor.k=k;openSheet(sheetFor.i,true)}}}
// =====================================================================
// SWIPE HINT (one time)
// =====================================================================
let hintOn=false,hintStart=0;
function hintTick(){if(S.hint||hintOn)return;if(!(siteOpen(1)||siteOpen(2))||sheetFor)return;hintOn=true;hintStart=T;$('#hint').style.display='block'}
function hintDraw(){if(!hintOn)return;const t=T-hintStart,el=$('#hint'),loop=1.6,n=Math.floor(t/loop),q=t-n*loop;
 el.style.top=((HOR-110+OY+cam.y)*SC-30)+'px';const arc=el.querySelector('.arc'),hand=el.querySelector('.hand');
 if(n>=3){const f=Math.max(0,1-(t-3*loop)/0.4);arc.style.opacity=0.6*f;hand.style.opacity=0;if(f<=0)endHint();return}
 arc.style.opacity=q<0.2?q/0.2*0.6:(q<1.2?0.4+0.6*((q-0.2)):0.6);if(q>=0.2&&q<1.2)arc.style.opacity=0.4+0.6*Math.min(1,(q-0.2)/1);
 const p=0.2+0.6*easeInOutCubic(Math.max(0,Math.min(1,(q-0.2)/1))),ang=(p-0.5)*240/760,x=120+760*Math.sin(ang),y=60-760*(1-Math.cos(ang))-30;
 hand.style.opacity=q<0.2?q/0.2:q<1.2?1:Math.max(0,1-(q-1.2)/0.4);hand.style.transform=`translate(${x-10}px,${y-4}px) rotate(${ang}rad)`}
function endHint(){hintOn=false;S.hint=1;$('#hint').style.display='none';save()}
// =====================================================================
// INPUT: axis lock, edge guard, momentum vertical scroll, snap rotation
// =====================================================================
const toLogical=(cx,cy)=>({x:cx/SC-OX,y:cy/SC});
function maxScroll(){const s=STOPS[site];if(s.kind!=='tower')return 0;const n=Math.min(CFG.maxFloors,floorsBuilt(s.bi)+1);const topY=C.y-R+floorBottom(n-1)*TS-140*TS-70;return Math.max(0,-(topY+OY)+170)}
let g0=null;
cv.addEventListener('pointerdown',e=>{if(e.clientX<20||e.clientX>innerWidth-20){g0={edge:true};return}g0={x:e.clientX,y:e.clientY,t:performance.now(),rot0:cam.rot,y0:cam.y,axis:null,hist:[]};cam.anim=null;cam.vy=0},{passive:true});
$('#shade').addEventListener('pointerdown',e=>{g0={x:e.clientX,y:e.clientY,t:performance.now(),rot0:cam.rot,y0:cam.y,axis:null,hist:[],fromShade:true}});
addEventListener('pointermove',e=>{if(!g0||g0.edge)return;const dx=e.clientX-g0.x,dy=e.clientY-g0.y;
 if(!g0.axis&&Math.hypot(dx,dy)>9){g0.axis=Math.abs(dx)>Math.abs(dy)?'x':'y';if(g0.fromShade&&g0.axis==='x')closeSheet();if(g0.fromShade&&g0.axis==='y'){g0=null;return}if(g0.axis==='x'&&hintOn)endHint()}
 if(g0.axis==='x'){cam.rot=g0.rot0-dx/SC/R*1.25;cam.rot=Math.max(-0.15,Math.min((STOPS.length-1)*CFG.rotPerSlot+0.15,cam.rot))}
 if(g0.axis==='y'){cam.y=Math.max(-30,Math.min(maxScroll()+30,g0.y0+dy/SC));g0.hist.push([performance.now(),cam.y]);if(g0.hist.length>6)g0.hist.shift()}},{passive:true});
addEventListener('pointerup',e=>{if(!g0||g0.edge){g0=null;return}const g=g0;g0=null;
 if(g.axis==='x'){const dx=e.clientX-g.x,v=dx/(performance.now()-g.t);let tgt=Math.round(cam.rot/CFG.rotPerSlot);if(Math.abs(v)>0.4&&tgt===site)tgt=site+(v<0?1:-1);goSite(tgt);return}
 if(g.axis==='y'){const h=g.hist;if(h.length>1){const a=h[0],b=h[h.length-1];cam.vy=(b[1]-a[1])/Math.max(16,b[0]-a[0])*1000}return}
 if(!g.fromShade)tap(toLogical(e.clientX,e.clientY))});
function goSite(k){k=Math.max(0,Math.min(STOPS.length-1,k));const from=cam.rot,to=k*CFG.rotPerSlot;cam.anim={from,to,t0:T,d:0.45};if(k!==site){site=k;cam.y=0;cam.vy=0;const s=STOPS[k];if(siteOpen(s.bi))ensureBuildingArt(s.bi)}hud()}
function tap(p){const s=STOPS[site],f=stopFrame(site);const lx=(p.x-f.x)/TS,ly=(p.y-(OY+cam.y)-f.y)/TS;
 if(s.kind==='pad'){if(Math.abs(ly+330)<24&&Math.abs(lx)<150&&S.ship.st==='docked'){if(launchShip()){shipAnim.mode='launch';shipAnim.t0=T;shipAnim.smoke=0;toast('🚀 Cargo away! Back in '+mmss(CFG.ship.tripSec/SPEED))}else toast('No LOADED crates yet: build the Packing floor')}return}
 const bi=s.bi,n=floorsBuilt(bi),fl=BUILDINGS[bi].floors;
 if(n===0){if(siteOpen(bi)&&Math.abs(ly+138)<24&&Math.abs(lx)<160){const nf=nextFloor(bi),i=IDX[nf.id],w=lockReason(i);if(w)toast('🔒 '+w);else buyFloor(i)}else if(!siteOpen(bi))toast(BUILDINGS[bi].soon?'Coming soon':'🔒 Build 3 Life Support floors first');return}
 const k=Math.floor((floorBottom(0)-ly)/120);
 if(lx>=160&&lx<=200&&k>=0&&k<n){openElev(bi);return}
 if(lx>=FX0&&lx<160){if(k>=0&&k<n){tapFloor(IDX[fl[k].id]);return}
  if(k===n&&fl[n]){const i=IDX[fl[n].id],w=lockReason(i);if(w)toast('🔒 '+w);else buyFloor(i)}}}
// =====================================================================
// LOOP
// =====================================================================
let last=performance.now(),saveAcc=0,hudAcc=0,fpsN=0,fpsT=0;
function frame(now){const dt=Math.max(0,Math.min(0.1,(now-last)/1000));last=now;T+=dt;
 if(cam.anim){const a=cam.anim,q=Math.min(1,(T-a.t0)/a.d);cam.rot=a.from+(a.to-a.from)*easeOutCubic(q);if(q>=1){cam.rot=a.to;cam.anim=null}}
 if(!g0&&cam.vy){cam.y+=cam.vy*dt;cam.vy*=Math.pow(0.04,dt);if(Math.abs(cam.vy)<5)cam.vy=0}
 if(!g0||g0.axis!=='y'){const mx=maxScroll();if(cam.y<0){cam.y+=(0-cam.y)*Math.min(1,dt*12);if(cam.y>-0.3)cam.y=0;cam.vy=Math.max(0,cam.vy)}if(cam.y>mx){cam.y+=(mx-cam.y)*Math.min(1,dt*12);cam.vy=Math.min(0,cam.vy)}}
 const gdt=dt*SPEED;step(gdt,true);autoCollect(gdt);
 shipTick(gnow(),true).forEach(ev=>{if(ev.type==='landed'){shipAnim.mode='land';shipAnim.t0=T;shipAnim.dust=0;toast(`🚀 Cargo sold on Earth: +${fmt(ev.v)}`);bump();const si=STOPS.findIndex(s=>s.kind==='pad');pop(si,0,-140,'coin','+'+fmt(ev.v))}if(ev.type==='ready')toast('🚀 Ship ready to load')});
 crewTick(dt);STOPS.forEach((s,si)=>{if(s.kind==='tower'){const n=floorsBuilt(s.bi);if(n&&Math.abs(stopFrame(si).a)<0.9)elevTick(s.bi,n,dt)}});
 render();hintDraw();hudAcc+=dt;if(hudAcc>0.25){hudAcc=0;hud();hintTick();BUILDINGS.forEach((b,bi)=>{if(siteOpen(bi))ensureBuildingArt(bi)})}saveAcc+=dt;if(saveAcc>5){saveAcc=0;save()}
 fpsN++;fpsT+=dt;if(fpsT>1){dbgText(Math.round(fpsN/fpsT));fpsN=0;fpsT=0}
 requestAnimationFrame(frame)}
// offline catch-up
function offline(){const now=Date.now(),away=Math.min(CFG.offlineCapSec,(now-S.rt)/1000*SPEED);let earned=0;const before=S.ship.st;
 if(away>5){let left=away;while(left>0){const ch=Math.min(10,left);earned+=step(ch,false,CFG.offlineRate);left-=ch}}
 S.gt=gnow();S.rt=now;const ev=shipTick(S.gt,false);ev.forEach(e=>{if(e.type==='landed'){earned+=e.v;padFx('dust_puff')}});
 if(earned>=1&&away>30){$('#wbtext').textContent=`Your base ran for ${mmss(away/SPEED)} while you were away.`;$('#wbamt').textContent='+'+fmt(earned);$('#modal').classList.add('on');$('#wbok').onclick=()=>{$('#modal').classList.remove('on');bump()}}
 save()}
// boot
(async function boot(){resize();document.querySelectorAll('img[data-ui]').forEach(im=>im.src=ui(im.dataset.ui));
 const bar=$('#lbar');await Promise.all([loadGroup('core',p=>bar.style.width=(p*80)+'%'),loadGroup('life',p=>{})]);bar.style.width='100%';
 ensureLook(elevLook(0));BUILDINGS.forEach((b,bi)=>{if(siteOpen(bi))ensureBuildingArt(bi)});F.forEach(d=>{if(d.id==='oxy')CFG.tierLevels.forEach(L=>{if(S.f.oxy.lvl>=L)ensureTier(d,L)})});
 offline();econ();crewSync();hud();
 const L=$('#load');L.style.opacity=0;setTimeout(()=>L.remove(),500);requestAnimationFrame(t=>{last=t;frame(t)});
 setTimeout(()=>loadGroup('fx2'),1500)})();
window.__ps={S,F,E:()=>E,econ,step,CFG,goSite,STOPS,SPR,launchShip,buyFloor,doUpgrade,save,cacheHits:()=>cacheHits,elevUpgrade};
