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
 maxFloors:10,siteAngleDeg:60,rotPerSlot:0.25,neighbourSink:0,surfaceScroll:6,towerScale:0.93,
 // money ONLY from mining (+ refining): $500 grant, a small raw-ore trickle until the first ship returns, then cargo sales
 econ:{startGrant:500,arrivalSec:20,leaveSec:10,
  pod:{housing:4,oxygen:0,water:4,energy:8},kwPerPerson:1,staffBonus:0.25,
  ptPerMin:1,hePerMin:1/3,ptValue:40,heValue:160,packShare:0.3,refinedMult:3,stageCap:72,
  oreTrickleSec:16,oreTrickle:3,laterFloorBoost:0.5,boostPer:0.03,depotBoost:0.05},
 elevator:{maxLevel:100,speedPerLevel:1.03,baseCapacity:1,capacityEvery:5,cost:25,costMult:1.12,lookEvery:10,bonusPerLevel:0.01,
  travelBaseMs:220,travelPerFloorMs:90,
  looks:['cage','steel','glass','maglev','cargo','panorama','hauler','twin_deck','neon','platinum','gold_express']},
 ship:{holdCrates:12,tripSec:600,turnaroundSec:60,loadPerMin:6},
 // Cargo Space Dock: 4 upgrade tracks, L1–50, new look every 10 levels
 dock:{maxLevel:50,lookEvery:10,cost:{crane:60,crew:80,pad:150,refuel:100},costMult:1.15,
  craneSpeed:0.04,crewSpeed:0.03,padHoldPer2:1,refuelPerLvl:0.015,refuelMin:0.3},
};
const QS=new URLSearchParams(location.search);
const IS_QA=location.pathname.includes('/qa/')||location.port==='8080',IS_PREVIEW=location.pathname.includes('/preview/')||IS_QA||location.port==='8765';   // /qa/ or the local preview = Playtester build   // dev server counts as preview
const DEV=IS_PREVIEW&&QS.get('dev')==='1';   // ?dev=1 is ignored on the live root
const SPEED=Math.max(0.1,+QS.get('speed')||1),DBG=QS.has('dbg');
// ----- buildings (order on the Moon). Max 10 floors each. -----
const BUILDINGS=[
 {id:'life',name:'Life Support',art:'life',floors:[
  {id:'oxy',name:'Oxygen Plant',art:'oxygen',role:'resource',res:'oxygen',cost:0,out:3,use:1,up:15,desc:'Makes oxygen. More oxygen supports more people.'},
  {id:'water',name:'Water',art:'water',role:'resource',res:'water',cost:120,req:{floor:'oxy',lvl:3},out:4,use:1,up:70,desc:'Makes water. More water supports more people.'},
  {id:'nuke',name:'Nuclear Power',art:'nuclear',role:'resource',res:'energy',cost:150,out:12,use:0,up:110,crew:'engineer',desc:'Makes energy for every floor and every person.'}]},
 {id:'mine',name:'He & Pt Mine',full:'Helium & Platinum Mine',art:'mine',roof:'penthouse_mine',floors:[
  {id:'rover',name:'Rover Bay',art:'mine_rover_bay',pack:'floors_later_offscreen',role:'mine',cost:0,out:1,use:2,up:12,ph:'#5a4a3a',desc:'Rovers drive into ADIT-2, mine regolith and dump it by ore type. Higher levels add speed.'},
  {id:'crusher',name:'Crusher',art:'mine_crusher',pack:'mine_later_crusher',role:'mine',cost:250,out:1,use:1,up:120,ph:'#4a4a5a',desc:'Crushes ore: more crates from every rover load.'},
  {id:'separator',name:'Separator',art:'mine_separator',pack:'mine_later_separator',role:'mine',cost:500,out:1,use:3,up:450,ph:'#2f4a5a',crew:'engineer',desc:'Separates Helium-3 and platinum. Uses a lot of energy.'},
  {id:'packing',name:'Packing',art:'mine_packing',pack:'mine_later_packing',role:'mine',cost:1800,out:1,use:1,up:1600,ph:'#4a3f2a',desc:'Packs Pt crates and He-3 canisters faster.'}]},
 {id:'dock',name:'Cargo Space Dock',dock:true,floors:[]},
 {id:'hab',name:'Habitat',art:'hab',roof:'roof_habitat',floors:[
  {id:'living',name:'Living Quarters',art:'living_quarters',tiers:1,role:'housing',cost:0,out:2,use:2,up:40,desc:'Beds for miners. Sets the population cap.'},
  {id:'hospital',name:'Hospital',art:'hospital',pack:'habitat_rooms',tiers:1,role:'boost',cost:500,out:1,use:2,up:150,ph:'#2f4a5a',desc:'Keeps miners healthy: a small boost to mining.'},
  {id:'cafe',name:'Café',art:'moon_cafe',pack:'habitat_rooms',tiers:1,role:'boost',cost:700,out:1,use:1,up:220,ph:'#4a3a2f',desc:'Coffee under the dome: a small boost to mining.'},
  {id:'markets',name:'Supply Depot',art:'market',pack:'supply_depot',role:'depot',cost:900,out:1,use:2,up:300,desc:'Stores supplies from Earth. Keeps miners happy: +5% mining per level step.'}]},
 {id:'yard',name:'Shipyard',art:'yard',tower:true,needs:{building:'mine',floors:2},floors:[
  {id:'refinery',name:'Refinery',art:'refinery',role:'refinery',cost:2500,out:1,use:3,up:900,ph:'#3a2f4a',desc:'Refines staged cargo: refined containers sell for 3× value.'},
  {id:'assembly',name:'Assembly',art:'ship_assembly',pack:'shipyard_rooms',tiers:1,slots:2,role:'boost',cost:6000,out:1,use:3,up:1800,ph:'#4a2f2a',desc:'Builds ship hull sections (2 floors tall).'},
  {id:'assembly_up',upper:'assembly',name:'Assembly',role:'none',cost:0,out:0,use:0,up:0},
  {id:'parts',name:'Parts',art:'ship_parts',pack:'shipyard_rooms',tiers:1,role:'boost',cost:9000,out:1,use:2,up:2600,ph:'#4a3a2a',desc:'Stores and picks ship parts.'},
  {id:'fuel',name:'Fuel',art:'ship_fuel',pack:'shipyard_rooms',tiers:1,role:'boost',cost:12000,out:1,use:3,up:3600,ph:'#4a2f3a',desc:'Cryogenic fuel for the cargo ships.'}]},
 {id:'eng',name:'Engineering',art:'eng',roof:'roof_engineering',needs:{building:'yard',floors:2},floors:[
  {id:'cnc',tiers:1,name:'CNC',art:'eng_cnc',pack:'engineering_rooms',role:'boost',cost:15000,out:1,use:2,up:4000,desc:'Machines precision parts.'},
  {id:'cad',tiers:1,name:'CAD',art:'eng_cad',pack:'engineering_rooms',role:'boost',cost:20000,out:1,use:1,up:5200,desc:'Designs better equipment.'},
  {id:'cam',tiers:1,name:'CAM',art:'eng_cam',pack:'engineering_rooms',role:'boost',cost:26000,out:1,use:1,up:6800,desc:'Programs the machines.'},
  {id:'print',tiers:1,name:'Print',art:'eng_print',pack:'engineering_rooms',role:'boost',cost:34000,out:1,use:2,up:8800,desc:'3D-prints spare parts.'},
  {id:'chem',tiers:1,name:'Chem',art:'eng_chem',pack:'engineering_rooms',role:'boost',cost:44000,out:1,use:2,up:11000,desc:'Materials and chemistry lab.'},
  {id:'prop',tiers:1,name:'Prop',art:'eng_prop',pack:'engineering_rooms',role:'boost',cost:58000,out:1,use:3,up:15000,desc:'Propulsion lab.'}]},
];
BUILDINGS.forEach(b=>{if(b.floors.length>CFG.maxFloors)throw new Error(b.name+': max 10 floors')});
// camera stops: each building, plus the Mine's starter launch pad between Mine and Habitat
// 6 stops, 60° apart: Life Support, Mine, Cargo Space Dock, Habitat, Shipyard, Engineering
const STOPS=BUILDINGS.map((b,bi)=>({kind:b.dock?'dock':'tower',bi,name:b.full||b.name}));
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
['sky','stars','stars_twinkle','earth'].forEach(n=>def(n,'bg/'+n,'core','img'));
def('base400','world/tower_base_400','core');
// Art's ground strip (later pack). Lives in art/moon/ground/@Nx/, not under ART's @Nx folder. Code ground stays as the first-screen fallback.
def('ground_strip','../ground/'+(DEV_DPR>2?'@3x':'@2x')+'/ground_strip','core','img');
const GSTRIP={tileWidth:1170,groundLineY:44,h:230,t:0};   // JSON values; refreshed from ground_strip.json on load
def('site','world/site_marker','core');
['walk','idle','wave','carry'].forEach(a=>def(a+'_worker','astronaut/astronaut_'+a,'core'));
['walk','idle'].forEach(a=>def(a+'_engineer','astronaut/astronaut_engineer_'+a,'core'));
['coin_spin','coin_sparkle','pickup_o2_spin','pickup_o2_sparkle','pickup_water_spin','pickup_water_sparkle','pickup_energy_spin','pickup_energy_sparkle','pickup_people_spin','pickup_people_sparkle','fx_collect_sparkle','floor_low_power','icon_low_power_blink','fx_door_hiss','fx_welcome_sparkle'].forEach(n=>def(n,'fx/'+n,'core'));def('fx_upgrade_burst','fx/fx_upgrade_burst','fx_later_upgrade_burst');   // later pack (after the first screen); until it loads, upgrades show the floor scale-pop instead
['shaft_tile','shaft_top','shaft_pit','cable_tile','rider','capacity_badge'].forEach(n=>def('el_'+n,'elevator/'+n,'core','img'));
def('el_call_panel','elevator/call_panel','core');def('el_floor_indicator','elevator/floor_indicator','core');
// heavy fx: loaded right after the first screen
['fx_floor_unlock','fx_tierup_flash_rays','fx_gold_shimmer','fx_elevator_tierup'].forEach(n=>def(n,'fx/'+n,'fx2'));
CFG.tierLevels.forEach(L=>def('banner_'+L,'fx/tier_banner_l'+L,'fx2','img'));
// per building floors. Mine + Supply Depot art live in art/moon/mine/, the dock in art/moon/dock/ (packs: ../packs/*.json)
const MINE=`../mine/${DEV_DPR>2?'@3x':'@2x'}/`,DOCK=`../dock/${DEV_DPR*0.65>2.2?'@3x':'@2x'}/`   /* dock is drawn at 0.65: pick the atlas nearest 1:1 device px (3x phone -> 1.95 -> @2x) */;
F.filter(d=>d.art).forEach(d=>{const inMine=d.role==='mine'||d.id==='markets';d.tierBase=inMine?MINE+'floors/tiers/floor_'+d.art:((['oxy','water','nuke','refinery'].includes(d.id)||d.tiers)?'floors/tiers/floor_'+d.art:null);   // others: base art only
 def('f_'+d.id,(inMine?MINE:'')+'floors/floor_'+d.art,d.pack||BUILDINGS[d.b].art,'floor');if(inMine)SPR['f_'+d.id].lowpower=true});
def('mine_preview',MINE+'preview/mine_preview','mine_preview','img');
['truck_pt_drive','truck_he3_drive','rover_bay_dump_still_pt','rover_bay_dump_still_he3'].forEach(n=>def(n,MINE+'rover/'+n,'mine_starter',n.includes('_still_')?'img':undefined));['rover_bay_dump_pt','rover_bay_dump_he3'].forEach(n=>def(n,MINE+'rover/'+n,'mine_later_dump'));   // dump sheets: later pack; the mid-pour still stands in until it loads
def('bin_fill_ore',MINE+'floors/bin_fill_ore','floors_later_offscreen');['rover_tunnel_pt','rover_tunnel_he3'].forEach(n=>def(n,MINE+'rover/'+n,'mine_later_tunnel_trucks'));   // tunnel trucks: later pack (after the first screen)def('bin_fill_ore',MINE+'floors/bin_fill_ore','mine_starter');   // Rover Bay v3 trucks (old rover_* sheets retired)
let BAYROUTE=null;tryJSON(ART+MINE+'rover/rover_bay_route.json').then(j=>BAYROUTE=j);
['loaded_box_pulse','loaded_box_sealed','loaded_box_stack3','he3_canister_pulse','he3_canister_sealed','he3_canister_stack3'].forEach(n=>def(n,MINE+'box/'+n,'mine_starter'));
['pickup_ore','pickup_miner','pickup_refined_coin'].forEach(n=>{def(n+'_spin',MINE+'fx/'+n+'_spin','mine_starter');def(n+'_sparkle',MINE+'fx/'+n+'_sparkle','mine_starter')});
def('tunnel_back',MINE+'tunnel/tunnel_back','mine_starter','floor');def('tunnel_haze',MINE+'tunnel/tunnel_haze','mine_starter','img');def('tunnel_front_lip',MINE+'tunnel/tunnel_front_lip','mine_starter','img');
const WALK=`../shared/walkway/${DEV_DPR>2?'@3x':'@2x'}/`;['walkway_cap','walkway_cap_R','walkway_astro_walk'].forEach(n=>def(n,WALK+n,'walkway'));['walkway_mid','walkway_mid_s','walkway_truss'].forEach(n=>def(n,WALK+n,'walkway','img'));
def('roof_hab','roofs/roof_habitat','roofs','floor');def('roof_eng','roofs/roof_engineering','roofs','floor');
['launch_tower','launch_tower_ship'].forEach(n=>def(n,'roofs/'+n,'roofs','img'));['launch_tower_crew_arm','launch_tower_fuel_arm'].forEach(n=>def(n,'roofs/'+n,'roofs'));   // roofs pack: later load
def('roof_mine',MINE+'floors/penthouse_mine','mine_later_penthouse','floor');SPR.roof_mine.lowpower=true;
// Cargo Space Dock (own station; loads when the player heads to it)
def('dock_base',DOCK+'pad/cargo_space_dock','dock','img');
['crane_gantry','crane_trolley','crane_hook_empty','crane_jib_mast','crane_jib_boom','floodlight_mast','floodlight_cone','dock_sign_neon_base','dock_sign_neon_pad_t10','dock_sign_neon_pad_t20','dock_sign_bloom_base','dock_sign_bloom_pad_t10','dock_sign_bloom_pad_t20'].forEach(n=>def(n,DOCK+'pad/'+n,'dock','img'));
['crane_hook_box','cargo_mule','dock_sign_glow_base','dock_sign_glow_pad_t10','dock_sign_glow_pad_t20'].forEach(n=>def(n,DOCK+'pad/'+n,'dock'));
def('ship4_hull',DOCK+'ship/ship4_hull','dock','img');def('launch_tower4',DOCK+'ship/launch_tower4','dock','img');
['ship4_flame','ship4_engine_glow','ship4_navlights','dust_puff4','smoke_plume4'].forEach(n=>def(n,DOCK+'ship/'+n,'dock'));
['walk','carry','push','wave'].forEach(n=>def('crew13_'+n,DOCK+'crew/crew13_'+n,'dock'));
def('ui_btn_dock_wrench_firsttime',DOCK+'ui/ui_btn_dock_wrench_firsttime','dock');
def('floor_empty','floors/floor_empty','floors_later_empty','img');   // later pack: empty-floor art for unbuilt floors
def('ship4_hatch',DOCK+'ship/ship4_hatch','dock_later_hatch');   // later pack: cargo hatch (0 open → 5 shut), loaded after the first screen
def('walk_medic','astronaut/astronaut_medic_walk','hab');def('idle_medic','astronaut/astronaut_medic_idle','hab');
const IMG_SIZE={rover_bay_dump_still_pt:[90,58,0,58],rover_bay_dump_still_he3:[90,58,0,58],ground_strip:[1170,230,0,0],launch_tower:[360,360,0,360],launch_tower_ship:[360,360,0,360],walkway_mid:[48,64,0,52],walkway_mid_s:[36,64,0,52],walkway_truss:[48,40,24,0],surface_hopper:[60,40,30,40],mine_preview:[390,844,0,0],tunnel_front_lip:[260,130,0,70],tunnel_haze:[260,130,0,70],dock_base:[600,70,300,70],ship4_hull:[320,480,160,480],floor_empty:[360,120,0,120],launch_tower4:[240,500,38,500],
 crane_gantry:[120,200,60,200],crane_trolley:[24,10,12,0],crane_hook_empty:[40,40,20,0],crane_jib_mast:[40,180,20,180],crane_jib_boom:[150,20,10,10],floodlight_mast:[30,150,15,150],floodlight_cone:[160,160,80,0],
 dock_sign_neon_base:[200,48,100,48],dock_sign_neon_pad_t10:[240,48,120,48],dock_sign_neon_pad_t20:[280,48,140,48],dock_sign_bloom_base:[280,40,140,20],dock_sign_bloom_pad_t10:[320,40,160,20],dock_sign_bloom_pad_t20:[360,40,180,20]};
window.__firstBytesMark=0;
const groupState={};
async function tryJSON(p){try{const r=await fetch(p);if(r.ok)return await r.json()}catch(e){}return null}
function getImg1(src){return new Promise(res=>{const im=new Image();im.onload=()=>res(im);im.onerror=()=>res(null);im.src=src})}
async function getImg(src){for(let a=0;a<4;a++){const im=await getImg1(a?src+(src.includes('?')?'&':'?')+'retry='+a:src);if(im)return im;if(a<3)await new Promise(r=>setTimeout(r,400*(a+1)))}return null}   // a failed load (e.g. a 503) is retried 3 times
const bmp=async im=>{if(!im)return null;try{return await createImageBitmap(im)}catch(e){return im}};
let loadedBytes=0;
async function loadSprite(key){const s=SPR[key];if(s.ready||s.loading)return s.loading;
 s.loading=(async()=>{
  if(s.kind==='img'){s.img=await bmp(await getImg(ART+s.path+'.webp'));if(s.img){const dv=s.path.includes('/@2x/')?2:s.path.includes('/@3x/')?3:(DEV_DPR>2?3:2);s.w=s.img.width/dv;s.h=s.img.height/dv;const z=IMG_SIZE[key];if(z){s.w=z[0];s.h=z[1];s.px=z[2];s.py=z[3]}}}
  else if(s.kind==='floor'){const j=await tryJSON(ART+s.path+'.json');if(j){const dir=ART+s.path.replace(/[^/]+$/,'');
    s.base=await bmp(await getImg(dir+j.base));s.pages=await Promise.all(j.layersImages.map(async n=>bmp(await getImg(dir+n))));s.layers=j.layers;s.fps=j.fps;s.n=j.frames;if(s.lowpower)s.lp=await bmp(await getImg(ART+s.path+'_lowpower.webp'))}}
  else{const j=await tryJSON(ART+s.path+'.json');if(j&&!j.meta&&j.image&&j.alpha){const dir=ART+s.path.replace(/[^/]+$/,''),im=await bmp(await getImg(dir+j.image));if(im){const dv=s.path.includes('/@2x/')?2:3;   // glow v2: one image, per-frame alpha, additive
    s.pages=[im];s.img=im;s.frames=j.alpha.map(()=>({page:0,x:0,y:0,w:im.width,h:im.height}));s.n=j.alpha.length;s.fps=j.fps||12;s.w=im.width/dv;s.h=im.height/dv;s.px=j.pivot.x;s.py=j.pivot.y;s.alpha=j.alpha;s.add=j.blend==='add'}}
  else if(j&&j.meta){const m=j.meta,dir=ART+s.path.replace(/[^/]+$/,'');
    s.sc=m.scale||(DEV_DPR>2?3:2);const fz=f=>Object.assign({page:f.page||0,ds:f.drawScale||1},f.frame,f.offset?{ox:f.offset.x,oy:f.offset.y}:{});const nm=s.path.split('/').pop();
    if(m.layers&&m.layers.includes('glow')&&j.frames[nm+'_glow_0']){s.frames=[];for(let i=0;j.frames[nm+'_'+i];i++){const g=j.frames[nm+'_glow_'+i];s.frames.push({layers:[g?Object.assign(fz(g),{lin:1}):null,fz(j.frames[nm+'_'+i])].filter(Boolean)})}}   // 2-layer burst: glow (drawScale 2, linear) under sharp
    else s.frames=Object.values(j.frames).map(fz);s.n=s.frames.length;const d0=Object.values(j.frames)[0];if(d0&&d0.duration&&m.layers)m.fps=1000/d0.duration;s.fps=m.fps||1;s.w=m.logicalFrame.w;s.h=m.logicalFrame.h;s.px=m.pivot.x;s.py=m.pivot.y;s.loop=m.loop!==false;
    s.pages=await Promise.all((m.images||[m.image]).map(async n=>bmp(await getImg(dir+n))));s.img=s.pages[0]}}
  s.ready=!!(s.img||s.base);s.missing=!s.ready})();return s.loading}
let firstScreenDone=false;const laterWait=[];
function loadGroup(g,onTick){if(groupState[g])return groupState[g];if(g==='mine_later_tunnel_trucks'&&DEV&&+QS.get('truckdelay')>0&&!loadGroup.td){loadGroup.td=1;const ms=+QS.get('truckdelay')*1000;return groupState[g]=new Promise(r=>setTimeout(r,ms)).then(()=>{delete groupState[g];return loadGroup(g,onTick)})}   // ?dev=1&truckdelay=N: hold the tunnel trucks N s (no request is made until then, so no cache-busting is needed)
if(!firstScreenDone&&/^(mine_later_|dock_later_hatch$|floors_later_empty$)/.test(g))return groupState[g]=new Promise(r=>laterWait.push(r)).then(()=>{delete groupState[g];return loadGroup(g,onTick)});   // every mine_later_* pack waits for the first screen
const keys=Object.keys(SPR).filter(k=>SPR[k].group===g);let done=0;
 return groupState[g]=Promise.all(keys.map(k=>loadSprite(k).then(()=>{done++;onTick&&onTick(done/keys.length)})))}
// art for a station: its building group plus the pack of every built floor; Mine starter/preview first
function ensureBuildingArt(bi){const b=BUILDINGS[bi];if(b.dock){loadGroup('dock');return}
 if(b.id==='mine'){loadGroup('mine_starter').then(()=>loadGroup('mine_later_tunnel_trucks'))}else if(b.art)loadGroup(b.art);
 b.floors.forEach(d=>{if(d.pack&&S.f[d.id].built)loadGroup(d.pack)});if(b.roof&&floorsBuilt(bi)===b.floors.length)loadGroup(b.id==='mine'?'mine_later_penthouse':'roofs');if(b.tower&&floorsBuilt(bi)===b.floors.length)loadGroup('roofs')}
// tier layers (cumulative): floors/tiers/floor_<art>_t<L>
function tierKey(d,L){return 't_'+d.id+'_'+L}
function ensureTier(d,L){const k=tierKey(d,L);if(!SPR[k]){if(d.pack==='floors_later_offscreen'&&!firstScreenDone)return{};   // Rover Bay tiers are in floors_later_offscreen: never fetched before the first screen
 def(k,`${d.tierBase}_t${L}`,'tier','floor');loadSprite(k)}return SPR[k]}
function ensureLook(look){const kb='car_'+look+'_back',kd='car_'+look+'_doors';if(!SPR[kb]){def(kb,'elevator/'+kb,'look','img');def(kd,'elevator/'+kd,'look');loadSprite(kb);loadSprite(kd)}return SPR[kb].ready&&SPR[kd].ready}
const ok=k=>SPR[k]&&SPR[k].ready;
function spr(c,key,frame,x,y,sx=1,sy=1){const S=SPR[key];if(!S||!S.ready)return;if(!S.frames){c.drawImage(S.img,x-(S.px||0)*sx,y-(S.py||0)*sy,S.w*sx,S.h*sy);return}
 const fi=((frame|0)%S.n+S.n)%S.n,f=S.frames[fi];if(S.alpha){c.save();c.globalAlpha*=S.alpha[fi];if(S.add)c.globalCompositeOperation='lighter';c.drawImage(S.pages[f.page],f.x,f.y,f.w,f.h,x-S.px*sx,y-S.py*sy,S.w*sx,S.h*sy);c.restore();return}if(f.layers){for(const L of f.layers){const k=L.ds/S.sc;c.save();c.globalCompositeOperation='source-over';if(L.lin){c.imageSmoothingEnabled=true;c.imageSmoothingQuality='low'}c.drawImage(S.pages[L.page],L.x,L.y,L.w,L.h,x-S.px*sx+L.ox*k*sx,y-S.py*sy+L.oy*k*sy,L.w*k*sx,L.h*k*sy);c.restore()}return}
 if(f.ox!=null){const k=1/S.sc;c.drawImage(S.pages[f.page],f.x,f.y,f.w,f.h,x-S.px*sx+f.ox*k*sx,y-S.py*sy+f.oy*k*sy,f.w*k*sx,f.h*k*sy);return}c.drawImage(S.pages[f.page],f.x,f.y,f.w,f.h,x-S.px*sx,y-S.py*sy,S.w*sx,S.h*sy)}
const fr=(k,t)=>SPR[k]&&SPR[k].ready?Math.floor(t*SPR[k].fps)%SPR[k].n:0;
const frOnce=(k,t)=>SPR[k]&&SPR[k].ready?Math.floor(t*SPR[k].fps):99;
function drawLayers(c,s,t,paused,h=120){if(!s||!s.ready||!s.layers)return;const gf=paused?0:Math.floor(t*s.fps);
 for(const L of s.layers){const q=L.frames[((gf%L.frames.length)+L.frames.length)%L.frames.length];c.drawImage(s.pages[q.page||0],q.x,q.y,q.w,q.h,L.x,L.y-h,L.w,L.h)}}
// =====================================================================
// SAVE / TIME — everything runs from saved timestamps
// =====================================================================
const SAVEKEY=DEV?(IS_QA?'planetstack-qa-dev':'planetstack-dev'):IS_QA?'planetstack-qa':location.pathname.includes('/preview/')?'planetstack-preview':'planetstack_moon_v2';
if(IS_PREVIEW&&QS.has('fresh')){try{localStorage.removeItem(SAVEKEY)}catch(e){}{const q=new URLSearchParams(location.search);q.delete('fresh');history.replaceState(null,'',location.pathname+'?'+q.toString().replace(/=(?=&|$)/g,''))}}   // ?dev=1&fresh: clean dev save (preview only); normal save untouched   // ?fresh clears THIS build's save (dev or not; preview/qa only)
const noCrew=d=>!!d.res||d.role==='housing'||!!d.upper;   // Life Support + Living Quarters run without crew
function fresh(){const n=Date.now();return{money:CFG.econ.startGrant,pop:3,trips:0,arr:0,pt:0,he:0,refPt:0,refHe:0,ptAcc:0,heAcc:0,refAcc:0,oreAcc:0,firstReturn:0,gt:n,rt:n,step:0,hint:0,tapped:0,wrench:0,
 dock:{crane:1,crew:1,pad:1,refuel:1},
 elev:Object.fromEntries(BUILDINGS.map(b=>[b.id,1])),ship:{st:'docked',t:n,pt:0,he:0,refPt:0,refHe:0,loadAcc:0},
 f:Object.fromEntries(F.map(d=>[d.id,{built:d.cost===0&&!d.upper,lvl:1,workers:d.cost===0&&!noCrew(d)?1:0,pend:0,ac:0}]))}}
function load(){try{const s=JSON.parse(localStorage.getItem(SAVEKEY));if(s&&s.f){F.forEach(d=>{if(noCrew(d)&&s.f[d.id])s.f[d.id].workers=0});   /* migrate: free Life Support / quarters crew to idle */const z=fresh();for(const k in z.f)s.f[k]=Object.assign(z.f[k],s.f[k]);
   F.forEach(d=>{if(d.upper)s.f[d.id].built=!!s.f[d.upper].built});   /* migrate: the Assembly upper slot was 'built' for free on every fresh save, which drew the unbuilt Refinery as a built floor */
   {const r=s.f.refinery;if(r&&!r.built){if(r.lvl>1)r.built=true;else{r.lvl=1;r.workers=0}}}   /* paid upgrades on the ghost Refinery count as built; otherwise it starts unbuilt */
s.elev=Object.assign(z.elev,s.elev);s.ship=Object.assign(z.ship,s.ship);s.dock=Object.assign(z.dock,s.dock);return Object.assign(z,s,{f:s.f})}}catch(e){}return fresh()}
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
const totalWorkers=()=>F.reduce((a,d)=>a+(noCrew(d)?0:S.f[d.id].workers),0);
const idleResidents=()=>Math.max(0,Math.floor(S.pop)-totalWorkers());
const elevLvl=bi=>S.elev[BUILDINGS[bi].id]||1;
const elevSpeedMul=bi=>Math.pow(CFG.elevator.speedPerLevel,elevLvl(bi)-1);
const elevCap=bi=>CFG.elevator.baseCapacity+Math.floor(elevLvl(bi)/CFG.elevator.capacityEvery);
const elevCost=bi=>Math.round(CFG.elevator.cost*Math.pow(CFG.elevator.costMult,elevLvl(bi)-1));
const elevLook=bi=>CFG.elevator.looks[Math.min(CFG.elevator.looks.length-1,Math.floor(elevLvl(bi)/CFG.elevator.lookEvery))];
const crewMul=()=>S.f.oxy.lvl>=20?1+CFG.oxygenCrewSpeed:1;
// output at full power for a given level/crew (people supported · kW · beds · $/resident/s · crates/min)
const MG=Math.pow(10000/(Math.pow(1.25,9)*32),1/40);const mineCurve=lv=>(lv<=10?Math.pow(1.25,lv-1):Math.pow(1.25,9)*Math.pow(MG,lv-10))*Math.pow(CFG.tierMult,tiersReached(lv));   // hybrid (Game Director): L10 ≈14.9×, L50 = 10,000×   // Mine/Refinery: L50 = 312.5 x 2^5 = 10,000x L1 (doublings included)
const procBoost=(d,lv)=>0.5+2.5*(lv-1)/49;   // Crusher/Separator/Packing: +50% at L1 to +300% at L50, summed
function rawOut(i,lv,w){const f=st(i),d=F[i];lv=lv||f.lvl;w=w==null?f.workers:w;if(noCrew(d))w=1;if(!f.built||w<1)return 0;
 if(d.role==='housing'){let x=d.out*growth(lv,CFG.earlyGrowth,CFG.lateGrowth)*Math.pow(CFG.tierMult,tiersReached(lv));return Math.max(Math.floor(x),d.out+lv-1)}   // every level adds at least one bed
 if(d.role==='mine'||d.role==='refinery')return d.out*mineCurve(lv)*(1+CFG.econ.staffBonus*(w-1));   // no extra compounding perks on income floors
 let x=d.out*growth(lv,CFG.earlyGrowth,CFG.lateGrowth)*Math.pow(CFG.tierMult,tiersReached(lv))*(1+CFG.econ.staffBonus*(w-1));
 if(lv>=20&&d.id!=='oxy')x*=1+CFG.tierUtility;if(lv>=30&&d.role!=='shop')x*=1+CFG.tierIndustrial;
 BUILDINGS[d.b].floors.forEach(o=>{if(S.f[o.id].built&&S.f[o.id].lvl>=40)x*=1+CFG.eliteBuilding});
 F.forEach(o=>{if(S.f[o.id].built&&S.f[o.id].lvl>=50)x*=1+CFG.masteredPlanet});
 return x*(1+CFG.elevator.bonusPerLevel*(elevLvl(d.b)-1))}
let E={};
const roomBoost=d=>{if(d.role!=='boost'&&d.role!=='depot')return 0;const f=S.f[d.id];if(!f.built||!f.workers)return 0;return (0.03+0.01*(f.lvl-1))*(d.use?E.power||1:1)};   // +3% at L1, +1%/level, +52% at L50; no tier doubling
const mineFloors=['rover','crusher','separator','packing'];
function econ(){const P=CFG.econ.pod,e={oxygen:P.oxygen,water:P.water,energy:P.energy,housing:P.housing,floorUse:0};
 F.forEach((d,i)=>{if(d.res==='energy')e.energy+=rawOut(i);if(st(i).built&&(st(i).workers>0||noCrew(d)))e.floorUse+=d.use||0});
 const pop=Math.floor(S.pop);e.demand=e.floorUse+pop*CFG.econ.kwPerPerson;e.power=e.demand>0?Math.min(1,e.energy/e.demand):1;
 F.forEach((d,i)=>{const o=rawOut(i)*(d.use?e.power:1);d._out=o;if(d.res==='oxygen')e.oxygen+=o;if(d.res==='water')e.water+=o;if(d.role==='housing')e.housing+=o});
 e.energySupport=Math.max(0,e.energy-e.floorUse)/CFG.econ.kwPerPerson;
 const lim={Beds:e.housing,Oxygen:e.oxygen,Water:e.water,Energy:e.energySupport};
 e.cap=Math.floor(Math.min(...Object.values(lim)));e.limit=Object.keys(lim).reduce((a,k)=>lim[k]<lim[a]?k:a,'Beds');e.lim=lim;
 // mining: Rover Bay sets the base rate; each later floor and the Supply Depot multiply it
 e.procBoost=mineFloors.slice(1).reduce((a,id)=>{const d=F[IDX[id]],f=S.f[id];return a+(d._out>0?procBoost(d,f.lvl)*(d.use?e.power:1):0)},0);let m=F[IDX.rover]._out*(1+e.procBoost);   // processing boosts add, applied once
 e.roomBoost=F.reduce((a,d)=>a+roomBoost(d),0);m*=1+e.roomBoost;   // support rooms: boosts summed additively, applied once (Game Director)
 e.mineMul=m;e.ptRate=m*CFG.econ.ptPerMin;e.heRate=m*CFG.econ.hePerMin;   // containers per minute
 e.refRate=F[IDX.refinery]._out;                                          // refined per minute
 e.ore=S.firstReturn?0:F[IDX.rover]._out*CFG.econ.oreTrickle/CFG.econ.oreTrickleSec;   // $/s
 {const C=CFG.econ,cont=e.ptRate+e.heRate,avg=cont>0?(e.ptRate*C.ptValue+e.heRate*C.heValue)/cont:0,lr=loadRate(),cyc=(tripFor(S.trips||0)+turnSec())/60+holdCap()/Math.max(0.01,lr);
  e.shipPerMin=Math.min(cont,holdCap()/cyc);   // containers the ship can actually deliver per minute
  e.packIncome=cont*avg*C.packShare/60;e.deliverIncome=e.shipPerMin*avg*(1-C.packShare)/60;
  e.refIncome=Math.min(e.refRate,e.shipPerMin)*avg*(C.refinedMult-1)/60;
  e.cargoRate=e.packIncome+e.deliverIncome+e.refIncome}   // $/s you really earn: 30% on every container packed + 70% (and the refined bonus) on what the ship carries
 e.rate=e.ore+e.cargoRate;E=e;return e}
const loose=()=>S.pt+S.he;   // containers on the pad the crane can still pick up
const padPt=()=>S.pt+(S.ship.st==='docked'?S.ship.pt:0),padHe=()=>S.he+(S.ship.st==='docked'?S.ship.he:0);   // loaded-but-not-launched containers still sit on the pad
const staged=()=>padPt()+padHe();   // pad count: leaves only when the ship launches
function step(dt,live,rate=1){const e=econ();let earned=0;
 if(S.pop<e.cap){S.arr+=dt;while(S.arr>=CFG.econ.arrivalSec&&S.pop<e.cap){S.arr-=CFG.econ.arrivalSec;S.pop++;if(live)residentArrives()}}
 else if(S.pop>e.cap){S.arr+=dt;if(S.arr>=CFG.econ.leaveSec){S.arr=0;S.pop=Math.max(e.cap,S.pop-1);if(live)toast(`👋 A miner left: not enough ${e.limit.toLowerCase()}`,e.limit==='Energy'?goNuclear:null)}}else S.arr=0;
 let over=totalWorkers()-Math.floor(S.pop);for(let i=F.length-1;i>=0&&over>0;i--){const f=st(i);while(f.workers>0&&over>0&&!(i===0&&f.workers===1)){f.workers--;over--}}
 for(let i=0;i<F.length&&idleResidents()>0;i++){const f=st(i);if(f.built&&f.workers<1&&!noCrew(F[i])&&!f.off){f.workers=1;if(live){crewSync();toast(`👩‍🚀 A miner now staffs ${F[i].name}`)}}}
 // raw-ore trickle (only until the first ship returns)
 if(e.ore>0){S.oreAcc+=e.ore*dt*rate;const v=CFG.econ.oreTrickle;while(S.oreAcc>=v){S.oreAcc-=v;S.money+=v;earned+=v;if(live)oreFx(v)}}
 // containers staged at the dock
 const cap=padCap();
 if(staged()<cap){S.ptAcc+=e.ptRate*dt/60;S.heAcc+=e.heRate*dt/60;
  const ps=CFG.econ.packShare;while(S.ptAcc>=1&&staged()<cap){S.ptAcc--;S.pt++;const v=CFG.econ.ptValue*ps;S.money+=v;earned+=v}while(S.heAcc>=1&&staged()<cap){S.heAcc--;S.he++;const v=CFG.econ.heValue*ps;S.money+=v;earned+=v}}   // 30% paid when packed
 else{S.ptAcc+=e.ptRate*dt/60;S.heAcc+=e.heRate*dt/60;const ps=CFG.econ.packShare;while(S.ptAcc>=1){S.ptAcc--;const v=CFG.econ.ptValue*ps;S.money+=v;earned+=v}while(S.heAcc>=1){S.heAcc--;const v=CFG.econ.heValue*ps;S.money+=v;earned+=v}}   // pad full: mining never stops, surplus sells locally at the pack share
 // Refinery: upgrades staged containers to refined (He-3 first: worth more)
 if(e.refRate>0){S.refAcc+=e.refRate*dt/60;while(S.refAcc>=1){const he=S.he-S.refHe>0,pt=S.pt-S.refPt>0;if(!he&&!pt){S.refAcc=Math.min(S.refAcc,1);break}S.refAcc--;
   const v=(he?CFG.econ.heValue:CFG.econ.ptValue)*(CFG.econ.refinedMult-1);if(he)S.refHe++;else S.refPt++;if(live)refineFx(v)}}
 // crane: one container moves pad → hold when the roller starts. Leftovers stay on the pad. Launch never adds cargo.
 craneSim(dt);
 return earned}
// ----- dock tracks -----
const DOCK_TRACKS=[
 {id:'crane',name:'Crane speed',icon:'ui_icon_income',looks:{10:'Second gantry G-2',20:'Heavy portal crane PC-1',30:'Ship-to-shore crane',40:'Automated twin-jib',50:'Gold mastery crane'}},
 {id:'crew',name:'Crew size',icon:'ui_icon_worker',looks:{10:'4 more crew spots + mule charger',20:'Crew ready-room',30:'Crew rover',40:'Forklift drones',50:'Gold crew lounge'}},
 {id:'pad',name:'Pad size',icon:'ui_icon_power',looks:{10:'Deck wings: bigger ships',20:'Blast deck + landing ring',30:'Heavy-ship cradle',40:'Deeper trench',50:'Gold edge lights'}},
 {id:'refuel',name:'Refuel & repair',icon:'ui_icon_energy',looks:{10:'LOX 2 + CH₄ 2 tanks',20:'Repair gantry + LOX sphere',30:'Rapid-fill manifold',40:'Robotic repair arms',50:'Gold service tower'}}];
const dockLvl=t=>S.dock[t]||1;
const dockCost=t=>Math.round(CFG.dock.cost[t]*Math.pow(CFG.dock.costMult,dockLvl(t)-1));
const tripMult=n=>n<1?1:n<2?2.5:6;   // hold grows with trip length: 2-min 1x, 5-min 2.5x, 10-min 6x (pay per trip-minute stays level)
// Hammerhead cycle is 7.6 s at crane L1. Each crane tier (every 10 levels) speeds it ~10%.
// Trip length speeds the same crane so a bigger hold still fills in the same time as the first 12 — flag if that should stay a flat 7.6 s.
const CRANE_CYCLE=7.6, CRANE_ROLLER=5.60, CRANE_LATCH=2.00;
function craneTierMul(){return Math.pow(1.1,Math.floor((dockLvl('crane')-1)/10))}
function craneCrewMul(){return 1+CFG.dock.crewSpeed*(dockLvl('crew')-1)}
function craneSpeedMul(){return craneTierMul()*craneCrewMul()*tripMult(S.trips||0)}
function loadRate(){return (60/CRANE_CYCLE)*craneSpeedMul()}
function craneWantsHe(){return S.he>0&&(S.he>=S.pt/3||S.pt===0)}
function craneTakeOne(){const sh=S.ship,he=craneWantsHe();
 if(he){S.he--;sh.he++;if(S.refHe>S.he){S.refHe--;sh.refHe++}}
 else if(S.pt>0){S.pt--;sh.pt++;if(S.refPt>S.pt){S.refPt--;sh.refPt++}}}
function craneSim(dt){const sh=S.ship;
 if(sh.st!=='docked'){sh.craneT=0;return}
 const committed=(sh.craneT||0)>CRANE_LATCH;
 if(!committed&&(loose()<=0||shipLoad()>=holdCap())){sh.craneT=0;return}
 let left=dt*craneSpeedMul(),guard=0;sh.craneT=sh.craneT||0;
 while(left>1e-4&&guard++<40){
  if(sh.craneT>=CRANE_CYCLE)sh.craneT=0;
  if(sh.craneT<CRANE_ROLLER){
   if(sh.craneT<CRANE_LATCH&&(loose()<=0||shipLoad()>=holdCap())){sh.craneT=0;return}
   const to=CRANE_ROLLER-sh.craneT;if(left<to){sh.craneT+=left;return}
   left-=to;sh.craneT=CRANE_ROLLER;if(loose()>0&&shipLoad()<holdCap())craneTakeOne()}
  const toEnd=CRANE_CYCLE-sh.craneT;if(left<toEnd){sh.craneT+=left;return}
  left-=toEnd;sh.craneT=0}}
const holdCap=()=>Math.round((CFG.ship.holdCrates+Math.floor((dockLvl('pad')-1)/2)*CFG.dock.padHoldPer2)*tripMult(S.trips||0));
const padCap=()=>Math.max(CFG.econ.stageCap,holdCap());   // the pad always fits a full hold
const turnSec=()=>CFG.ship.turnaroundSec*Math.max(CFG.dock.refuelMin,1-CFG.dock.refuelPerLvl*(dockLvl('refuel')-1));
const shipLoad=()=>S.ship.pt+S.ship.he;
const cargoValue=o=>(o.pt*CFG.econ.ptValue+o.he*CFG.econ.heValue)*(1-CFG.econ.packShare)+(o.refPt*CFG.econ.ptValue+o.refHe*CFG.econ.heValue)*(CFG.econ.refinedMult-1);
function dockUpgrade(t){if(dockLvl(t)>=CFG.dock.maxLevel||S.money<dockCost(t))return;const before=Math.floor(dockLvl(t)/10);S.money-=dockCost(t);S.dock[t]++;
 if(Math.floor(dockLvl(t)/10)>before){const tr=DOCK_TRACKS.find(x=>x.id===t);toast(`🔧 ${tr.name}: ${tr.looks[dockLvl(t)]||'new look'}`);loadGroup('fx2');if(ok('fx_upgrade_burst'))FX.push({type:'sprite',key:'fx_upgrade_burst',si:stopOfDock(),x:0,y:-60,t:T})}
 save();hud();openDock(true)}
// ----- cargo ship (timestamps) -----
function shipTick(t,live){const s=S.ship,ev=[];
 if(s.st==='trip'&&t>=s.t+tripSec(s)*1000){S.trips=(S.trips||0)+1;const v=shipValue(s);S.money+=v;s.val=null;ev.push({type:'landed',v});s.st='turn';s.t+=tripSec(s)*1000;s.pt=s.he=s.refPt=s.refHe=0;S.firstReturn=1}
 if(s.st==='turn'&&t>=s.t+turnSec()*1000){s.st='docked';s.t+=turnSec()*1000;ev.push({type:'ready'})}
 return ev}
const tripFor=n=>n<1?120:n<2?300:600;   // 1st trip 2 min, 2nd 5 min, then 10 min
const tripSec=s=>s.dur||CFG.ship.tripSec;
const shipValue=s=>s.st!=='docked'&&s.val!=null?s.val:Math.round(cargoValue(s));
function launchShip(){const s=S.ship;if(s.st!=='docked'||shipLoad()<1)return false;padDip=null;s.val=Math.round(cargoValue(s));s.st='trip';s.t=gnow();s.dur=tripFor(S.trips||0);s.craneT=0;armT=T;save();return true}
const SUF=['','K','M','B','T','Qa','Qi','Sx','Sp','Oc','No','Dc'];
function compact(n){n=Math.floor(n);if(n<1000)return String(n);let k=0,v=n;while(v>=999.5&&k<SUF.length-1){v/=1000;k++}if(v>=999.5)return n.toExponential(1).replace('+','');let t=v.toPrecision(3);if(t.includes('.'))t=t.replace(/0+$/,'').replace(/\.$/,'');return t+SUF[k]}   // 3 significant digits, ≤6 chars with $
const fmt=n=>'$'+compact(n);
const num=n=>n<10?n.toFixed(1):compact(n);
const mmss=s=>{s=Math.max(0,Math.ceil(s));return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')};
function lockReason(i){const d=F[i],b=BUILDINGS[d.b];if(b.soon)return 'Coming soon';if(DEV)return null;
 if(b.needs&&!siteOpen(d.b)){const nb=BUILDINGS.find(x=>x.id===b.needs.building);return `Needs ${b.needs.floors} ${nb.name} floors`}
 if(d.req&&S.f[d.req.floor].lvl<d.req.lvl)return `Needs ${F[IDX[d.req.floor]].name.replace(' Plant','')} level ${d.req.lvl}`;
 if(S.money<d.cost)return `Need ${fmt(d.cost-S.money)} more`;return null}
const nextFloor=bi=>BUILDINGS[bi].floors.find(d=>!S.f[d.id].built&&!d.upper);
// meter line shown on each floor
function meter(i){const d=F[i],o=d._out||0;if(!st(i).workers&&!noCrew(d))return 'No crew';
 if(d.res==='oxygen'||d.res==='water')return `supports ${num(o)}`;
 if(d.res==='energy')return `${num(E.energy||0)}/${num(E.demand||0)} kW`;if(d.role==='housing')return `${num(o)} beds`;
 if(d.role==='depot'||d.role==='boost')return `+${Math.round(roomBoost(d)*100)}% mining`;
 if(d.role==='refinery')return `${num(o)} refined/min`;
 if(d.role==='mine')return d.id==='rover'?`${num(E.ptRate||0)} Pt/min`:`+${Math.round(procBoost(d,st(IDX[d.id]).lvl)*100)}% mining`;return ''}
// ----- goals -----
const GOALS=[
 {d:'Swipe to the Mine and tap the Rover Bay',p:()=>S.tapped?1:0},
 {d:'Ship your first cargo from the Cargo Space Dock',p:()=>S.ship.st!=='docked'||S.firstReturn?1:Math.min(.99,shipLoad()/4)},
 {d:`Upgrade the Oxygen Plant to level ${CFG.tutorialLevel}`,p:()=>Math.min(1,(S.f.oxy.lvl-1)/(CFG.tutorialLevel-1))},
 {d:'Build Water',p:()=>S.f.water.built?1:Math.min(.99,S.money/F[IDX.water].cost)},
 {d:'Build Nuclear Power',p:()=>S.f.nuke.built?1:Math.min(.99,S.money/F[IDX.nuke].cost)},
 {d:'Build the Crusher',p:()=>S.f.crusher.built?1:Math.min(.99,S.money/F[IDX.crusher].cost)},
 {d:'Upgrade the Rover Bay to level 10',p:()=>Math.min(1,(S.f.rover.lvl-1)/9)},
 {d:'Build the Separator',p:()=>S.f.separator.built?1:Math.min(.99,S.money/F[IDX.separator].cost)},
 {d:'Open the Shipyard and build the Refinery',p:()=>S.f.refinery.built?1:Math.min(.99,S.money/F[IDX.refinery].cost)},
 {d:'Grow the base: more miners, more cargo',p:()=>1,last:true}];
function goalTick(){let g=GOALS[S.step];if(!g){S.step=GOALS.length-1;g=GOALS[S.step]}
 if(!g.last&&g.p()>=1){S.step++;g=GOALS[S.step];const el=$('#goal');el.classList.add('pop');setTimeout(()=>el.classList.remove('pop'),350);toast('✅ Goal complete!')}
 $('#gd').textContent=g.d;$('#gp').style.width=(g.p()*100)+'%'}
// =====================================================================
// RENDER
// =====================================================================
const cv=$('#cv'),ctx=cv.getContext('2d',{alpha:false});
let W=390,H=844,DPR=DEV_DPR,SC=1,OY=0,OX=0,TS=0.93;
const snap=v=>Math.round(v*DPR*SC)/(DPR*SC);
function smooth(c){c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high'}
const HOR=560,C={x:195,y:HOR},FOOT_MID=13.67,FX0=-200,SPAN=500;   // flat Moon (no globe): ground line at HOR; stations sit SPAN pt apart on one straight pan
function resize(){DPR=DEV_DPR;W=innerWidth;H=innerHeight;cv.width=Math.round(W*DPR);cv.height=Math.round(H*DPR);   // never lowered
 SC=Math.max(0.5,Math.round(W/390*DPR*4)/(4*DPR));if(390*SC>W)SC=Math.floor(W/390*DPR*4)/(4*DPR);
 OX=snap((W/SC-390)/2);OY=snap(H/SC-844);
 TS=Math.round(Math.min(CFG.towerScale,(W/SC-6)/412)*DPR*SC*4)/(4*DPR*SC);   // tower group fits 390 and lands on a clean device-pixel ratio
 smooth(ctx);skyC=null;gK=0;for(const k in towerCache)delete towerCache[k];dbgText()}
addEventListener('resize',resize);
function dbgText(fps){if(!DBG)return;let el=$('#dbg');if(!el){el=document.createElement('div');el.id='dbg';document.body.appendChild(el)}
 el.textContent=`devicePixelRatio ${window.devicePixelRatio}\nDPR used ${DPR}\ncanvas ${cv.width}×${cv.height} (${(cv.width/innerWidth).toFixed(2)}×)\nSC ${SC}  tower ${TS.toFixed(4)}\nart ${ART}${fps?`\nfps ${fps}`:''}`}
const cam={rot:0,y:0,vy:0,anim:null};
let skyC=null;
function skyLayer(){const w=W*DPR|0,h=H*DPR|0;if(skyC&&skyC.width===w&&skyC.height===h)return skyC;skyC=document.createElement('canvas');skyC.width=w;skyC.height=h;const c=skyC.getContext('2d');smooth(c);if(ok('sky'))c.drawImage(SPR.sky.img,0,0,w,h);return skyC}
// ----- stop geometry -----
const stopOfTower=bi=>STOPS.findIndex(s=>s.kind==='tower'&&s.bi===bi);
// cam.rot stays the pan coordinate (one station = CFG.rotPerSlot); a is just the offset from rest, there is no rotation any more
function stopFrame(si){const a=si*CFG.rotPerSlot-cam.rot;return{a,x:C.x+a/CFG.rotPerSlot*SPAN,y:HOR}}
const camX=()=>cam.rot/CFG.rotPerSlot*SPAN;
const floorBottom=k=>-FOOT_MID+4-k*120;
let T=0,dtG=0,site=0;
const floorFx={},crew={},elev={};
function crewSync(){F.forEach((d,i)=>{const f=st(i),arr=crew[d.id]||(crew[d.id]=[]);
 while(arr.length<Math.min(4,f.workers))arr.push({x:40+Math.random()*260,v:(Math.random()<.5?-1:1)*30,idle:0,t:Math.random()*5});arr.length=Math.min(arr.length,f.workers)})}
function crewTick(dt){const m=crewMul();for(const id in crew)for(const a of crew[id]){if(a.idle>0){a.idle-=dt;continue}a.x+=a.v*dt*m;if(a.x<16||a.x>344){a.v=-a.v;a.x=Math.max(16,Math.min(344,a.x))}if(Math.random()<dt*.12)a.idle=1+Math.random()*2}}
function render(){ctx.setTransform(DPR,0,0,DPR,0,0);smooth(ctx);
 ctx.setTransform(DPR*SC,0,0,DPR*SC,Math.round(OX*DPR*SC),0);
 const rx=camX(),sx=((-rx*0.05)%390+390)%390,syy=OY*0.5+cam.y*0.05;
 ctx.drawImage(skyLayer(),-OX,0,W/SC,H/SC);
 ctx.save();ctx.translate(0,syy);if(ok('stars')){ctx.drawImage(SPR.stars.img,sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars.img,sx-390,0,390,844)}
 if(ok('stars_twinkle')){const tw=0.675+0.325*Math.sin(T*Math.PI*2/2.4);ctx.globalAlpha=tw;ctx.drawImage(SPR.stars_twinkle.img,sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars_twinkle.img,sx-390,0,390,844);
  ctx.globalAlpha=1.35-tw;ctx.scale(-1,1);ctx.drawImage(SPR.stars_twinkle.img,-390-sx,0,390,844);if(sx>0.5)ctx.drawImage(SPR.stars_twinkle.img,-sx,0,390,844)}
 ctx.restore();ctx.globalAlpha=1;
 if(ok('earth'))ctx.drawImage(SPR.earth.img,40-rx*0.1,90+OY*0.4+cam.y*0.1+Math.sin(T*Math.PI*2/20)*2,120,120);
 ctx.save();ctx.translate(0,snap(OY+cam.y));
 const vis=STOPS.map((s,si)=>({s,si,f:stopFrame(si)})).filter(o=>Math.abs(o.f.x-195)<760);
 drawGround(rx);
 drawWalkways();   // after the ground so footings sit on it, before every tower so the joints hide behind the walls
 vis.forEach(drawStop);
 drawWalkways(true);
 drawFX();ctx.restore();
 // (old mine_preview overlay removed: while mine_starter loads, the real Mine layout draws with placeholder floors, so nothing snaps)
}
let curStopA=0,armT=-99;
// ----- flat regolith ground (procedural, opaque): tile TW pt wide, repeats while panning. Depth gradient, craters and boulders with hard shadows, strata at the bottom.
const GTW=1000,GTH=330,gC=document.createElement('canvas'),gX=gC.getContext('2d');let gK=0;
function rng(seed){let x=seed>>>0;return()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return(x>>>0)/4294967296}}
// GROUND_LIFT: same gradient shape, every stop scaled so the code ground's average gray matches Art's strip (~147)
const GROUND_LIFT={k:1.13,tint:[1.023,1.000,0.968]};   // x1.13 (GD-approved: on-screen match to the strip; Art's 1.21 was ~7 gray too bright), hue tinted to the strip's average surface colour (150.9,147.5,142.7)
const gLift=h=>{const v=[1,3,5].map(i=>parseInt(h.substr(i,2),16)),l=(v[0]+v[1]+v[2])/3*(window.__gl||GROUND_LIFT.k);return`rgb(${GROUND_LIFT.tint.map(t=>Math.min(255,Math.round(l*t)))})`};
function buildGround(){const k=DPR*SC;if(gK===k)return;gK=k;gC.width=Math.ceil(GTW*k);gC.height=Math.ceil(GTH*k);const c=gX;c.setTransform(k,0,0,k,0,0);smooth(c);
 let g=c.createLinearGradient(0,0,0,GTH);[[0,'#9a9aa0'],[0.08,'#86868d'],[0.55,'#6b6b72'],[0.78,'#55555c'],[1,'#3c3c43']].forEach(([o,h])=>g.addColorStop(o,gLift(h)));c.fillStyle=g;c.fillRect(0,0,GTW,GTH);
 const r=rng(7);
 for(let i=0;i<2600;i++){const y=Math.pow(r(),0.8)*GTH*0.8,x=r()*GTW,s=0.4+r()*1.3*(0.5+y/GTH);c.fillStyle=r()<.5?'rgba(255,255,255,.07)':'rgba(0,0,0,.09)';c.fillRect(x,y,s,s*0.6)}   // regolith grain
 // strata at the bottom edge (wavy bands, darker with depth)
 const st=[[218,'#5e5a57'],[236,'#4f4b49'],[252,'#5a5652'],[268,'#46423f'],[286,'#3e3a38'],[304,'#35322f']];
 st.forEach(([y0,col],j)=>{c.fillStyle=col;c.beginPath();c.moveTo(0,GTH);for(let x=0;x<=GTW;x+=20){c.lineTo(x,y0+Math.sin(x*0.012+j*1.7)*4+Math.sin(x*0.041+j)*1.5)}c.lineTo(GTW,GTH);c.closePath();c.fill();
  c.strokeStyle='rgba(255,255,255,.08)';c.lineWidth=1;c.beginPath();for(let x=0;x<=GTW;x+=20){const yy=y0+Math.sin(x*0.012+j*1.7)*4+Math.sin(x*0.041+j)*1.5;x?c.lineTo(x,yy):c.moveTo(x,yy)}c.stroke()});
 // craters (flattened by perspective), light rim toward the sun (left), hard shadow inside on the left
 const wrap=(fn,x,w)=>{fn(x);if(x-w<0)fn(x+GTW);if(x+w>GTW)fn(x-GTW)};
 for(let i=0;i<34;i++){const y=12+Math.pow(r(),1.3)*190,rad=(5+r()*22)*(0.6+y/220),x=r()*GTW,f=0.32+0.1*y/200;
  wrap(cx=>{c.save();c.translate(cx,y);c.scale(1,f);c.fillStyle='#5d5d64';c.beginPath();c.arc(0,0,rad,0,7);c.fill();
   c.fillStyle='#3d3d44';c.beginPath();c.arc(0,0,rad,0,7);c.arc(rad*0.28,-rad*0.12,rad*0.92,0,7,true);c.fill('evenodd');   // hard inner shadow
   c.strokeStyle='rgba(225,225,230,.55)';c.lineWidth=1.6/f*0.5;c.beginPath();c.arc(0,0,rad+1,Math.PI*0.15,Math.PI*1.05);c.stroke();
   c.strokeStyle='rgba(30,30,36,.5)';c.beginPath();c.arc(0,0,rad+1,Math.PI*1.1,Math.PI*2.1);c.stroke();c.restore()},x,rad+2)}
 // boulders with hard cast shadows to the right
 for(let i=0;i<46;i++){const y=8+Math.pow(r(),1.2)*200,sz=(2+r()*7)*(0.6+y/200),x=r()*GTW;
  wrap(bx=>{c.fillStyle='rgba(20,20,26,.6)';c.beginPath();c.ellipse(bx+sz*1.1,y+sz*0.15,sz*1.5,sz*0.38,0,0,7);c.fill();
   c.beginPath();const n=6;for(let j=0;j<n;j++){const a=j/n*Math.PI*2,rr0=sz*(0.75+((i*7+j*3)%5)/10);const px=bx+Math.cos(a)*rr0,py=y-sz*0.45+Math.sin(a)*rr0*0.7;j?c.lineTo(px,py):c.moveTo(px,py)}c.closePath();
   const bg=c.createLinearGradient(bx-sz,y-sz,bx+sz,y);bg.addColorStop(0,'#b4b4ba');bg.addColorStop(0.55,'#7b7b82');bg.addColorStop(1,'#45454c');c.fillStyle=bg;c.fill()},x,sz*3)}
 // horizon rim: a crisp lighter edge so the ground reads as a solid edge against the sky
 c.fillStyle='rgba(255,255,255,.18)';c.fillRect(0,0,GTW,1.2)}
// ground: code-drawn tile (first-screen fallback) → Art's ground_strip, 200 ms crossfade once loaded.
// The strip's groundLineY sits on HOR, so building pads (y 0 = HOR) and walkway legs (down to HOR) stand on the art's ground line.
// strip fade progress: advances per rAF by the frame's real time, but a long (hitchy) frame counts as at most 34 ms,
// so the 200 ms ramp always spans >= 6 drawn frames and can never pop in one frame. Dev: logs alpha every frame + on-screen readout.
let gsLast=0;function stripTick(now){if(!GSTRIP.t0||GSTRIP.done)return;const dt=gsLast?Math.min(34,now-gsLast):0;gsLast=now;GSTRIP.p=Math.min(1,(GSTRIP.p||0)+dt/200);const a=easeIO(GSTRIP.p);
 if(DEV){(GSTRIP.log=GSTRIP.log||[]).push([Math.round(now),+a.toFixed(3)]);console.log(`[ground strip] t=${Math.round(now-GSTRIP.t0)}ms alpha=${a.toFixed(3)}`);let el=$('#gsa');if(!el){el=document.createElement('div');el.id='gsa';el.style.cssText='position:fixed;left:8px;top:calc(env(safe-area-inset-top) + 230px);z-index:20;font:11px ui-monospace,Menlo,monospace;color:#9ff0ff;background:rgba(0,0,0,.6);padding:4px 6px;border-radius:6px;pointer-events:none;white-space:pre';document.body.appendChild(el)}
  el.textContent='strip α '+GSTRIP.log.slice(-8).map(x=>x[1].toFixed(2)).join(' ');if(GSTRIP.p>=1)setTimeout(()=>el.remove(),3000)}
 if(GSTRIP.p>=1)GSTRIP.done=true}
function drawGround(rx){const S=SPR.ground_strip,fa=GSTRIP.t0?easeIO(GSTRIP.p||0):0,bottom=H/SC-(OY+cam.y)+40;
 if(fa<1){buildGround();ctx.fillStyle='#2f2d2b';ctx.fillRect(-OX-2,HOR+GTH-1,W/SC+4,Math.max(0,bottom-HOR-GTH+1));   // solid rock below the tile
  const ox=-(((rx%GTW)+GTW)%GTW);for(let x=ox-OX;x<W/SC-OX+GTW;x+=GTW){ctx.drawImage(gC,0,0,gC.width,gC.height,Math.floor(x),HOR,GTW+0.5,GTH)}}
 if(fa>0){const TW=GSTRIP.tileWidth,top=HOR-GSTRIP.groundLineY,GH=GSTRIP.h,sc=S.img.width/TW;ctx.save();ctx.globalAlpha=fa;
  ctx.fillStyle='#2e2c2a';ctx.fillRect(-OX-2,top+GH-1,W/SC+4,Math.max(0,bottom-top-GH+1));   // below the strip: same dark rock as its strata edge
  const ox=-(((rx%TW)+TW)%TW);for(let x=ox-OX-TW;x<W/SC-OX+TW;x+=TW){const dx=Math.round(x*SC*DPR)/(SC*DPR);ctx.drawImage(S.img,0,0,S.img.width,S.img.height,dx,top,TW+1/(SC*DPR),GH)}   // device-pixel-snapped, 1 device px overlap: no hairline seams
  ctx.restore()}}
// every building stands on a flat foundation pad with a contact shadow (replaces the curved globe base)
function dockPlinth(){const w=420;ctx.save();ctx.globalAlpha=.5;ctx.fillStyle='#000';ctx.filter='blur(3px)';ctx.beginPath();ctx.ellipse(0,5,w*0.54,7,0,0,7);ctx.fill();ctx.restore();
 const g=ctx.createLinearGradient(0,-26,0,6);g.addColorStop(0,'#5a5f69');g.addColorStop(1,'#3a3d44');ctx.fillStyle=g;ctx.fillRect(-w/2,-26,w,32);ctx.fillStyle='rgba(255,255,255,.12)';ctx.fillRect(-w/2,5,w,1)}   // solid plinth under the dock deck: nothing see-through
function foundation(){const w=440,h=10;ctx.save();ctx.globalAlpha=.55;ctx.fillStyle='#000';ctx.filter='blur(3px)';ctx.beginPath();ctx.ellipse(0,h-1,w*0.54,7,0,0,7);ctx.fill();ctx.restore();
 const g=ctx.createLinearGradient(0,-4,0,h);g.addColorStop(0,'#a3a6ad');g.addColorStop(0.35,'#7d8088');g.addColorStop(1,'#4c4e55');ctx.fillStyle=g;ctx.beginPath();ctx.moveTo(-w/2,h);ctx.lineTo(-w/2+6,-4);ctx.lineTo(w/2-6,-4);ctx.lineTo(w/2,h);ctx.closePath();ctx.fill();
 ctx.fillStyle='rgba(255,255,255,.25)';ctx.fillRect(-w/2+6,-4,w-12,1);ctx.fillStyle='rgba(0,0,0,.25)';for(let x=-w/2+40;x<w/2-20;x+=60)ctx.fillRect(x,-3,1,h+2)}
// flat steel base band under the tower (top strip of tower_base_400; the old curved underside is gone)
function baseBand(c){c.save();c.beginPath();c.rect(-210,-FOOT_MID-2,420,FOOT_MID+2);c.clip();spr(c,'base400',0,0,-FOOT_MID+44);c.restore();c.fillStyle='#3b4252';c.fillRect(-206,-0.5,412,1)}
// glass walkway tubes between neighbouring stations: always visible (no fade), flat ground, caps ~10 pt over each outer wall column,
// tube on support legs down to the regolith. Mine's right end is raised over the truck door; the Dock end sits on its deck.
let DOCK_CAP_DY=-39,MINE_CAP_LIFT=80;
const wkEnd=(si,side)=>{const s=STOPS[si];if(s.kind==='dock')return DOCK_CAP_DY;if(side>0&&BUILDINGS[s.bi].id==='mine')return -52-MINE_CAP_LIFT*TS;return -52};   // tube baseline (grating) relative to the ground
const wkWall=si=>(STOPS[si].kind==='dock'?195:206)*TS;
function leg(x,top,gnd){if(gnd-top<3)return;shadow(x+3,gnd,14,.4);const g=ctx.createLinearGradient(x,0,x+6,0);g.addColorStop(0,'#5b6577');g.addColorStop(.45,'#9aa4b5');g.addColorStop(1,'#4a5364');ctx.fillStyle=g;ctx.fillRect(x,top,6,gnd-top-2);
 ctx.fillStyle='rgba(30,36,48,.55)';for(let y=top+8;y<gnd-6;y+=12)ctx.fillRect(x,y,6,1.5);ctx.fillStyle='#6b7486';ctx.fillRect(x-3,gnd-3,12,3);ctx.fillStyle='#3d4555';ctx.fillRect(x-3,gnd-1,12,1)}
function drawWalkways(capsPass){if(!ok('walkway_mid')||!ok('walkway_cap')||!ok('walkway_cap_R'))return;
 for(let i=0;i<STOPS.length-1;i++){const fa=stopFrame(i),fb=stopFrame(i+1),ax=fa.x+wkWall(i),bx=fb.x-wkWall(i+1);if(bx<-60||ax>450)continue;
  const ea=wkEnd(i,1),eb=wkEnd(i+1,-1),dk=STOPS[i].kind==='dock'||STOPS[i+1].kind==='dock',lift=Math.min(ea,eb)<-60;
  const yy=HOR+(lift?Math.min(ea,eb):dk?DOCK_CAP_DY:-52),ay=yy,by=yy,G=bx-ax,ang=0,IN=10;   // tubes stay level; caps upright
  const x0=-G/2-IN,x1=G/2+IN,span=x1-x0-60,N=Math.max(1,Math.ceil(span/48)),sx=span/(48*N);
  // legs first (behind the glass): world-vertical, every ~48 pt along the run, from the tube underside to the ground
  if(capsPass){ctx.save();ctx.translate((ax+bx)/2,(ay+by)/2);ctx.rotate(ang);spr(ctx,'walkway_cap',fr('walkway_cap',T),x0,0);spr(ctx,'walkway_cap_R',fr('walkway_cap_R',T+0.5),x1,0);ctx.restore();continue}   // caps over the outer wall columns
  const nL=Math.max(1,Math.round(span/56));for(let j=0;j<nL;j++){const u=(j+0.5)/nL,lx=ax+(bx-ax)*u,ly=ay+12;leg(lx-3,ly,HOR)}
  if(lift)for(const ex of [ax-IN+4,bx+IN-10])leg(ex,ay+12,HOR+(ex<(ax+bx)/2?(ea<-60?0:DOCK_CAP_DY+12):(eb<-60?0:DOCK_CAP_DY+12)))   // raised run: legs under both caps (to the ground, or to the dock deck)
  ctx.save();ctx.translate((ax+bx)/2,(ay+by)/2);ctx.rotate(ang);
  const mids=()=>{for(let k=0;k<N;k++)spr(ctx,'walkway_mid',0,x0+30+k*48*sx,0,sx,1)};mids();
  if(ok('walkway_astro_walk')&&span>20){const L=span-10;const per=Math.max(1,L/22*2),q=((T+i*3.1)%per)/per,go=q<.5,u=go?q*2:2-q*2;ctx.save();ctx.translate(x0+35+L*u,0);if(!go)ctx.scale(-1,1);spr(ctx,'walkway_astro_walk',fr('walkway_astro_walk',T),0,0);ctx.restore()}
  ctx.globalAlpha=.35;mids();ctx.globalAlpha=1;ctx.restore()}}
function drawStop(o){const {s,f}=o;curStopA=0;ctx.save();
 ctx.translate(snap(f.x),snap(f.y));   // upright, always
 ctx.scale(TS,TS);const atRest=s.kind==='dock'?Math.abs(f.a)<0.0004:true;   // no rotation: the static tower cache is valid while panning too
 if(s.kind!=='dock')foundation();else dockPlinth();
 if(s.kind==='dock')drawDock(s.bi,atRest);else{const n=floorsBuilt(s.bi);if(n===0)drawSite(s.bi);else drawTower(s.bi,n,atRest);if(BUILDINGS[s.bi].id==='mine')drawMineForeground(f)}
 ctx.restore()}
function label(x,y,txt,col,size){ctx.font=`700 ${size}px Inter,system-ui,-apple-system,sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='rgba(0,0,0,.55)';ctx.fillText(txt,x,y+1);ctx.fillStyle=col;ctx.fillText(txt,x,y)}
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath()}
function chip(x,y,txt,bg,fg,font,sh){ctx.font=font||'700 11px Inter,system-ui,-apple-system,sans-serif';const w=ctx.measureText(txt).width+12;ctx.fillStyle=bg||'rgba(10,14,26,.66)';rr(ctx,x,y,w,17,8);if(sh){ctx.save();ctx.shadowColor='rgba(0,0,0,.55)';ctx.shadowBlur=0;ctx.shadowOffsetY=ctx.getTransform().d;ctx.fill();ctx.restore()}else ctx.fill();ctx.fillStyle=fg||'#eaf2ff';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,x+6,y+9);return w}
function pillBtn(x,y,txt,on){const p=on?1+0.03*Math.sin(T*5):1;ctx.save();ctx.translate(x,y);ctx.scale(p,p);ctx.font='800 15px Rajdhani,Inter,system-ui,sans-serif';const w=ctx.measureText(txt).width+34;
 const g=ctx.createLinearGradient(0,-18,0,18);if(on){g.addColorStop(0,'#ffb347');g.addColorStop(1,'#ff8a2a')}else{g.addColorStop(0,'#3a4560');g.addColorStop(1,'#2a3247')}
 ctx.fillStyle=on?'#a84c0c':'#161b27';rr(ctx,-w/2,-17,w,38,19);ctx.fill();ctx.fillStyle=g;rr(ctx,-w/2,-19,w,36,18);ctx.fill();if(!on){ctx.strokeStyle='#5b667e';ctx.lineWidth=1.5;ctx.stroke()}
 ctx.fillStyle=on?'#3a1600':'#eaf2ff';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(txt,0,0);ctx.restore()}
// unbuilt floor: floor_empty art (later pack) once loaded, dashed frame until then
function emptyFloor(x0,yb){if(ok('floor_empty')){spr(ctx,'floor_empty',0,x0,yb);return}ctx.save();ctx.globalAlpha=.55;ctx.setLineDash([8,6]);ctx.lineWidth=2;ctx.strokeStyle='#8fa3c4';ctx.strokeRect(x0+4,yb-116,352,112);ctx.restore()}
const emptyFloorSite=bi=>siteOpen(bi)&&!BUILDINGS[bi].soon&&nextFloor(bi)&&nextFloor(bi).id==='refinery';
function drawSite(bi){const b=BUILDINGS[bi],open=siteOpen(bi),p=1+0.03*Math.max(0,Math.sin(T*Math.PI*2/1.6));
 if(emptyFloorSite(bi)){const nf=nextFloor(bi),why=lockReason(IDX[nf.id]);   // unbuilt Refinery: same dashed empty-floor frame as other unbuilt floors, button centred on it
  emptyFloor(-180,0);
  label(0,-132,b.full||b.name,'#c9d3e6',15);pillBtn(0,-60,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(0,-26,'🔒 '+why,'#ffb347',13);return}
 spr(ctx,'site',fr('site',T),0,-6,p,p);label(0,-112,b.full||b.name,'#c9d3e6',15);
 if(b.soon)label(0,-93,b.note?`Coming soon · ${b.note}`:'Coming soon','#8fa3c4',12);
 else if(!open){label(0,-93,`🔒 Needs ${b.needs.floors} floors in ${BUILDINGS.find(x=>x.id===b.needs.building).name}`,'#ffb347',13)}
 else{const nf=nextFloor(bi),why=lockReason(IDX[nf.id]);pillBtn(0,-138,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(0,-106,'🔒 '+why,'#ffb347',13)}}
// ----- floors -----
function floorScale(fx){let sx=1,sy=1;
 if(fx.build!=null){const t=(T-fx.build)/0.65;if(t<1){sy=easeOutBack(Math.min(1,t));sx=1+0.04*Math.sin(t*Math.PI)}}
 if(fx.up!=null){const t=(T-fx.up)/0.4;if(t<1){const w=Math.sin(t*Math.PI)*(1-t);sx*=1+0.05*w;sy*=1-0.06*w}}
 if(fx.pop!=null){const t=(T-fx.pop)/0.3;if(t<1){const w=Math.sin(t*Math.PI)*(1-t*0.5);sx*=1+0.08*w;sy*=1+0.08*w}}
 if(fx.tap!=null){const t=(T-fx.tap)/0.16;if(t<1){const w=Math.sin(t*Math.PI);sx*=1-0.015*w;sy*=1-0.03*w}}return[sx,sy]}
// Low power: ONE steady state with hysteresis (was re-picked from E.power every frame + a 12 fps flicker overlay → strobing).
// Goes short when power < 0.99, or < 0.999 for 0.6 s; recovers only after power >= 0.999 for 1.2 s. Dim fades to 60% / back over 400 ms.
const LPS={on:false,k:0,lo:0,hi:0};
// Animated every rAF from the frame timestamp (ms), eased; power is re-read from a fresh econ() each frame (not the game tick), so the restore starts right after the buffer.
let NOW=0;const easeIO=q=>q<.5?2*q*q:1-Math.pow(-2*q+2,2)/2;
function lpTick(dt,now){const p=econ().power;
 if(!LPS.on){LPS.lo=p<0.999?LPS.lo+dt:0;if(p<0.99||LPS.lo>=0.6){LPS.on=true;LPS.hi=0;lpAnim(1,now)}}else{LPS.hi=p>=0.999?LPS.hi+dt:0;if(LPS.hi>=0.6){LPS.on=false;LPS.lo=0;lpAnim(0,now)}}
 const a=LPS.a;if(a){const q=Math.min(1,(now-a.t0)/400);LPS.k=a.from+(a.to-a.from)*easeIO(q);if(DEV){const ms=Math.round(now-a.t0);(LPS.log=LPS.log||[]).push([Math.round(now),ms,+LPS.k.toFixed(3)]);console.log(`[mine dim] t=${ms}ms alpha=${LPS.k.toFixed(3)}`);let el=$('#mda');if(!el){el=document.createElement('div');el.id='mda';el.style.cssText='position:fixed;left:8px;top:calc(env(safe-area-inset-top) + 250px);z-index:20;font:11px ui-monospace,Menlo,monospace;color:#ffd27f;background:rgba(0,0,0,.6);padding:4px 6px;border-radius:6px;pointer-events:none';document.body.appendChild(el)}el.textContent=`mine dim ${LPS.k.toFixed(3)} @${ms}ms`}if(q>=1)LPS.a=null}}
function lpAnim(to,now){LPS.a={from:LPS.k,to,t0:now}}
const lowPower=d=>(d.use||0)>0&&LPS.on;
function tierLayers(d,f){if(!d.tierBase)return[];   // no tier art → base art only (never blank)
const out=[];CFG.tierLevels.forEach(L=>{if(f.lvl>=L){const s=ensureTier(d,L);if(s.ready)out.push({L,s})}});return out}
function floorStatic(c,d,f){if(d.upper)return;const H=d.slots===2?240:120;const s=SPR['f_'+d.id];
 if(s&&s.ready)c.drawImage(s.base,0,-H,360,H);else placeholderStatic(c,d);
 tierLayers(d,f).forEach(o=>{const dt=(floorFx[d.id]||{}).tierDrop;if(!(dt&&dt.L===o.L&&T-dt.t<0.45))c.drawImage(o.s.base,0,-H,360,H)});
 const L=tierOf(f.lvl);if(L&&!tierLayers(d,f).length){const col=CFG.tierColors[CFG.tierLevels.indexOf(L)];c.save();c.strokeStyle=col;c.lineWidth=3;c.globalAlpha=.9;c.strokeRect(2.5,-117.5,355,111);c.restore()}}
// floor labels never hide under the Goal card: if a floor's top is under the HUD band, its label sticks just below the band (within the floor)
let BAND=0;const stickT={};function chipY(H,id){const m=ctx.getTransform();let y=-H+6;if(BAND&&Math.abs(m.b)<=0.01&&m.d>0){const st=(BAND-m.f)/m.d;y=Math.min(Math.max(-H+6,st),-26)}
 const stuck=y>-H+6.5;if(!stuck){delete stickT[id];return{y,a:1,sh:false}}if(stickT[id]==null)stickT[id]=T;return{y,a:Math.min(1,(T-stickT[id])/0.12),sh:true}}   // stuck: same plate + 1 pt shadow, fades in over 120 ms
function floorAnim(d,f,k){if(d.upper)return;const H=d.slots===2?240:120;const s=SPR['f_'+d.id],lp=false,t=T+k*0.3;   // low power never freezes/jumps the ambient layers any more: the ONLY low-power visual is the eased 400 ms dim / _lowpower crossfade (LPS.k)
 if(s&&s.ready){drawLayers(ctx,s,t,lp,H)}else placeholderAnim(d,f,t,lp);
 tierLayers(d,f).forEach(o=>{const dt=(floorFx[d.id]||{}).tierDrop;
  if(dt&&dt.L===o.L&&T-dt.t<0.45){const q=Math.max(0,Math.min(1,(T-dt.t-0.15)/0.26));if(q>0){ctx.save();ctx.globalAlpha=q;ctx.translate(0,-24*(1-easeOutBack(q,1.7)));ctx.drawImage(o.s.base,0,-H,360,H);drawLayers(ctx,o.s,T,lp,H);ctx.restore()}}
  else drawLayers(ctx,o.s,T,lp,H)});
 if(d.id==='rover'&&s&&s.ready)roverBay(s,f,lp);
 if(f.lvl>=50&&ok('fx_gold_shimmer')&&d.id!=='oxy'){spr(ctx,'fx_gold_shimmer',fr('fx_gold_shimmer',T),0,0)}
 if((d.use||0)>0&&LPS.k>0){if(s&&s.lp){ctx.save();ctx.globalAlpha=LPS.k;ctx.drawImage(s.lp,0,-H,360,H);ctx.restore()}   // Art: normal lights drawn once, the floor's _lowpower layer crossfaded over it (alpha 0→1 / 1→0 over 400 ms), no texture swap
  else{ctx.fillStyle=`rgba(4,6,12,${(0.4*LPS.k).toFixed(3)})`;ctx.fillRect(0,-H,360,H)}}   // floors without _lowpower art (Life Support): steady dim to 60%. The single warning lives in the HUD pill
 if(!f.workers&&!noCrew(d)){ctx.fillStyle='rgba(5,8,15,.45)';ctx.fillRect(0,-H,360,H);label(180,-60,(f.off?'No crew · tap, then + to assign':'Needs crew · tap to assign a resident'),'#ffb347',13)}
 const fx=floorFx[d.id]||{};if(fx.up!=null){const q=(T-fx.up)/0.25;if(q<1){ctx.globalAlpha=0.6*(1-q);ctx.fillStyle='#fff';ctx.fillRect(0,-H,360,H);ctx.globalAlpha=1}}
 (crew[d.id]||[]).forEach(a=>{const y=-120+104,role=(d.crew&&ok('walk_'+d.crew))?d.crew:'worker',key=(a.idle>0?'idle_':'walk_')+role;
  ctx.globalAlpha=.25;ctx.fillStyle='#000';ctx.beginPath();ctx.ellipse(a.x,y,6,1.2,0,0,7);ctx.fill();ctx.globalAlpha=1;
  ctx.save();ctx.translate(snap(a.x),y);if(a.v<0)ctx.scale(-1,1);spr(ctx,key,lp&&a.idle<=0?0:fr(key,T+a.t),0,0);ctx.restore()});
 const L=tierOf(f.lvl);let bw=0;const bf='800 11px Inter,system-ui,sans-serif';const cc=chipY(H,d.id),cy=cc.y;ctx.save();ctx.globalAlpha*=cc.a;
 if(L){const bt=(L===50?'🏅 ':'★ ')+d.tierInfo[L].name;ctx.font=bf;bw=ctx.measureText(bt).width+12;chip(352-bw-34,cy,bt,CFG.tierColors[CFG.tierLevels.indexOf(L)],'#1a1205',bf,cc.sh)}   // badge pinned right (clear of the star medal)
 ctx.font='700 11px Inter,system-ui,-apple-system,sans-serif';const maxW=(L?352-bw-34-6:340)-8-12;let txt=`${d.name} ${f.lvl} · ${meter(IDX[d.id])}`;
 if(ctx.measureText(txt).width>maxW){while(txt.length>4&&ctx.measureText(txt+'…').width>maxW)txt=txt.slice(0,-1);txt=txt.trimEnd()+'…'}chip(8,cy,txt,null,null,null,cc.sh);ctx.restore();
}
function coinBubble(x,y,txt){ctx.font='800 12px Rajdhani,Inter,system-ui,sans-serif';const w=ctx.measureText(txt).width+30;ctx.fillStyle='rgba(255,138,42,.95)';rr(ctx,x-w/2,y-11,w,22,11);ctx.fill();
 spr(ctx,'coin_spin',fr('coin_spin',T),x-w/2+12,y,0.8,0.8);ctx.fillStyle='#3a1600';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,x-w/2+22,y+1)}
// ----- Mine placeholders (until the rover/box art arrives) -----
function placeholderStatic(c,d){const g=c.createLinearGradient(0,-120,0,0);g.addColorStop(0,d.ph||'#3a4258');g.addColorStop(1,'#1c2130');c.fillStyle=g;c.fillRect(0,-120,360,120);
 c.fillStyle='#2a3245';c.fillRect(0,-8,360,8);c.fillStyle='#e8a11a';for(let x=0;x<360;x+=24)c.fillRect(x,-8,12,3);
 c.strokeStyle='rgba(255,255,255,.08)';c.lineWidth=1;for(let x=60;x<360;x+=60){c.beginPath();c.moveTo(x,-118);c.lineTo(x,-10);c.stroke()}
 c.fillStyle='#232a3b';c.fillRect(0,-120,360,6);
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
// roof (penthouse): drawn on the highest floor once the building is full; bottom edge = that floor's top
function roofSpr(bi,n){const b=BUILDINGS[bi];if(!b.roof||n<b.floors.length)return null;const s=SPR['roof_'+b.id];return s&&s.ready?s:null}
function roofStatic(c,bi,n){const s=roofSpr(bi,n);if(!s)return;c.drawImage(s.base,FX0,floorBottom(n)-180,360,180)}
function launchTower(bi,n){const b=BUILDINGS[bi];if(!b.tower||n<b.floors.length||!ok('launch_tower'))return;ctx.save();ctx.translate(FX0,floorBottom(n));
 const away=S.ship.st!=='docked',f=away?Math.min(11,Math.floor((T-armT)*12)):0;   // arms swing away once (12f @12fps) when the cargo ship launches
 spr(ctx,'launch_tower_ship',0,0,0);spr(ctx,'launch_tower',0,0,0);spr(ctx,'launch_tower_crew_arm',f,0,0);spr(ctx,'launch_tower_fuel_arm',f,0,0);ctx.restore()}
function roofAnim(bi,n){launchTower(bi,n);const s=roofSpr(bi,n);if(!s)return;ctx.save();ctx.translate(FX0,floorBottom(n));drawLayers(ctx,s,T,false,180);if(s.lp&&LPS.k>0){ctx.globalAlpha=LPS.k;ctx.drawImage(s.lp,0,-180,360,180);ctx.globalAlpha=1}ctx.restore()}
function drawCar(bi,n){const e=elevState(bi),look=elevLook(bi);
 for(let k=0;k<n;k++)spr(ctx,'el_call_panel',Math.abs(e.pos-k)<0.05?1:0,162,floorBottom(k)-60);
 if(!ensureLook(look))return;const settle=e.phase==='settle'?2*Math.sin(Math.min(1,(T-e.t0)/0.16)*Math.PI)*(1-Math.min(1,(T-e.t0)/0.31)):0;
 const y=floorBottom(0)-16-e.pos*120+settle,x=180;ctx.drawImage(SPR['car_'+look+'_back'].img,x-17,y-56,34,56);
 const r=Math.min(e.riders,3);if(ok('el_rider'))for(let i=0;i<(elevCap(bi)>3?2:r);i++)ctx.drawImage(SPR.el_rider.img,x-17+8+i*5,y-56+52-16,9,16);
 if(elevCap(bi)>3&&ok('el_capacity_badge')){ctx.drawImage(SPR.el_capacity_badge.img,x+1,y-56,16,10);ctx.fillStyle='#fff';ctx.font='800 7px Inter,sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(elevCap(bi),x+9,y-51)}
 spr(ctx,'car_'+look+'_doors',Math.round(e.doors*7),x,y)}
// ----- tower cache (static footing + shaft + floor bases) -----
const towerCache={};let cacheHits=0;
function towerKey(bi,n){const fl=BUILDINGS[bi].floors;let k=[DPR,SC,TS,n,!!roofSpr(bi,n)].join('|');for(let i=0;i<n;i++){const d=fl[i],f=S.f[d.id];k+='|'+tierOf(f.lvl)+(SPR['f_'+d.id]&&SPR['f_'+d.id].ready?'a':'p')+tierLayers(d,f).length}return k}
function towerNeedsLive(bi,n){const fl=BUILDINGS[bi].floors;for(let i=0;i<n;i++){const fx=floorFx[fl[i].id]||{};if(fx.build!=null&&T-fx.build<0.7||fx.up!=null&&T-fx.up<0.45||fx.tap!=null&&T-fx.tap<0.2||fx.pop!=null&&T-fx.pop<0.35||fx.tierDrop&&T-fx.tierDrop.t<0.5)return true}return false}
function getTowerCache(bi,n){const key=towerKey(bi,n);let c=towerCache[bi];if(c&&c.key===key)return c;
 const s=DPR*SC*TS,top=Math.floor((floorBottom(n-1)-320)*s)/s,w=420,h=Math.ceil((50-top)*s)/s;
 const cv2=document.createElement('canvas');cv2.width=Math.ceil(w*s);cv2.height=Math.ceil(h*s);const x=cv2.getContext('2d');smooth(x);x.setTransform(s,0,0,s,w/2*s,-top*s);
 baseBand(x);drawShaftStatic(x,bi,n);
 const fl=BUILDINGS[bi].floors;for(let i=0;i<n;i++){x.save();x.translate(FX0,floorBottom(i));floorStatic(x,fl[i],S.f[fl[i].id]);x.restore()}
 roofStatic(x,bi,n);
 return towerCache[bi]={key,cv:cv2,top,w,h}}
function drawTower(bi,n,atRest){const fl=BUILDINGS[bi].floors,live=!atRest||towerNeedsLive(bi,n);
 if(!live){const c=getTowerCache(bi,n);ctx.drawImage(c.cv,-c.w/2,c.top,c.w,c.h);cacheHits++}
 else{baseBand(ctx);drawShaftStatic(ctx,bi,n);roofStatic(ctx,bi,n)}
 for(let k=0;k<n;k++){const d=fl[k],f=S.f[d.id];ctx.save();ctx.translate(FX0,floorBottom(k));
  if(live){const [sx,sy]=floorScale(floorFx[d.id]||{});ctx.scale(sx,sy);floorStatic(ctx,d,f)}floorAnim(d,f,k);ctx.restore()}
 drawCar(bi,n);roofAnim(bi,n);
 const nf=fl[n],yTop=floorBottom(n);
 if(nf&&n<CFG.maxFloors){emptyFloor(FX0,yTop);
  const why=lockReason(IDX[nf.id]);pillBtn(FX0+180,yTop-66,`Build ${nf.name} · ${fmt(nf.cost)}`,!why);if(why)label(FX0+180,yTop-32,'🔒 '+why,'#ffb347',13)}}
// ----- Mine foreground: ADIT-2 cave v3, rover, hopper. One ground line (y=0 here), scale 1 = same scale as the tower.
// Cave sits fully on screen (right), hopper at left; rover rolls in from the Rover Bay (off-screen left).
// Foreground yard: cave sits to the right of the tower, closer (×1.18) so the road, conveyor and attendant read in front of the floors.
const FG={y:78,s:1.18,par:1.12,tunnel:28,hopper:-160};
const ease=q=>q<.5?2*q*q:1-2*(1-q)*(1-q);
// outdoor half of the truck beat: in from the left, down the ADIT-2 ramp, mine, back up, out to the left (never crosses the portal)
const rampPt=u=>({x:FG.tunnel+20+150*u,y:48*u});
let tunnelOk=false;
function roverState(){const {n,c}=truckClock(),kind=truckKind(n+1),top=rampPt(0).x,off=-330;
 if(!tunnelOk&&c<0.2&&ok('rover_tunnel_pt')&&ok('rover_tunnel_he3'))tunnelOk=true;
 if(!tunnelOk)return null;   // tunnel truck pack not loaded yet: the truck waits in the bay (no pop-in)
 if(c<2.2){const e=1-Math.pow(1-c/2.2,3),x=off+(top-45-off)*e;return{x,y:-Math.abs(Math.sin(x*0.2))*0.6*(1-e),k:'truck_'+kind+'_drive',f:Math.floor(c*12)%8,moving:1-e,dir:1,kind}}
 if(c<2.5){const q=(c-2.2)/0.3;return{x:top-45,y:Math.sin(q*Math.PI*2)*1.2*(1-q),k:'truck_'+kind+'_drive',f:0,moving:0,kind}}
 if(c<3.5){const q=(c-2.5),u=q*q*(3-2*q),p=rampPt(u);return{x:p.x,y:p.y,k:'rover_tunnel_'+kind,f:Math.min(7,Math.floor(q*8)),ramp:u,moving:0.5,dir:1,kind,piv:1}}
 if(c<5.0)return null;
 if(c<6.0){const q=(c-5),u=1-q*q*(3-2*q),p=rampPt(u);return{x:p.x,y:p.y,k:'rover_tunnel_'+kind,f:8+Math.min(7,Math.floor(q*8)),ramp:u,moving:0.5,dir:-1,kind,piv:1}}
 const q=(c-6)/2.4,e=q*q,x=top-45+(off-(top-45))*e;return{x,y:-Math.abs(Math.sin(x*0.2))*0.6*e,k:'truck_'+kind+'_drive',f:7-Math.floor(c*12)%8,moving:Math.min(1,e*2),dir:-1,kind}}   // backs out (never mirrored: bed labels stay readable)
function shadow(x,y,w,a=.45){ctx.save();ctx.globalAlpha=a;ctx.fillStyle='#000';ctx.filter='blur(2px)';ctx.beginPath();ctx.ellipse(x,y,0.53*w,3.5,0,0,7);ctx.fill();ctx.restore()}
// soft-edged cave: fade the art's rectangular sides/bottom into the regolith so it blends with the ground
const caveC=document.createElement('canvas'),caveX=caveC.getContext('2d');
function softCave(key,frame){const s=SPR[key];if(!s||!s.ready)return;const k=DPR*SC,w=Math.ceil(260*k),h=Math.ceil(130*k);if(caveC.width!==w||caveC.height!==h){caveC.width=w;caveC.height=h}
 const c=caveX;c.setTransform(1,0,0,1,0,0);c.clearRect(0,0,w,h);c.setTransform(k,0,0,k,0,0);smooth(c);c.drawImage(s.base,0,0,260,130);drawLayers(c,s,T,false,0);c.globalCompositeOperation='destination-in';
 let g=c.createLinearGradient(0,0,260,0);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(0.07,'#000');g.addColorStop(0.95,'#000');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,260,130);
 g=c.createLinearGradient(0,96,0,130);g.addColorStop(0,'#000');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,260,130);
 c.globalCompositeOperation='source-over';ctx.drawImage(caveC,FG.tunnel,-70,260,130)}
const dust=[];
function dustTick(r,dt){if(!r||!r.moving||r.y>4)return;if(Math.random()<dt*22*r.moving){const back=-(r.dir||1)*(r.flip?-1:1)*0;dust.push({x:(r.piv?r.x:r.x+45)-(r.dir||1)*38+(Math.random()-.5)*8,y:-1,vx:-(r.dir||1)*(6+Math.random()*10),vy:-(4+Math.random()*6),t:0,life:0.9+Math.random()*0.6,s:2+Math.random()*2.5})}}
function drawDust(dt){for(let i=dust.length-1;i>=0;i--){const d=dust[i];d.t+=dt;if(d.t>d.life){dust.splice(i,1);continue}d.x+=d.vx*dt;d.y+=d.vy*dt;d.vy+=1.62*4*dt;if(d.y>0){d.y=0;d.vy=0;d.vx*=0.9}   // low-g arc
 const q=d.t/d.life;ctx.globalAlpha=0.35*(1-q);ctx.fillStyle='#b9b4aa';ctx.beginPath();ctx.arc(d.x,d.y,d.s*(1+q*1.6),0,7);ctx.fill()}ctx.globalAlpha=1}
let fgLast=0;
// ---- Truck cycle (MINE_SPEC Rover Bay v3). Two labelled trucks share an 8.4 s beat: one dumps in the bay while the other works the tunnel.
const BEAT=8.4,truckKind=n=>n%2?'he3':'pt';
let TCK=0;const truckSpeed=()=>(1-0.5*LPS.k)*Math.min(1.6,1+(S.f.rover.lvl-1)*0.02);   // accumulated clock: a speed change never jumps the truck
function truckClock(){const t=TCK;return{n:Math.floor(t/BEAT),c:t%BEAT}}
const tintC=document.createElement('canvas'),tintX=tintC.getContext('2d');
function sprTint(key,frame,x,y,tint){if(tint>=0.999){spr(ctx,key,frame,x,y);return}const S=SPR[key];if(!S||!S.ready)return;const k=DPR*SC,w=Math.ceil(S.w*k)+2,h=Math.ceil(S.h*k)+2;
 if(tintC.width<w||tintC.height<h){tintC.width=w;tintC.height=h}tintX.setTransform(1,0,0,1,0,0);tintX.clearRect(0,0,tintC.width,tintC.height);tintX.setTransform(k,0,0,k,0,0);smooth(tintX);spr(tintX,key,frame,S.px,S.py);
 tintX.globalCompositeOperation='source-atop';tintX.fillStyle=`rgba(0,0,0,${1-tint})`;tintX.fillRect(0,0,S.w,S.h);tintX.globalCompositeOperation='source-over';ctx.drawImage(tintC,0,0,S.w*k,S.h*k,x-S.px,y-S.py,S.w,S.h)}
function roverBay(base,f,lp){const R=BAYROUTE;if(!R||S.f.rover.workers<=0)return;const tc=truckClock(),n=tc.n,c=tunnelOk?tc.c:2.7,kind=truckKind(n),FY=R.floorY-120;
 // bin: +1 step per pour end, wraps after full
 const pours=n+(c>=4.9?1:0);spr(ctx,'bin_fill_ore',Math.min(4,pours%6),14,68-120);
 if(c>=7.9)return;const i=Math.min(R.frames.length-1,Math.floor(c*R.fps)),q=c*R.fps-i,a=R.frames[i],b=R.frames[Math.min(R.frames.length-1,i+1)],x=Math.max(R.stopX??92,a.x+(b.x-a.x)*q),bob=a.bob+(b.bob-a.bob)*q;
 const tint=x>330?0.45:x<220?1:1-0.55*(x-220)/110,y=FY-bob;
 let key,fr8;if(c>=2.7&&c<5.8){key='rover_bay_dump_'+kind;fr8=Math.min(15,Math.floor((c-2.7)/3.1*16));if(!SPR[key].ready){key='rover_bay_dump_still_'+kind;fr8=0}}else{key='truck_'+kind+'_drive';const rev=a.seg==='reverseIn',mv=Math.abs(b.x-a.x)>0.05;fr8=mv?(rev?7-Math.floor(c*12)%8:Math.floor(c*12)%8):0}
 
 ctx.save();ctx.globalAlpha=.35*tint;ctx.fillStyle='#000';ctx.beginPath();ctx.ellipse(x+45,FY+0.5,46,3,0,0,7);ctx.fill();ctx.restore();
 sprTint(key,fr8,x,y,tint);
 if(x+90>292&&base.base){const kk=base.base.width/360;ctx.drawImage(base.base,292*kk,42*kk,10*kk,62*kk,292,42-120,10,62)}}   // right jamb over the truck

function drawMineYard(){
 // road strip along the loader path, conveyor up to the tower, attendant platform clear of the truck
 const mouth=FG.tunnel+168;
 ctx.fillStyle='#2c3038';ctx.fillRect(-70,-10,mouth+80,18);
 ctx.fillStyle='#6d675c';ctx.fillRect(-70,-10,mouth+80,1.6);ctx.fillRect(-70,6.4,mouth+80,1.6);
 ctx.fillStyle='#e0a24a';const dash=(T*22)%16;for(let x=-60+dash;x<mouth+10;x+=16)ctx.fillRect(x,-1.1,7,2.2);
 const x0=FG.tunnel+36,y0=-2,x1=-120,y1=-92,len=Math.hypot(x1-x0,y1-y0),ang=Math.atan2(y1-y0,x1-x0);
 ctx.strokeStyle='#4a5362';ctx.lineWidth=8;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(x0,y0);ctx.lineTo(x1,y1);ctx.stroke();
 ctx.strokeStyle='#9aa6b6';ctx.lineWidth=2.2;ctx.beginPath();ctx.moveTo(x0,y0-3.2);ctx.lineTo(x1,y1-3.2);ctx.stroke();
 ctx.save();ctx.translate(x0,y0);ctx.rotate(ang);ctx.fillStyle='#d9893a';const off=(T*36)%14;for(let x=off;x<len;x+=14)ctx.fillRect(x,-1.3,6,2.6);ctx.restore();
 const px=FG.tunnel-6;
 ctx.fillStyle='rgba(0,0,0,.35)';ctx.beginPath();ctx.ellipse(px+16,2,18,3,0,0,7);ctx.fill();
 ctx.fillStyle='#3e4654';ctx.fillRect(px,-20,34,20);ctx.fillStyle='#c5ceda';ctx.fillRect(px,-20,34,2);ctx.fillRect(px+2,-20,2,20);ctx.fillRect(px+30,-20,2,20);
 ctx.save();ctx.translate(px+16,0);ctx.scale(0.42,0.42);
 if(ok('crew13_walk'))spr(ctx,'crew13_walk',0,0,0);else{ctx.fillStyle='#e7eef8';ctx.fillRect(-6,-28,12,22);ctx.fillStyle='#ffb347';ctx.beginPath();ctx.arc(0,-32,6,0,7);ctx.fill()}
 ctx.restore();
 const lg=ctx.createRadialGradient(FG.tunnel+150,-16,6,FG.tunnel+140,-8,110);
 lg.addColorStop(0,'rgba(255,176,80,.42)');lg.addColorStop(1,'rgba(255,176,80,0)');
 ctx.fillStyle=lg;ctx.fillRect(FG.tunnel+40,-90,210,100)}
function drawMineForeground(f){if(!ok('tunnel_back'))return;const par=(f.x-195)*(FG.par-1)/TS,dt=Math.min(0.1,Math.max(0,T-fgLast));fgLast=T;
 ctx.save();ctx.translate(par,FG.y);ctx.scale(FG.s,FG.s);
 // No stand-in road, conveyor, or stick attendant. Those covered Art's cave.
 // attendant_marshal, road_light, and lamp_post are not in the repo yet.
 softCave('tunnel_back');
 let r=null;if(S.f.rover.workers>0&&BAYROUTE)r=roverState();
 dustTick(r,dt);drawDust(dt);
 
 if(r){const ramp=r.ramp!=null;
  if(!ramp||r.ramp<0.35)shadow(r.piv?r.x:r.x+45,(r.piv?r.y:r.y-Math.min(0,0))+0.5,90,.45*(ramp?1-r.ramp/0.35:1));
  ctx.save();
  // never draw over the portal: clip off the header/arch (x>=146,y<70 local) and everything right of the mouth (x>=228)
  if(ramp){const L=FG.tunnel;ctx.beginPath();ctx.moveTo(-600,-300);ctx.lineTo(L+146,-300);ctx.lineTo(L+146,0+2);ctx.lineTo(L+226,2);ctx.lineTo(L+226,300);ctx.lineTo(-600,300);ctx.closePath();ctx.clip();
   ctx.globalAlpha=Math.max(0,Math.min(1,(1-r.ramp)/0.25))}   // fade into the dark mouth
  if(r.piv){ctx.translate(r.x,r.y);spr(ctx,r.k,r.f,0,0)}else{ctx.translate(r.x+45,r.y);if(r.ang)ctx.rotate(r.ang);if(r.flip)ctx.scale(-1,1);spr(ctx,r.k,r.f,-45,0)}ctx.restore()}
 if(ok('tunnel_front_lip'))softCaveLip();
 if(ok('tunnel_haze')){ctx.globalAlpha=0.75+0.25*Math.sin(T*0.9);spr(ctx,'tunnel_haze',0,FG.tunnel+Math.sin(T*0.35)*3,0);ctx.globalAlpha=1}
 ctx.restore()}
const lipC=document.createElement('canvas'),lipX=lipC.getContext('2d');
function softCaveLip(){const s=SPR.tunnel_front_lip,k=DPR*SC,w=Math.ceil(260*k),h=Math.ceil(130*k);if(lipC.width!==w||lipC.height!==h){lipC.width=w;lipC.height=h;lipC._ok=0}
 if(!lipC._ok){const c=lipX;c.setTransform(1,0,0,1,0,0);c.clearRect(0,0,w,h);c.setTransform(k,0,0,k,0,0);smooth(c);c.drawImage(s.img,0,0,260,130);c.globalCompositeOperation='destination-in';
  let g=c.createLinearGradient(0,0,260,0);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(0.07,'#000');g.addColorStop(0.95,'#000');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,260,130);
  g=c.createLinearGradient(0,96,0,130);g.addColorStop(0,'#000');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(0,0,260,130);c.globalCompositeOperation='source-over';lipC._ok=1}
 ctx.drawImage(lipC,FG.tunnel,-70,260,130)}
// ----- Cargo Space Dock (own station) -----
const shipAnim={mode:null,t0:0};
const stopOfDock=()=>STOPS.findIndex(s=>s.kind==='dock');
const DSC=0.65;   // 600-wide dock fits the 390 screen
const dockTier=t=>Math.floor(dockLvl(t)/10)*10;
// dock track looks: trimmed pieces from tracks/dock_tracks.json (dock-tracks-v1), logical pts in a 760x620 canvas, pivot (380,620). Loaded on demand.
let TRK=null,trkLoading=null;const trkImg={};
function trackMan(){if(!trkLoading)trkLoading=tryJSON(ART+DOCK+'tracks/dock_tracks.json').then(j=>{TRK=j&&j.images?j:{images:{}}});return TRK}
function ensureTrack(t,L){const k=`dock_${t}_t${L}`;if(!trackMan())return null;const list=TRK.images[k];if(!list)return null;
 return list.map(e=>{let o=trkImg[e.file];if(!o){o=trkImg[e.file]={e,img:null};getImg(ART+DOCK+'tracks/'+e.file).then(bmp).then(im=>o.img=im)}return{e,o}})}
function dockOverlays(list){list.forEach(t=>{for(let L=10;L<=dockLvl(t);L+=10){const ps=ensureTrack(t,L);if(ps)ps.forEach(({e,o})=>{if(o.img)ctx.drawImage(o.img,-380+e.x,-620+e.y,e.w,e.h)})}})}   // cumulative per track; every piece; missing art → base dock
const HANDLER_X=392;   // handler's mark on the deck. Other walkers route behind it and never cross it.
const dockCrew=[{a:70,b:200,k:'push'},{a:230,b:340,k:'carry'},{a:470,b:575,k:'walk'}];
// Launch closes the hatch, then lifts. Nothing slides in: the crane already put the hold aboard. Leftovers stay on the pad.
const STOCK_VIS=12;
const hatchAt=()=>0.02;
const liftDelay=()=>shipAnim.mode==='launch'?0.32:0;
// what the pad stacks show around a launch: loaded containers stay drawn until they leave. The animated 12 leave one by one (top first);
// the rest of the load fades out over 200 ms after the slide, so the stack matches the pad count when the tick-down ends. Unloaded containers stay.
function padVis(){const r={pt:padPt(),he:padHe(),spt:0,she:0,fpt:0,fhe:0,fa:1};if(!padDip||padDip.lp==null)return r;const dt=T-padDip.t,E0=padDip.end;if(dt>=E0+0.2)return r;
 const n=padDip.n,k=Math.min(n,12),ah=Math.round(k*padDip.he/Math.max(1,n)),ap=k-ah,fh=padDip.lh-ah,fp=padDip.lp-ap;let wp=0,wh=0;
 for(let i=0;i<k;i++)if(dt-i*0.04<=0){if(i<ah)wh++;else wp++}   // animated boxes not yet departed
 if(dt<E0){r.spt=fp+wp;r.she=fh+wh;return r}
 r.fa=1-(dt-E0)/0.2;r.fpt=fp;r.fhe=fh;return r}
function padSlide(deck,X,sy0){const dt=padDip?T-padDip.t:9;   // drawn over the hull so the slide into the hold reads
 if(padDip&&dt<padDip.end){const k=Math.min(padDip.n,12),he=Math.round(k*padDip.he/Math.max(1,padDip.n));for(let i=0;i<k;i++){const isHe=i<he,j=isHe?i:i-he,q=Math.max(0,Math.min(1,(dt-i*0.04)/0.4));if(q<=0||q>=1)continue;
    const sx=X(isHe?510:440),sy=deck-(PAD_VIS.tiers-1)*PAD_VIS.tierGap+j*10,e=easeInOutCubic(q),bx=sx+(36-sx)*e,by=sy+(sy0-240-sy)*e;ctx.save();ctx.globalAlpha=1-0.6*q;spr(ctx,isHe?'he3_canister_pulse':'loaded_box_pulse',0,bx,by);ctx.restore()}}
}
const CRANE_PHASES=[['slew',0.90],['lower',0.85],['latch',0.25],['raise',0.85],['traverse',1.15],['settle',0.90],['enter',0.70],['roller',0.40],['door',0.50],['return',1.10]];
function cranePhaseAt(t){let u=Math.max(0,t||0);for(const [id,d] of CRANE_PHASES){if(u<=d)return{id,q:d?u/d:1};u-=d}return{id:'park',q:1}}
function craneSwayDeg(ph){
 if(ph.id==='traverse')return 6.2*Math.sin(ph.q*Math.PI*2);
 if(ph.id==='settle')return 6.2*Math.exp(-5.2*ph.q)*Math.sin(ph.q*Math.PI*3);   // under 0.5° before bay entry
 if(ph.id==='enter'||ph.id==='roller'||ph.id==='door')return 0.22*Math.sin(T*1.7);
 return Math.sin(T*0.55)*0.7}
function craneCarrying(ph){return ph.id==='latch'&&ph.q>0.5||ph.id==='raise'||ph.id==='traverse'||ph.id==='settle'||ph.id==='enter'}
function drawStockpile(deck,X,skip){let pt=S.pt,he=S.he;if(skip==='he'&&he>0)he--;else if(skip==='pt'&&pt>0)pt--;
 const extra=S.pt+S.he-STOCK_VIS,show=Math.min(STOCK_VIS,pt+he);let spt=Math.min(pt,show),she=Math.min(he,show-spt);
 if(pt>0&&he>0&&she===0&&show>1){she=1;spt=show-1}
 const zone=(cx,count,key)=>{for(let i=0;i<count;i++){const r=Math.floor(i/3),j=i%3;spr(ctx,key,fr(key,T+i*0.3),X(cx)-27+j*26,deck-r*22)}};
 if(spt)zone(440,spt,'loaded_box_pulse');if(she)zone(508,she,'he3_canister_pulse');
 if(extra>0){ctx.font='800 13px Rajdhani,Inter,system-ui,sans-serif';const txt='+'+extra,w=ctx.measureText(txt).width+12,bx=X(545),by=deck-18;
  ctx.fillStyle='rgba(10,14,26,.85)';rr(ctx,bx,by,w,18,9);ctx.fill();ctx.fillStyle='#ffe2b0';ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillText(txt,bx+6,by+9)}}
function drawCrane(deck,X){const sh=S.ship,busy=sh.st==='docked'&&(sh.craneT||0)>0.04,ph=busy?cranePhaseAt(sh.craneT):{id:'park',q:1};
 const sway=craneSwayDeg(ph),carry=busy&&craneCarrying(ph),lerp=(a,b,q)=>a+(b-a)*Math.max(0,Math.min(1,q));
 const stockX=458,bayX=156,parkX=360;let hx=parkX,hy=deck-170,roll=0;
 if(ph.id==='slew'){hx=lerp(parkX,stockX,ph.q);hy=deck-176}
 else if(ph.id==='lower'){hx=stockX;hy=lerp(deck-176,deck-34,ph.q)}
 else if(ph.id==='latch'){hx=stockX;hy=deck-34}
 else if(ph.id==='raise'){hx=stockX;hy=lerp(deck-34,deck-164,ph.q)}
 else if(ph.id==='traverse'){hx=lerp(stockX,230,ph.q);hy=deck-164}
 else if(ph.id==='settle'){hx=230;hy=deck-164}
 else if(ph.id==='enter'){hx=lerp(230,bayX,ph.q);hy=lerp(deck-164,deck-148,ph.q)}
 else if(ph.id==='roller'){hx=bayX;hy=deck-148;roll=ph.q}
 else if(ph.id==='door'){hx=lerp(bayX,250,ph.q);hy=deck-168}
 else if(ph.id==='return'){hx=lerp(250,parkX,ph.q);hy=deck-176}
 hx+=sway*1.1;
 spr(ctx,'crane_gantry',0,X(430),deck);const gtx=X(430)+Math.sin(T*0.35)*6,gty=deck-188;spr(ctx,'crane_trolley',0,gtx,gty);
 ctx.strokeStyle='#2a2f3a';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(gtx,gty+6);ctx.lineTo(gtx,gty+26);ctx.stroke();
 const mastX=X(515);ctx.save();ctx.translate(mastX,deck);ctx.scale(1.45,1.45);spr(ctx,'crane_jib_mast',0,0,0);
  ctx.translate(0,-176);ctx.rotate((-16+sway)*Math.PI/180);ctx.scale(-1,1);spr(ctx,'crane_jib_boom',0,0,0);ctx.restore();
 const tipX=mastX-Math.cos(sway*Math.PI/180)*168,tipY=deck-250+Math.sin((-16+sway)*Math.PI/180)*70;
 ctx.strokeStyle='#1c212b';ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(tipX,tipY);ctx.lineTo(X(hx),hy);ctx.stroke();
 const he=craneWantsHe();
 if(carry){spr(ctx,'crane_hook_empty',0,X(hx),hy);spr(ctx,he?'he3_canister_pulse':'loaded_box_pulse',0,X(hx),hy+16)}
 else spr(ctx,'crane_hook_empty',0,X(hx),hy);
 if(roll>0){const e=roll*roll*(3-2*roll);ctx.save();ctx.globalAlpha=1-e;spr(ctx,'loaded_box_pulse',0,X(lerp(bayX,78,e)),lerp(hy,deck-230,e));ctx.restore()}
 return carry?(he?'he':'pt'):''}
function drawDock(bi,atRest){const k=DSC/TS;ctx.save();ctx.translate(-(bi===STOPS[site].bi?dockPan:0)/TS,0);ctx.scale(k,k);
 if(!ok('dock_base')){spr(ctx,'site',fr('site',T),0,-6,1/k,1/k);label(0,-150,'Cargo Space Dock','#c9d3e6',22);label(0,-120,'Loading dock art…','#8fa3c4',18);ctx.restore();return}
 const X=x=>x-300,deck=-50;
 // floodlights
 [10,585].forEach(x=>{if(ok('floodlight_cone')){ctx.globalAlpha=.55;spr(ctx,'floodlight_cone',0,X(x),deck-150+6);ctx.globalAlpha=1}spr(ctx,'floodlight_mast',0,X(x),deck)});
 ctx.save();ctx.translate(X(65),deck);ctx.scale(-1,1);spr(ctx,'launch_tower4',0,0,0);ctx.restore();
 spr(ctx,'dock_base',0,0,0);
 dockOverlays(['crew','refuel','pad']);
 // walkers stay on the back lane, clear of the handler's mark
 const nCrew=Math.min(dockCrew.length,1+Math.floor(dockLvl('crew')/10));
 for(let i=0;i<nCrew;i++){const c=dockCrew[i],per=(c.b-c.a)/28*2+1.2,q=((T+i*1.7)%per)/per,go=q<0.5,u=go?q*2:2-q*2;
  let x=c.a+(c.b-c.a)*Math.min(1,Math.max(0,(u*1.1-0.05)));if(Math.abs(x-HANDLER_X)<36)x=HANDLER_X+(x<HANDLER_X?-36:36);
  ctx.save();ctx.translate(X(x),deck-18);if(!go)ctx.scale(-1,1);spr(ctx,'crew13_'+c.k,fr('crew13_'+c.k,T),0,0);ctx.restore()}
 const skip=(S.ship.st==='docked'&&(S.ship.craneT||0)>0.04&&craneCarrying(cranePhaseAt(S.ship.craneT)))?(craneWantsHe()?'he':'pt'):'';
 // ship
 const s=S.ship,a=shipAnim,t=T-a.t0;let y=deck,flame=0,glow=0,vis=s.st!=='trip';
 if(a.mode==='launch'){vis=true;const tl=t-liftDelay();if(tl<0){}else if(tl<0.4){flame=1;glow=1;if(!a.smoke){a.smoke=1;FX.push({type:'dock',key:'smoke_plume4',t:T})}}else if(tl<1.9){const q=(tl-0.4)/1.5;y=deck-1800*q*q;flame=1}else{a.mode=null;vis=false}}
 if(a.mode==='land'){vis=true;if(t<1.8){const q=t/1.8;y=deck-1800*(1-easeOutCubic(q));flame=t>1.5?(1.8-t)/0.3:1;glow=t>1.3?1:0}else if(t<2.1){y=deck-4*Math.sin((t-1.8)/0.3*Math.PI);if(!a.dust){a.dust=1;FX.push({type:'dock',key:'dust_puff4',t:T})}}else a.mode=null}
 if(vis&&ok('ship4_hull')){const hx=0,top=y-480;
  if(flame>0){ctx.globalAlpha=Math.min(1,flame);spr(ctx,'ship4_flame',fr('ship4_flame',T),hx,top+432);ctx.globalAlpha=1}
  if(glow){ctx.globalCompositeOperation='lighter';spr(ctx,'ship4_engine_glow',fr('ship4_engine_glow',T),hx,top+440);ctx.globalCompositeOperation='source-over'}
  spr(ctx,'ship4_hull',0,hx,y);if(ok('ship4_hatch')){let hf=5;if(a.mode==='launch'){const tc=t-hatchAt();hf=tc<0?0:Math.min(5,Math.floor(tc/0.05))}else if(a.mode!=='land'&&(s.st==='docked'||s.st==='turn'))hf=0;spr(ctx,'ship4_hatch',hf,hx-160+SPR.ship4_hatch.px,top+SPR.ship4_hatch.py)}
 ctx.globalCompositeOperation='lighter';spr(ctx,'ship4_navlights',fr('ship4_navlights',T),hx-160+108,top+163);ctx.globalCompositeOperation='source-over'}
 drawStockpile(deck,X,skip);
 drawCrane(deck,X);
 dockOverlays(['crane']);
 // handler stands on the mark, in front. Nobody else is drawn here.
 ctx.save();ctx.translate(X(HANDLER_X),deck);spr(ctx,'crew13_walk',0,0,0);ctx.restore();
 const pt=dockTier('pad'),sk=pt>=20&&ok('dock_sign_neon_pad_t20')?'pad_t20':pt>=10&&ok('dock_sign_neon_pad_t10')?'pad_t10':'base';
 {const g=SPR['dock_sign_glow_'+sk],gf=fr('dock_sign_glow_'+sk,T),al=g&&g.alpha?g.alpha[gf%g.n]:1;ctx.save();ctx.translate(0,deck+38);ctx.rotate(-curStopA);spr(ctx,'dock_sign_neon_'+sk,0,0,0);spr(ctx,'dock_sign_glow_'+sk,gf,0,0);ctx.restore();
  if(ok('dock_sign_bloom_'+sk)){ctx.save();ctx.globalCompositeOperation='lighter';ctx.globalAlpha=0.6+0.4*al;spr(ctx,'dock_sign_bloom_'+sk,0,0,deck);ctx.restore()}}
 const mt=(T*30)%1400,mx=mt<700?-700+mt:700-(mt-700),mxC=mx<0?mx:Math.min(mx,440);
 if(Math.abs(mxC-HANDLER_X)>48){ctx.save();ctx.translate(X(mxC),deck-16);if(mt>=700)ctx.scale(-1,1);spr(ctx,'cargo_mule',fr('cargo_mule',T),0,0);ctx.restore()}
 FX.filter(o=>o.type==='dock').forEach(o=>{const q=frOnce(o.key,T-o.t);if(SPR[o.key]&&q<SPR[o.key].n)spr(ctx,o.key,q,0,deck)});
 ctx.restore();
 const L=shipLoad(),pad=loose(),Y=L+pad;
 if(s.st==='docked'&&a.mode!=='launch')pillBtn(0,-408,L?`🚀 ${L} of ${Y} loaded`:'Crane is loading…',L>0);
 else if(s.st==='trip')label(0,-408,`🚀 To Earth: ${mmss((s.t/1000+tripSec(s)-gnow()/1000)/SPEED)} · ${fmt(shipValue(s))}`,'#eaf2ff',15);
 else if(s.st==='turn')label(0,-408,`🔧 Refuel & repair ${mmss((s.t/1000+turnSec()-gnow()/1000)/SPEED)}`,'#eaf2ff',15);
 label(0,-372,`In hold ${L}/${holdCap()}`,'#bfe9ff',14);
 label(0,-352,`On pad ${pad}`,'#d5e6ff',14)}
function easeOutBack(t,c1=1.70158){const c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)}
const easeOutCubic=t=>1-Math.pow(1-t,3),easeInOutCubic=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
// =====================================================================
// FX (positions in tower-local coords of a stop, so they ride the rotation)
// =====================================================================
const FX=[];
function stopXf(si){const f=stopFrame(si);return f}
function withStop(si,fn){const f=stopFrame(si);if(Math.abs(f.a)>0.36)return;ctx.save();ctx.translate(f.x,f.y);ctx.rotate(f.a);ctx.scale(TS,TS);fn();ctx.restore()}
// Dock delivery pop-up (Art & Animation spec): Rajdhani Bold 22/26 pt gold, 2 pt navy outline, soft cyan glow, 26 pt coin
const coinImg=new Image();coinImg.src=ART+'ui/ui_icon_coin.webp';const POPFONT='Rajdhani,"Arial Narrow","Helvetica Neue",Arial,sans-serif';
function drawDockPop(o,t){const sc=t<0.12?0.6+0.5*(t/0.12):t<0.18?1.1-0.1*((t-0.12)/0.06):1,ty=t<0.18?0:Math.min(1,(t-0.18)/1.2),y=o.y-40*easeOutCubic(ty),a=t<1.68?1:Math.max(0,1-(t-1.68)/0.3);
 const fs=o.v>=1000?26:22;ctx.save();ctx.globalAlpha=a;ctx.globalCompositeOperation='source-over';ctx.filter='none';ctx.translate(o.x,y);ctx.scale(sc,sc);ctx.font=`700 ${fs}px ${POPFONT}`;const tw=ctx.measureText(o.txt).width,w=26+6+tw,x0=-w/2;
 ctx.save();ctx.globalAlpha*=0.25;const g=ctx.createRadialGradient(0,0,4,0,0,w*0.7);g.addColorStop(0,'#3ad0ff');g.addColorStop(1,'rgba(58,208,255,0)');ctx.fillStyle=g;ctx.beginPath();ctx.ellipse(0,0,w*0.7,fs*1.3,0,0,7);ctx.fill();ctx.restore();
 if(coinImg.complete&&coinImg.naturalWidth)ctx.drawImage(coinImg,x0,-13,26,26);
 ctx.textAlign='left';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=4;ctx.strokeStyle='rgba(11,16,32,.8)';ctx.strokeText(o.txt,x0+32,1);ctx.fillStyle='#FFD24A';ctx.fillText(o.txt,x0+32,1);ctx.restore()}
function pop(si,x,y,key,txt,delay=0){FX.push({type:'pop',si,x,y,key,txt,t:T+delay})}
function floorPt(d,x,y){return{si:stopOfTower(d.b),x:FX0+x,y:floorBottom(d.k)-120+y}}
function drawFX(){for(let i=FX.length-1;i>=0;i--){const o=FX[i],t=T-o.t;if(t<0)continue;let done=false;
 if(o.type==='dock'){if(t>3)done=true}
 else if(o.type==='dockpop'){done=t>1.98;withStop(o.si,()=>drawDockPop(o,t))}
 else if(o.type==='pop'){const D=o.rise||0.6;done=t>D+0.5;withStop(o.si,()=>{if(t<D){const q=t/D,sc=t<0.18?0.6+0.5*(t/0.18):(t<0.28?1.1-0.1*((t-0.18)/0.1):1);
   ctx.globalAlpha=t>D-0.15?(D-t)/0.15:1;const y=o.y-(o.dist||28)*easeOutCubic(q);spr(ctx,o.key+'_spin',fr(o.key+'_spin',t),o.x,y,sc,sc);
   if(o.txt){ctx.font='700 15px Rajdhani,Inter,system-ui,sans-serif';ctx.textAlign='left';ctx.textBaseline='middle';ctx.lineWidth=3;ctx.strokeStyle='rgba(0,0,0,.6)';ctx.strokeText(o.txt,o.x+13,y);ctx.fillStyle=o.key==='coin'?'#ffd34d':'#eaf2ff';ctx.fillText(o.txt,o.x+13,y)}ctx.globalAlpha=1}
  else{const q=frOnce(o.key+'_sparkle',t-D);spr(ctx,o.key+'_sparkle',q,o.x,o.y-(o.dist||28))}})}
 else if(o.type==='sprite'){const q=frOnce(o.key,t);done=!SPR[o.key]||!SPR[o.key].ready||q>=SPR[o.key].n*(o.loops||1);if(!done)withStop(o.si,()=>spr(ctx,o.key,q,o.x,o.y))}
 else if(o.type==='banner'){done=t>1.35;withStop(o.si,()=>{if(!ok(o.key))return;const s=t<0.15?0.6+0.48*(t/0.15):t<0.25?1.08-0.08*((t-0.15)/0.1):1;ctx.globalAlpha=t>1.15?Math.max(0,(1.35-t)/0.2):1;
   ctx.save();ctx.translate(o.x,o.y);ctx.scale(s,s);ctx.drawImage(SPR[o.key].img,-110,-22,220,44);ctx.restore();ctx.globalAlpha=1})}
 else if(o.type==='arrive'){done=t>4.5;withStop(o.si,()=>drawArrive(o,t))}
 if(done)FX.splice(i,1)}}
// new miner: car doors → hiss → walk out → wave → sparkle → +miner icon
function residentArrives(){const si=stopOfTower(0);const e=elevState(0);if(e.phase==='hold'&&Math.abs(e.pos)<0.01)e.hold=Math.max(e.hold,2);else e.forced=0;
 FX.push({type:'arrive',si,t:T+(e.pos>0.01?1.6:0),x:180,y:floorBottom(0)-16})}
function drawArrive(o,t){const ex=o.x-17;
 if(t>0.15&&t<0.68)spr(ctx,'fx_door_hiss',frOnce('fx_door_hiss',t-0.15),ex,o.y-8,-1,1);
 let ax=ex,key='idle_worker',f=0,flip=true;if(t>=0.4&&t<0.9){ax=ex-18*easeOutCubic((t-0.4)/0.5);key='walk_worker';f=fr(key,t)}else if(t>=0.9){ax=ex-18;if(t<1.73){key='wave_worker';f=Math.min(9,frOnce('wave_worker',t-0.9))}else if(t<2.2){key='idle_worker';f=fr(key,t)}else{ax=ex-18-40*(t-2.2);key='walk_worker';f=fr(key,t)}}
 if(t>=0.3){ctx.save();ctx.globalAlpha=t>4?Math.max(0,(4.5-t)/0.5):1;ctx.translate(ax,o.y);if(flip&&key!=='wave_worker')ctx.scale(-1,1);spr(ctx,key,f,0,0);ctx.restore();ctx.globalAlpha=1}
 if(t>0.95&&t<1.6)spr(ctx,'fx_welcome_sparkle',frOnce('fx_welcome_sparkle',t-0.95),ex-18,o.y-48);
 if(t>1.0&&!o.p1){o.p1=1;FX.push({type:'pop',si:o.si,x:ex-18,y:o.y-50,key:ok('pickup_miner_spin')?'pickup_miner':'pickup_people',txt:'+1 miner',t:T,rise:0.7,dist:30})}
 if(t>1.6&&!o.p3){o.p3=1;tickMeter('people')}}
// coins only for: dock delivery, ore trickle, Refinery
function oreFx(v){const si=stopOfTower(IDX.rover!=null?F[IDX.rover].b:1);if(Math.abs(stopFrame(si).a)>0.36)return;pop(si,FX0+56,-60,ok('pickup_ore_spin')?'pickup_ore':'coin','+'+fmt(v));tickMeter('coin')}
function refineFx(v){const d=F[IDX.refinery],top=d.k===floorsBuilt(d.b)-1,p=floorPt(d,250,top?62:-8);FX.push({type:'pop',si:p.si,x:p.x,y:p.y,key:ok('pickup_refined_coin_spin')?'pickup_refined_coin':'coin',txt:'+'+fmt(v),t:T,dist:top?24:20})}   // starts 4pt above the nameplate (top floor: lower, under the HUD)
function tickMeter(k){const el=document.querySelector(`.m[data-k="${k}"]`)||(k==='coin'?$('#money'):null);if(!el)return;el.classList.remove('tick');void el.offsetWidth;el.classList.add('tick')}
// =====================================================================
// ACTIONS
// =====================================================================
function moneyPop(v){if(!(v>0))return;const r=$('#money').getBoundingClientRect(),d=document.createElement('div');d.textContent='+'+fmt(v);d.style.cssText=`position:fixed;left:${r.left+r.width/2}px;top:${r.bottom+4}px;transform:translateX(-50%);z-index:60;font:700 20px var(--num);color:#ffe2b0;text-shadow:0 2px 6px rgba(0,0,0,.6);pointer-events:none;transition:transform .9s cubic-bezier(.2,.9,.3,1),opacity .9s`;document.body.appendChild(d);requestAnimationFrame(()=>{d.style.transform='translate(-50%,-26px)';d.style.opacity='0'});setTimeout(()=>d.remove(),1000)}
function bump(){const m=$('#money');m.classList.add('bump');setTimeout(()=>m.classList.remove('bump'),160)}
function buyFloor(i){let d=F[i];const nc=noCrew(d);if(d.upper){i=IDX[d.upper];d=F[i]}if(lockReason(i))return false;if(d.slots===2){const u=S.f[d.id+'_up'];if(u){u.built=true;u.lvl=1}}S.money-=d.cost;if(d.pack)loadGroup(d.pack);const f=st(i);f.built=true;f.lvl=1;if(!nc&&idleResidents()>0)f.workers=1;
 ensureBuildingArt(d.b);(floorFx[d.id]=floorFx[d.id]||{}).build=T;const p=floorPt(d,0,120);FX.push({type:'sprite',key:'fx_floor_unlock',si:p.si,x:p.x,y:p.y,t:T});
 toast(f.workers||nc?`🏗️ ${d.name} built!`:`🏗️ ${d.name} built: needs a resident to staff it`);crewSync();save();hud();return true}
function upgradeN(i,n){let c=0,k=0,lv=st(i).lvl;while(k<n&&lv+k<CFG.maxLevel){const x=upCost(i,lv+k);if(c+x>S.money)break;c+=x;k++}return{k,c}}
function doUpgrade(i,n){const {k,c}=upgradeN(i,n);if(!k)return;const f=st(i),d=F[i],before=f.lvl;S.money-=c;f.lvl+=k;const fx=floorFx[d.id]=floorFx[d.id]||{};fx.up=T;
 const p=floorPt(d,180,60);if(ok('fx_upgrade_burst'))FX.push({type:'sprite',key:'fx_upgrade_burst',si:p.si,x:p.x,y:p.y,t:T});else (floorFx[d.id]=floorFx[d.id]||{}).pop=T;   // burst not loaded yet: quick scale-pop instead
 CFG.tierLevels.forEach(L=>{if(before<L&&f.lvl>=L)tierUp(i,L)});crewSync();save();hud();openSheet(i,true)}
function tierUp(i,L){const d=F[i],p=floorPt(d,0,120),fx=floorFx[d.id]=floorFx[d.id]||{};fx.tierDrop={L,t:T};loadGroup('fx2');if(d.tierBase)ensureTier(d,L);
 FX.push({type:'sprite',key:'fx_tierup_flash_rays',si:p.si,x:p.x,y:p.y,t:T});FX.push({type:'banner',key:'banner_'+L,si:p.si,x:p.x+180,y:p.y-150,t:T+0.3});
 if(L===50)FX.push({type:'sprite',key:'fx_gold_shimmer',si:p.si,x:p.x,y:p.y,t:T,loops:2});toast(`★ ${d.name}: ${d.tierInfo[L].name}!`)}
const hireCost=i=>Math.round(25*Math.pow(3,st(i).workers));
function unassign(i){const f=st(i);if(noCrew(F[i])||f.workers<1)return;f.workers--;if(!f.workers)f.off=1;crewSync();save();hud();openSheet(i,true);toast('🧑‍🚀 Resident sent to idle')}
function hire(i){const f=st(i);if(noCrew(F[i]))return;if(f.workers>=floorSlots(f)||idleResidents()<1||S.money<hireCost(i))return;S.money-=hireCost(i);f.workers++;f.off=0;crewSync();save();hud();openSheet(i,true);toast('👩‍🚀 Resident assigned')}
function tapFloor(i){const d=F[i],f=st(i);(floorFx[d.id]=floorFx[d.id]||{}).tap=T;
 if(!noCrew(d)&&!f.workers&&!f.off&&idleResidents()>0){f.workers=1;crewSync();toast(`👩‍🚀 A resident now staffs ${d.name}`);save();return}
 if(d.role==='mine'&&!S.tapped){S.tapped=1;save()}
 if(d.role==='depot'){const p=floorPt(d,180,50);pop(p.si,p.x,p.y,ok('pickup_miner_spin')?'pickup_miner':'pickup_people',meter(i))}
 if(d.res){const p=floorPt(d,180,50);pop(p.si,p.x,p.y,RES[d.res].pick,meter(i))}
 openSheet(i)}
function elevUpgrade(bi){if(elevLvl(bi)>=CFG.elevator.maxLevel||S.money<elevCost(bi))return;const before=elevLook(bi);S.money-=elevCost(bi);S.elev[BUILDINGS[bi].id]++;
 if(elevLook(bi)!==before){loadGroup('fx2');FX.push({type:'sprite',key:'fx_elevator_tierup',si:stopOfTower(bi),x:180,y:floorBottom(0)-0,t:T});toast('🛗 New elevator: '+elevLook(bi).replace('_',' '))}save();hud();openElev(bi)}
// =====================================================================
// SHEET
// =====================================================================
let sheetFor=null,sheetOpenedAt=0,mult=1;const ui=n=>ART+'ui/'+n+'.webp';
const resIcon=d=>d.role==='depot'?'ui_icon_food':d.role==='mine'||d.role==='refinery'?'ui_icon_income':d.res==='oxygen'?'ui_icon_oxygen':d.res==='water'?'ui_icon_water':d.res==='energy'?'ui_icon_energy':d.role==='housing'?'ui_icon_people':d.role==='shop'?'ui_icon_coin':'ui_icon_power';
function statRows(i){const d=F[i],f=st(i),lv=f.lvl,{k}=upgradeN(i,mult),nl=Math.min(CFG.maxLevel,lv+Math.max(1,k)),a=rawOut(i,lv),b=rawOut(i,nl),pw=d.use?E.power:1,rows=[];
 const arrow=(x,y)=>`${x} <em>→ ${y}</em>`;
 if(d.res==='oxygen'||d.res==='water'){const da=Math.floor(b*pw)-Math.floor(a*pw);rows.push(['ui_icon_people','Supports',arrow(num(a*pw)+' people',num(b*pw)+(da>0?` (+${num(da)} miners)`:''))]);rows.push([resIcon(d),(d.res==='oxygen'?'O₂':'Water')+' output',arrow(num(a*0.8)+' kg/h',num(b*0.8)+' kg/h')])}
 if(d.res==='energy'){rows.push(['ui_icon_energy','Energy output',arrow(num(a)+' kW',num(b)+' kW')]);rows.push(['ui_icon_power','Base demand',`${num(E.demand)} kW`+(E.power<1?' <span class="bad">· short</span>':'')])}
 if(d.role==='housing')rows.push(['ui_icon_people','Beds',arrow(num(Math.floor(a)),num(Math.floor(b)))]);
 if(d.role==='housing'&&Math.floor(b)>Math.floor(a))rows[rows.length-1][2]+=` (+${num(Math.floor(b)-Math.floor(a))} miners)`;
 if(d.role==='depot'||d.role==='boost')rows.push(['ui_icon_income','Mining boost',arrow('+'+(2+lv)+'% mining','+'+(2+nl)+'%')]);   // +3% at L1, +1%/level (summed with other rooms)
 if(d.role==='refinery')rows.push(['ui_icon_income','Refined',arrow(num(a*pw)+'/min',num(b*pw)+'/min')]);
 if(d.id==='rover')rows.push(['ui_icon_income','Mining',arrow(num(a*pw*CFG.econ.ptPerMin)+' Pt/min',num(b*pw*CFG.econ.ptPerMin)+' Pt/min')]);
 else if(d.role==='mine')rows.push(['ui_icon_income','Mining boost',arrow('+'+Math.round(procBoost(d,lv)*100)+'%','+'+Math.round(procBoost(d,nl)*100)+'%')]);
 if(d.use)rows.push(['ui_icon_low_power','Power use',`${d.use} kW`+(E.power<1?` <span class="bad">· ${Math.round(E.power*100)}% power</span>`:'')]);
 return rows}
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
 ${noCrew(d)?'':`<div class="hire"><button class="av" id="ua" aria-label="Send one crew to idle" ${f.workers?'':'disabled'}><img src="${ui('ui_icon_worker')}"></button><div class="ht"><b>Crew ${f.workers}/${slots}</b><small>${f.workers?'Tap the crew icon to send one to idle':'No crew · tap + to assign'} · ${idle} idle</small></div>
  <button id="hb" aria-label="Assign a resident" ${hireWhy?'disabled':''}>${hireWhy?`<span class="hw">${hireWhy}</span>`:`<b class="plus">+</b><img src="${ui('ui_icon_coin')}">${fmt(hc).slice(1)}`}</button></div>`}
 <div class="ctl"><div class="tog" id="tog"><div class="knob" style="transform:translateX(${[0,41,83][[1,10,999].indexOf(mult)]}px)"></div><span data-m="1" class="${mult===1?'on':''}">x1</span><span data-m="10" class="${mult===10?'on':''}">x10</span><span data-m="999" class="${mult===999?'on':''}">MAX</span></div>
 <button class="up ${can?'glow':''}" id="ub" ${can?'':'disabled'}>${max?'MAX LEVEL':can?`UPGRADE${k>1?' ×'+k:''}<small><img src="${ui('ui_icon_coin')}">${fmt(c).slice(1)}</small>`:`UPGRADE<small>Need ${need} more</small>`}</button></div>
 <div class="tiers">${CFG.tierLevels.map(L=>`<div class="${lv>=L?'done':''}"><b>${lv>=L?'✓':'Lv'} ${L}</b><span><strong>${d.tierInfo[L].name}</strong> · ${d.tierInfo[L].effect}<br><span style="color:var(--dim)">${d.tierInfo[L].art}</span></span></div>`).join('')}</div>
 <div class="desc">${d.desc||''}</div>`;
 $('#sx').onclick=closeSheet;$('#ub').onclick=()=>doUpgrade(i,mult===999?CFG.maxLevel:mult);if($('#hb'))$('#hb').onclick=()=>hire(i);if($('#ua'))$('#ua').onclick=()=>unassign(i);
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
function openDock(refresh){const el=$('#sheet');sheetFor={dock:1,k:refresh&&sheetFor?sheetFor.k:null};const sh=S.ship;
 const rows=DOCK_TRACKS.map(t=>{const lv=dockLvl(t.id),c=dockCost(t.id),max=lv>=CFG.dock.maxLevel,can=!max&&S.money>=c,nl=Math.ceil((lv+1)/10)*10;
  const eff=t.id==='crane'?`Load ${num(loadRate())}/min · ${(CRANE_CYCLE/craneSpeedMul()).toFixed(1)}s cycle`:t.id==='crew'?`${2+Math.floor(lv/10)} crew · +${Math.round(CFG.dock.crewSpeed*(lv-1)*100)}% load`:t.id==='pad'?`Hold ${holdCap()}`:`Turnaround ${mmss(turnSec())}`;
  return `<div class="drow"><img src="${ui(t.icon)}"><div class="dt"><b>${t.name} <span class="dl">LV ${lv}</span></b><small>${eff}</small>${max?'':`<small class="nl">Next look LV ${nl}: ${t.looks[nl]||''}</small>`}
   <div class="dbar"><i style="width:${lv/CFG.dock.maxLevel*100}%"></i></div></div>
   <button class="dup ${can?'glow':''}" data-t="${t.id}" ${can?'':'disabled'}>${max?'MAX':can?`<img src="${ui('ui_icon_coin')}">${fmt(c).slice(1)}`:`Need ${fmt(c-S.money)}`}</button></div>`}).join('');
 el.innerHTML=`<div class="grab"></div><div class="hdr"><div class="ico"><img src="${ART+DOCK}ui/ui_icon_dock_wrench.webp"></div><div><h2>Cargo Space Dock</h2><div class="sub">In hold ${shipLoad()} · On pad ${loose()}</div></div><button class="x" id="sx" style="margin-left:auto">✕</button></div>${rows}
 <div class="desc">Pt crate ${fmt(CFG.econ.ptValue)} · He-3 canister ${fmt(CFG.econ.heValue)} (30% when packed, 70% on delivery) · refined ×${CFG.econ.refinedMult}. A new look every 10 levels.</div>`;
 $('#sx').onclick=closeSheet;el.querySelectorAll('.dup').forEach(b=>b.onclick=()=>dockUpgrade(b.dataset.t));
 if(!refresh){el.classList.add('open');$('#shade').classList.add('on');sheetOpenedAt=performance.now()}}
function wrenchUI(){let b=$('#wrench');const show=STOPS[site].kind==='dock';
 if(!b){b=document.createElement('button');b.id='wrench';b.onclick=()=>{if(!S.wrench){S.wrench=1;save()}openDock();wrenchUI()};document.body.appendChild(b)}
 b.style.display=show?'block':'none';b.className=S.wrench?'':'first';b.style.backgroundImage=`url(${ART+DOCK}ui/ui_btn_dock_wrench.webp)`}
// a tap in the station-dot row always closes an open sheet first and never reaches the sheet underneath (e.g. the Upgrade button)
let dotSwallow=0;
const inDots=(x,y)=>{const d=$('#dots');if(!d||!d.children.length)return -1;const r=d.getBoundingClientRect(),cy=r.top+r.height/2;if(Math.abs(y-cy)>22||x<r.left-8||x>r.right+8)return -1;const c=d.children[0].getBoundingClientRect();return Math.max(0,Math.min(STOPS.length-1,Math.floor((x-c.left)/c.width)))};
addEventListener('pointerdown',ev=>{if(!$('#sheet').classList.contains('open'))return;const j=inDots(ev.clientX,ev.clientY);if(j<0)return;ev.preventDefault();ev.stopPropagation();dotSwallow=performance.now();closeSheet();goSite(j)},true);
addEventListener('click',ev=>{if(performance.now()-dotSwallow<700){ev.preventDefault();ev.stopPropagation()}},true);
function closeSheet(){sheetFor=null;sd=null;const el=$('#sheet'),sh=$('#shade');el.style.transform='';el.style.transition='';sh.style.opacity='';sh.style.transition='';el.classList.remove('open');sh.classList.remove('on')}
// ----- sheet drag-to-dismiss (grab handle). Touch events (iOS Safari: preventDefault while dragging) + mouse pointer. 1:1 with the finger, backdrop fades;
// release past 30% of the height or a flick closes in 250 ms ease-out, otherwise springs back. Tapping the backdrop still closes.
let sd=null;
function sdStart(y,target){const el=$('#sheet');if(!el.classList.contains('open'))return;const onHandle=!!(target&&target.closest&&(target.closest('.grab')||target.closest('.hdr')));
 sd={y0:y,dy:0,h:el.offsetHeight||1,active:false,handle:onHandle,hist:[[performance.now(),y]]}}
function sdMove(y,e){if(!sd)return false;const el=$('#sheet'),dy=y-sd.y0;sd.hist.push([performance.now(),y]);if(sd.hist.length>6)sd.hist.shift();
 if(!sd.active){if(dy>6&&(sd.handle||el.scrollTop<=0)){sd.active=true;el.style.transition='none';$('#shade').style.transition='none'}else{if(Math.abs(dy)>6&&!sd.handle)sd=null;return false}}
 const d=Math.max(0,y-sd.y0);sd.dy=d;el.style.transform=`translateY(${d}px)`;$('#shade').style.opacity=(0.35*(1-Math.min(1,d/sd.h))).toFixed(3);if(e&&e.cancelable)e.preventDefault();return true}
function sdEnd(){if(!sd)return;const g=sd;sd=null;if(!g.active)return;const el=$('#sheet'),sh=$('#shade'),b=g.hist[g.hist.length-1],a=g.hist.find(h=>b[0]-h[0]<=100)||b,v=(b[1]-a[1])/Math.max(16,b[0]-a[0]);   // px/ms
 if(g.dy>0.3*g.h||v>0.6){el.style.transition='transform .25s cubic-bezier(0,0,.58,1)';el.style.transform='translateY(100%)';sh.style.transition='opacity .25s ease-out';sh.style.opacity='0';sheetDragClosed=performance.now();setTimeout(()=>{if(!el.classList.contains('open'))return;closeSheet()},250)}
 else{el.style.transition='transform .3s cubic-bezier(.2,1.25,.4,1)';el.style.transform='translateY(0)';sh.style.transition='opacity .3s';sh.style.opacity='.35';setTimeout(()=>{if(!sd){el.style.transition='';el.style.transform='';sh.style.transition='';sh.style.opacity=''}},320)}}
let sheetDragClosed=0;
{const el=$('#sheet');
 // The sheet re-renders its innerHTML on refresh, which detaches the touch target; touch events keep going to that detached node and never bubble.
 // So move/end listeners are bound to the touch target itself at touchstart (works on iOS Safari too), and removed at the end.
 const tm=e=>{if(sd&&e.touches.length===1)sdMove(e.touches[0].clientY,e)},te=e=>{const t=e.currentTarget;t.removeEventListener('touchmove',tm);t.removeEventListener('touchend',te);t.removeEventListener('touchcancel',te);sdEnd()};
 el.addEventListener('touchstart',e=>{if(e.touches.length!==1)return;sdStart(e.touches[0].clientY,e.target);if(!sd)return;const t=e.target;t.addEventListener('touchmove',tm,{passive:false});t.addEventListener('touchend',te);t.addEventListener('touchcancel',te)},{passive:true});
 el.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'){sdStart(e.clientY,e.target);}});
 document.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'&&sd)sdMove(e.clientY,e)});
 document.addEventListener('pointerup',e=>{if(e.pointerType==='mouse')sdEnd()})}
$('#shade').onclick=()=>{if(performance.now()-sheetOpenedAt>400)closeSheet()};
let tt=0,padDip=null;
// Toast: always >= 8 pt below the lowest HUD element showing (stats bar #meters, or the low-power pill #lpw → 18 pt below it, as Art spec'd).
// Re-placed EVERY frame while visible: the pill can appear after the toast (power hysteresis), so a one-off placement could end up under it.
function placeToast(){const t=$('#toast'),vis=e=>{if(!e||!e.offsetParent)return null;const r=e.getBoundingClientRect();return r.height?r:null};
 const m=vis($('#meters')),pr=vis($('#lpw')),g=$('#goal'),gr=g&&+getComputedStyle(g).opacity>0.05?vis(g):null;const SLIDE=10;   // toast slides in from -10px: every clearance includes it so the gap is >=8pt during the slide too
 let top=m?m.bottom+8+SLIDE:0;if(pr)top=Math.max(top,pr.bottom+8+SLIDE);if(gr)top=Math.max(top,gr.bottom+8+SLIDE);
 const v=Math.round(top)+'px';if(t.style.top!==v)t.style.top=v}
function toast(m,tap){const t=$('#toast');t.textContent=m;t.onclick=tap?()=>{t.classList.remove('on');tap()}:null;t.style.pointerEvents=tap?'auto':'';if(E){econ();lowPowerUI()}placeToast();t.classList.add('on');clearTimeout(tt);tt=setTimeout(()=>{t.classList.remove('on');t.style.pointerEvents='';t.onclick=null},2200)}
// =====================================================================
// HUD
// =====================================================================
let shownMoney=0;
const powerShort=()=>!!E&&(LPS.on||(E.limit==='Energy'&&S.pop>=E.cap));   // short when floors are underpowered OR energy can't support the crew (miners about to leave)
// next step the player can actually take toward more power, following the real unlock order (floor below first, then level reqs)
function powerStep(){let i=IDX.nuke,guard=0;
 while(guard++<12){const d=F[i],f=S.f[d.id];
  if(f.built)return{i,kind:'up',text:`upgrade ${d.name.replace(' Power','')} (${fmt(upCost(i))})`};
  const nf=nextFloor(d.b);if(nf&&nf!==d){i=IDX[nf.id];continue}
  if(d.req&&S.f[d.req.floor].lvl<d.req.lvl){const r=IDX[d.req.floor];if(!S.f[d.req.floor].built){i=r;continue}return{i:r,kind:'up',text:`upgrade ${F[r].name.replace(' Plant','')} to Lv${d.req.lvl}`}}
  return{i,kind:'build',text:`build ${d.name.replace(' Power','')} (${fmt(d.cost)})`}}
 return{i:IDX.nuke,kind:'build',text:`build Nuclear (${fmt(F[IDX.nuke].cost)})`}}
function lowPowerUI(){const el=$('#lpw');if(!el)return;const low=powerShort();el.style.display=low?'flex':'none';if(!low)return;
 const t='Low power: '+powerStep().text;if(el.dataset.t!==t){el.dataset.t=t;el.querySelector('span').textContent=t}}
function goNuclear(){const p=powerStep(),d=F[p.i],si=STOPS.findIndex(s=>s.kind==='tower'&&s.bi===d.b);closeSheet();goSite(si);if(S.f[d.id].built)setTimeout(()=>openSheet(p.i),480)}   // opens that exact step: the floor's sheet if built, else its station with the build button
function hud(){const e=E;lowPowerUI();if($('#toast').classList.contains('on'))placeToast();if(sheetFor&&sheetFor.dock){const k=Math.floor(S.money)+'|'+['crane','crew','pad','refuel'].map(dockCost).join(',')+'|'+shipLoad()+'|'+staged()+'|'+S.ship.st;if(k!==sheetFor.k){sheetFor.k=k;openDock(true)}}$('#mval').textContent=fmt(S.money);$('#rate').textContent=S.firstReturn?`cargo ${fmt(e.cargoRate*60)}/min`:`+${fmt(e.ore*60)}/min ore`;
 const lim=e.limit,low=e.power<0.999,m=[['people','ui_icon_people',`${num(S.pop)}/${num(e.cap)}`,lim==='Beds'],['oxygen','ui_icon_oxygen',num(e.oxygen),lim==='Oxygen'],['water','ui_icon_water',num(e.water),lim==='Water'],['energy','ui_icon_energy',`${num(e.energy)}/${num(e.demand)}`,lim==='Energy']];
 const box=$('#meters');if(!box.children.length)box.innerHTML=m.map(r=>`<div class="m glass" data-k="${r[0]}"><img src="${ui(r[1])}"><span></span></div>`).join('');
 m.forEach((r,j)=>{const el=box.children[j];el.querySelector('span').textContent=r[2];el.classList.toggle('lim',!!r[3]&&r[0]!=='energy');el.classList.toggle('low',r[0]==='energy'&&low)});
 goalTick();const s=STOPS[site];$('#sname').textContent=s.name.toUpperCase();
 const dots=$('#dots');if(dots.children.length!==STOPS.length){dots.innerHTML=STOPS.map(()=>'<i><b></b></i>').join('');dots.onclick=ev=>{ev.stopPropagation();if(sheetFor||$('#sheet').classList.contains('open'))closeSheet();const r=dots.children[0].getBoundingClientRect(),j=Math.floor((ev.clientX-r.left)/r.width);goSite(Math.max(0,Math.min(STOPS.length-1,j)))}}   /* fixed-width slots: tap maps to its slot; active pill centred in its slot */[...dots.children].forEach((d,j)=>d.classList.toggle('on',j===site));
 if(sheetFor&&sheetFor.elev!=null&&!document.activeElement.closest?.('#sheet')){const k=Math.floor(S.money)+'|'+elevCost(sheetFor.elev);if(k!==sheetFor.k){openElev(sheetFor.elev);sheetFor.k=k}}
 if(sheetFor&&sheetFor.i!=null&&!document.activeElement.closest?.('#sheet')){const k=JSON.stringify([Math.floor(S.money),upCost(sheetFor.i),hireCost(sheetFor.i),st(sheetFor.i).lvl,st(sheetFor.i).workers,idleResidents(),mult]);if(k!==sheetFor.k){sheetFor.k=k;openSheet(sheetFor.i,true)}}}
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
// Vertical scroll on EVERY station: the topmost thing drawn (tower roof / dock status pill) must be able to clear the HUD.
// hudClear = bottom of the goal card (CSS px include env(safe-area-inset-top)) + 14, converted to logical units.
function hudClear(){const g=$('#goal'),r=g&&g.offsetParent&&g.getBoundingClientRect();const css=r&&r.height?r.bottom:(($('#hud')||{}).getBoundingClientRect?.().bottom||190);return css/SC+14}
function stopTop(s){if(s.kind==='tower'){const n=Math.min(CFG.maxFloors,floorsBuilt(s.bi)+1);return HOR+floorBottom(n-1)*TS-200*TS-70}if(s.kind==='dock')return HOR-412;return HOR-200}   // dock: status pill + ship nose
function maxScroll(){const s=STOPS[site];const top=stopTop(s);let m=Math.max(0,hudClear()-(top+OY));if(s.kind==='tower')m=Math.max(m,-(top+OY)+300);return Math.max(m,60)}   // always at least a little travel so a vertical drag never feels dead
let g0=null,dockPan=0;const PANMAX=60;   // dock stop: sideways pan over the 760-wide art (screen pts)
// Gestures: one set of handlers fed by TOUCH events on touch devices (iOS Safari can cancel touch pointer streams, e.g. after a reload,
// which left drags dead while dot taps still worked) and by POINTER events for mouse/pen only.
let inputReady=false;
function gStart(x,y,shade){if(!inputReady){g0=null;return}if(!shade&&(x<20||x>innerWidth-20)){g0={edge:true};return}g0=shade?{x,y,t:performance.now(),rot0:cam.rot,y0:cam.y,axis:null,hist:[],fromShade:true}:{x,y,t:performance.now(),rot0:cam.rot,y0:cam.y,axis:null,hist:[],pan0:dockPan,onDock:STOPS[site].kind==='dock'&&!cam.anim};if(!shade)cam.vy=0}
function gMove(x,y){if(!g0||g0.edge)return;const dx=x-g0.x,dy=y-g0.y;
 if(!g0.axis&&Math.hypot(dx,dy)>9){g0.axis=Math.abs(dx)>Math.abs(dy)?'x':'y';if(g0.fromShade&&g0.axis==='x')closeSheet();if(g0.fromShade&&g0.axis==='y'){g0=null;return}if(g0.axis==='x'&&g0.onDock&&!((dx>0&&g0.pan0<=-PANMAX+0.5)||(dx<0&&g0.pan0>=PANMAX-0.5)))g0.axis='p';   // pan until the edge; only a NEW swipe from the edge changes station
  if(g0.axis==='x'){if(cam.anim){cam.anim=null;g0.rot0=cam.rot+dx/SC*CFG.rotPerSlot/SPAN}}if(g0.axis==='x'&&hintOn)endHint()}
 if(g0.axis==='p'){const want=g0.pan0-dx/SC;dockPan=Math.max(-PANMAX,Math.min(PANMAX,want));g0.over=want-dockPan;cam.rot=g0.rot0+g0.over*CFG.rotPerSlot/SPAN;return}   // pan the dock to its edge, then the SAME drag carries on into the station swipe (no dead swipes)
 if(g0.axis==='x'){cam.rot=g0.rot0-dx/SC*CFG.rotPerSlot/SPAN;   // straight pan, 1:1 with the finger
 cam.rot=Math.max(-0.06,Math.min((STOPS.length-1)*CFG.rotPerSlot+0.06,cam.rot))}
 if(g0.axis==='y'){cam.y=Math.max(-30,Math.min(maxScroll()+30,g0.y0+dy/SC));g0.hist.push([performance.now(),cam.y]);if(g0.hist.length>6)g0.hist.shift()}}
function gEnd(x,y,cancel){if(!g0||g0.edge){g0=null;return}const g=g0;g0=null;if(g.axis==='p'){if(!g.over)return;const ov=-g.over*SC;let tgt=Math.round(cam.rot/CFG.rotPerSlot);if(!cancel&&Math.abs(ov)>0.2*innerWidth&&tgt===site)tgt=site+(ov<0?1:-1);goSite(tgt);return}
 if(g.axis==='x'){const dx=x-g.x,v=dx/(performance.now()-g.t);let tgt=Math.round(cam.rot/CFG.rotPerSlot);if(!cancel&&(Math.abs(v)>0.3||Math.abs(dx)>0.2*innerWidth)&&tgt===site)tgt=site+(dx<0?1:-1);/* quick flick or ~20% width advances one station */goSite(tgt);return}
 if(g.axis==='y'){const h=g.hist;if(h.length>1){const a=h[0],b=h[h.length-1];cam.vy=(b[1]-a[1])/Math.max(16,b[0]-a[0])*1000}return}
 if(!cancel&&!g.fromShade)tap(toLogical(x,y))}
let tId=null,tLast=null;
// never require touches.length===1: a stale/ghost touch left over from a reload or an interrupted gesture would otherwise block every drag.
// Track the first finger; a second finger joining a live gesture is ignored; a tracked id no longer present is treated as gone.
const tStart=shade=>e=>{if(tId!=null&&[...e.touches].some(q=>q.identifier===tId))return;const t=e.changedTouches[0];tId=t.identifier;tLast=t;gStart(t.clientX,t.clientY,shade)};
cv.addEventListener('touchstart',tStart(false),{passive:true});$('#shade').addEventListener('touchstart',tStart(true),{passive:true});
addEventListener('touchmove',e=>{if(tId==null)return;const t=[...e.changedTouches].find(q=>q.identifier===tId);if(!t)return;tLast=t;gMove(t.clientX,t.clientY);if(g0&&g0.axis&&e.cancelable)e.preventDefault()},{passive:false});
addEventListener('touchend',e=>{if(tId==null)return;const t=[...e.changedTouches].find(q=>q.identifier===tId);if(!t)return;tId=null;gEnd(t.clientX,t.clientY)});
addEventListener('touchcancel',()=>{if(tId==null)return;tId=null;gEnd(tLast?tLast.clientX:0,tLast?tLast.clientY:0,true)});   // snap to the nearest station, never stuck mid-pan
const mouseLike=e=>e.pointerType!=='touch';
cv.addEventListener('pointerdown',e=>{if(mouseLike(e))gStart(e.clientX,e.clientY,false)},{passive:true});
$('#shade').addEventListener('pointerdown',e=>{if(mouseLike(e))gStart(e.clientX,e.clientY,true)});
addEventListener('pointermove',e=>{if(mouseLike(e))gMove(e.clientX,e.clientY)},{passive:true});
addEventListener('pointercancel',e=>{if(mouseLike(e))gEnd(e.clientX,e.clientY,true)});
addEventListener('pointerup',e=>{if(mouseLike(e))gEnd(e.clientX,e.clientY)});
function goSite(k,instant){k=Math.max(0,Math.min(STOPS.length-1,k));const from=cam.rot,to=k*CFG.rotPerSlot;cam.anim=instant?null:{from,to,t0:T,d:0.45};if(instant)cam.rot=to;if(k!==site)dockPan=0;if(k!==site){site=k;cam.y=0;cam.vy=0;const s=STOPS[k];if(siteOpen(s.bi))ensureBuildingArt(s.bi);if(k>=1&&k<=3)ensureBuildingArt(stopOfDock())}hud();wrenchUI()}
function tap(p){const s=STOPS[site],f=stopFrame(site);const lx=(p.x-f.x+(s.kind==='dock'?dockPan:0))/TS,ly=(p.y-(OY+cam.y)-f.y)/TS;
 if(s.kind==='dock'){if(Math.abs(ly+408)<28&&Math.abs(lx)<180&&S.ship.st==='docked'){const L=shipLoad(),Y=L+loose();if(launchShip()){shipAnim.mode='launch';shipAnim.t0=T;shipAnim.smoke=0;toast('🚀 Cargo away · '+L+' of '+Y+' loaded · '+fmt(shipValue(S.ship))+' · back in '+mmss(tripSec(S.ship)/SPEED))}else toast('Nothing in the hold yet. The crane is still loading.')}else openDock();return}
 const bi=s.bi,n=floorsBuilt(bi),fl=BUILDINGS[bi].floors;
 if(n===0){if(siteOpen(bi)&&Math.abs(ly-(emptyFloorSite(bi)?-60:-138))<24&&Math.abs(lx)<160){const nf=nextFloor(bi),i=IDX[nf.id],w=lockReason(i);if(w)toast('🔒 '+w);else buyFloor(i)}else if(!siteOpen(bi))toast(BUILDINGS[bi].soon?'Coming soon':'🔒 Build 3 Life Support floors first');return}
 const k=Math.floor((floorBottom(0)-ly)/120);
 if(lx>=160&&lx<=200&&k>=0&&k<n){openElev(bi);return}
 if(lx>=FX0&&lx<160){if(k>=0&&k<n){const d=fl[k];tapFloor(IDX[d.upper||d.id]);return}
  if(k===n&&fl[n]){const i=IDX[fl[n].id],w=lockReason(i);if(w)toast('🔒 '+w);else buyFloor(i)}}}
// =====================================================================
// LOOP
// =====================================================================
let last=performance.now(),saveAcc=0,hudAcc=0,fpsN=0,fpsT=0;
let scrolledCls=false;
function frame(now){{const g=$('#goal'),r=g&&g.getBoundingClientRect();BAND=r&&r.height?(r.bottom+6)*(cv.width/(cv.clientWidth||1)):0}{const sc=cam.y>60;if(sc!==scrolledCls){scrolledCls=sc;document.body.classList.toggle('scrolled',sc)}}const dt=Math.max(0,Math.min(0.1,(now-last)/1000));last=now;T+=window.__freeze?0:dt;NOW=now;stripTick(now);if($('#toast').classList.contains('on'))placeToast();lpTick(dt,now);if(!window.__freeze&&E)TCK+=dt*truckSpeed();
 if(!cam.anim&&!g0){const P=CFG.rotPerSlot,k=Math.max(0,Math.min(STOPS.length-1,Math.round(cam.rot/P)));if(Math.abs(cam.rot-k*P)>0.0004)goSite(k)}   // never rest half-turned
 if(cam.anim){const a=cam.anim,q=Math.min(1,(T-a.t0)/a.d);cam.rot=a.from+(a.to-a.from)*easeOutCubic(q);if(q>=1){cam.rot=a.to;cam.anim=null}}
 if(!g0&&cam.vy){cam.y+=cam.vy*dt;cam.vy*=Math.pow(0.04,dt);if(Math.abs(cam.vy)<5)cam.vy=0}
 if(!g0||g0.axis!=='y'){const mx=maxScroll();if(cam.y<0){cam.y+=(0-cam.y)*Math.min(1,dt*12);if(cam.y>-0.3)cam.y=0;cam.vy=Math.max(0,cam.vy)}if(cam.y>mx){cam.y+=(mx-cam.y)*Math.min(1,dt*12);cam.vy=Math.min(0,cam.vy)}}
 const gdt=dt*SPEED;step(gdt,true);if(DEV)S.money=Math.max(S.money,1e12);
 shipTick(gnow(),true).forEach(ev=>{if(ev.type==='landed'){shipAnim.mode='land';shipAnim.t0=T;shipAnim.dust=0;toast(`🚀 Cargo delivered to Earth: +${fmt(ev.v)}`);bump();FX.push({type:'dockpop',si:stopOfDock(),x:0,y:-230,v:ev.v,txt:'+'+fmt(ev.v),t:T})}if(ev.type==='ready')toast('🚀 Ship ready to load')});
 crewTick(dt);STOPS.forEach((s,si)=>{if(s.kind==='tower'){const n=floorsBuilt(s.bi);if(n&&Math.abs(stopFrame(si).a)<0.36)elevTick(s.bi,n,dt)}});
 render();hintDraw();hudAcc+=dt;if(hudAcc>0.25){hudAcc=0;hud();hintTick();if(bgDone)BUILDINGS.forEach((b,bi)=>{if(siteOpen(bi)&&!b.dock)ensureBuildingArt(bi)})}saveAcc+=dt;if(saveAcc>5){saveAcc=0;save()}
 fpsN++;fpsT+=dt;if(fpsT>1){dbgText(Math.round(fpsN/fpsT));fpsN=0;fpsT=0}
 requestAnimationFrame(frame)}
// offline catch-up
// Welcome back: display:none unless showing (no invisible hit area ever); shown as the LAST body child on its own layer above the canvas/HUD;
// COLLECT answers pointerup/touchend/click (first wins); dismiss removes pointer events at once and display after the fade.
function showWelcome(){const m=$('#modal'),b=$('#wbok');document.body.appendChild(m);m.classList.add('show');m.offsetWidth;requestAnimationFrame(()=>m.classList.add('on'));
 let done=false;const go=e=>{if(done)return;done=true;if(e&&e.cancelable)e.preventDefault();m.classList.remove('on');m.style.pointerEvents='none';setTimeout(()=>{m.classList.remove('show');m.style.pointerEvents=''},320);g0=null;tId=null;
  const v=S.wbPend||0;S.wbPend=0;S.money+=v;save();hud();bump();moneyPop(v)};
 b.onclick=go;b.onpointerup=go;b.ontouchend=go}
const WB_MIN_SEC=60;
function offline(){const now=Date.now(),rt0=S.rt,away=Math.min(CFG.offlineCapSec,(now-S.rt)/1000*SPEED);let earned=0;const before=S.ship.st,m0=S.money;
 if(away>5){let left=away;while(left>0){const ch=Math.min(10,left);earned+=step(ch,false,CFG.offlineRate);left-=ch}}
 S.gt=gnow();S.rt=now;const ev=shipTick(S.gt,false);ev.forEach(e=>{if(e.type==='landed'){earned+=e.v;FX.push({type:'dock',key:'dust_puff4',t:0})}});
 // Welcome back: everything earned while away (production + cargo that landed) is HELD in S.wbPend and banked only on COLLECT.
 // A pending amount from a reload before collecting is carried over (never lost, never double-paid).
 // Shown only after >=60 real seconds away (wall clock, every mode incl. ?dev=1 / ?speed=N). Shorter gaps bank silently; a carried pending amount is banked too.
 const realAway=(now-rt0)/1000,gained=Math.max(0,S.money-m0);
 if(realAway<WB_MIN_SEC){if((S.wbPend||0)>=1&&!$('#modal').classList.contains('show')){const p=S.wbPend;S.wbPend=0;S.money+=p;moneyPop(p)}}
 else if(gained>=1||(S.wbPend||0)>=1){S.money=m0;S.wbPend=(S.wbPend||0)+gained;$('#wbtext').textContent=`Your base ran for ${mmss(realAway)} while you were away.`;$('#wbamt').textContent='+'+fmt(S.wbPend);showWelcome()}
 save()}
// boot: first screen = core + Life Support; then stream the Mine (preview → starter pack), Habitat, fx in the background
let bgDone=false;
(async function boot(){resize();document.querySelectorAll('img[data-ui]').forEach(im=>im.src=ui(im.dataset.ui));
 const bar=$('#lbar');await Promise.all([loadGroup('core',p=>bar.style.width=(p*80)+'%'),loadGroup('life',p=>{})]);bar.style.width='100%';
 if(SPR.ground_strip&&SPR.ground_strip.ready){GSTRIP.p=1;GSTRIP.done=true;GSTRIP.t0=1}   // painted ground is on the first screen — don't flash the old gray ground
 ensureLook(elevLook(0));
 offline();econ();crewSync();hud();devUI();
 {const r=performance.getEntriesByType('resource'),n=performance.getEntriesByType('navigation')[0];window.__firstScreen={files:r.length+1,bytes:r.reduce((a,x)=>a+x.transferSize,0)+(n?n.transferSize:0)}}const L=$('#load');L.style.pointerEvents='none';L.style.opacity=0;setTimeout(()=>{L.remove();inputReady=true},500);/* the fading loader no longer catches taps; touch input turns on when it is gone */requestAnimationFrame(t=>{last=t;frame(t)});document.fonts&&document.fonts.load('700 22px Rajdhani').catch(()=>{});
 await new Promise(r=>setTimeout(r,400));
 await loadGroup('mine_starter');{const r=performance.getEntriesByType('resource'),n=performance.getEntriesByType('navigation')[0];window.__firstScreenMine={files:r.length+1,bytes:r.reduce((a,x)=>a+(x.transferSize||x.encodedBodySize||0),0)+(n?n.transferSize:0)}}firstScreenDone=true;laterWait.splice(0).forEach(r=>r());loadGroup('mine_later_tunnel_trucks');await loadGroup('hab');await loadGroup('fx2');loadGroup('walkway');loadGroup('mine_later_dump');loadGroup('fx_later_upgrade_burst');loadGroup('floors_later_offscreen');tryJSON(ART+SPR.ground_strip.path+'.json').then(j=>{if(j){GSTRIP.tileWidth=j.tileWidth||GSTRIP.tileWidth;GSTRIP.groundLineY=j.groundLineY??GSTRIP.groundLineY;GSTRIP.h=(j.logicalSize&&j.logicalSize.h)||GSTRIP.h;IMG_SIZE.ground_strip=[GSTRIP.tileWidth,GSTRIP.h,0,0]}});loadGroup('ground_later_strip').then(()=>{const S=SPR.ground_strip;if(S.ready){S.w=GSTRIP.tileWidth;S.h=GSTRIP.h;const im=S.img;Promise.resolve(im&&im.decode?im.decode():null).catch(()=>{}).then(()=>{
   // warm the GPU upload with an invisible draw, then start the 200 ms fade on the NEXT frame: no decode hitch mid-fade
   try{const c=document.createElement('canvas').getContext('2d');c.drawImage(im,0,0,1,1)}catch(e){}requestAnimationFrame(t=>{GSTRIP.t0=t})})}});loadGroup('dock_later_hatch');loadGroup('floors_later_empty');bgDone=true;
 BUILDINGS.forEach((b,bi)=>{if(siteOpen(bi)&&!b.dock)ensureBuildingArt(bi)})})();
// dev mode (?dev=1 on preview only): unlimited money + Max out
function devUI(){if(!DEV)return;const b=document.createElement('button');b.id='devmax';b.textContent='DEV · Max out';b.onclick=maxOut;document.body.appendChild(b)}
function maxOut(){BUILDINGS.forEach(b=>b.soon=false);S.tapped=1;S.firstReturn=1;S.step=GOALS.length-1;F.forEach(d=>{const f=S.f[d.id];if(BUILDINGS[d.b].soon)return;f.built=true;f.lvl=CFG.maxLevel;f.workers=noCrew(d)?0:2});BUILDINGS.forEach(b=>S.elev[b.id]=CFG.elevator.maxLevel);
 for(const t in S.dock)S.dock[t]=CFG.dock.maxLevel;S.pop=Math.max(S.pop,40,F.filter(d=>!d.upper).length*2);for(const k in towerCache)delete towerCache[k];BUILDINGS.forEach((b,bi)=>{if(!b.soon)ensureBuildingArt(bi)});crewSync();save();hud();toast('DEV: everything maxed')}
window.__ps={openSheet,openElev,toast,LPS,placeToast,offline,cam,refineFx,setT:v=>{T=v},sp:()=>truckClock(),pan:v=>{dockPan=v},maxScroll,S,F,E:()=>E,maxOut,openDock:()=>openDock(),econ,step,CFG,goSite,STOPS,SPR,launchShip,buyFloor,doUpgrade,save,cacheHits:()=>cacheHits,elevUpgrade};
