// Shipyard Bay upgrade path (Jacob 11/15 2:23-2:26 PM PT via Game Director; spec planet-stack/specs/shipyard_bay_upgrades.md).
// The bay has its own upgrade card (styled like the Launch Pad card): Lv1-50, Lv1->2 costs $50k, +10% per level.
//   Every level: ship upgrade time and ship / booster / ring build time x 0.98 (bayTimeMul = 0.98^(lv-1)).
//   Lv10: second welding platform -> 2 rings stacked at once (bayRingLanes).
//   Lv20: 2 bay spots (ship upgrade / ship build side by side, baySlots) + the second ship can be built ($2.5M).
//   Lv30: extended roof -> the booster can be built ($5M; the upright booster on the transporter is 57.7 m, the Lv1-29 door is 48 m).
//   Lv40: second ring rack (12 rings stored instead of 6, bayRackCap).
//   Lv50: gold-tier hall trim (look only).
// Logic only. No new art: the approved hall shows at every level. Each look tier (10/20/30/40/50) calls the handlers registered with
// onLook(tier, fn), so Art's model states (Lv10 platform, Lv20 wide hall, Lv30 wide hall + roof, Lv40 rack, Lv50 trim) plug in there later
// without touching the logic. Rings stay $100k each (the conveyor stays free).
// Save: one additive key, S.bay = { lv, jobs: [{ k, t0, sec, mul }], own: { ship2, booster }, rings }. migrateBay() fills a missing or
// partial key. Game Coder's save migration is not touched. Job stamps are wall-clock ms like the other loop stamps, so shift() moves them
// with every other stamp (shiftTk).
// Ship upgrades (Game Coder's ship_upgrade.mjs / buyShip) are read, never edited: an upgrade in progress takes one bay spot, and its work
// time (S.upg.workSec) is multiplied by bayTimeMul once, the first frame after the job starts and before its work phase begins
// (S.upg.bayK records the factor used).

export const BAY_MAX = 50;
export const BAY_COST0 = 50000;                 // Lv1 -> Lv2
export const BAY_COST_GROWTH = 1.10;            // +10% per level
export const BAY_TIME_MUL_PER_LV = 0.98;        // every level x0.98 build / upgrade time
export const BAY_WELD2_LV = 10, BAY_SLOTS2_LV = 20, BAY_SHIP2_LV = 20, BAY_BOOSTER_LV = 30, BAY_RACK2_LV = 40, BAY_GOLD_LV = 50;
export const BAY_SHIP2_PRICE = 2500000, BAY_BOOSTER_PRICE = 5000000, BAY_RING_PRICE = 100000;
export const BAY_RACK = 6, BAY_RACK2 = 12;
// Base build times in game seconds at Bay Lv1, before bayTimeMul (Game Director 11/15 17:02: second ship 3600 s, booster 5400 s).
// PLACEHOLDER: ring 60 s (no number given yet).
export const BAY_BASE_SEC = { ship2: 3600, booster: 5400, ring: 60 };
export const BAY_LOOK_TIERS = [10, 20, 30, 40, 50];
export const BAY_LOOK_NAMES = { 0: 'approved hall', 10: 'second welding platform', 20: 'wide hall, 2 ship spots', 30: 'wide hall + extended roof', 40: 'second ring rack', 50: 'gold-tier hall trim' };
const SHIP_KINDS = ['ship2', 'booster'];
// ---- Lv20 bay B route (Game Director 11/15 3:40 PM PT) ----
// Bay A is today's spot: the ST-10B parks outside the hall's west side at world x 700 (CFG.shipyardCrawlerStopX). From Bay Lv20, a ship upgrade
// that starts while bay A is taken by a ship / booster build goes to bay B: from the pad along the z -13 trail to the bay A stop, south around the
// hall's SW corner, east along the front apron, then north in through the east front door. Waypoints are Shipyard-local metres (station origin
// world x 800, z 0), measured against the v3 hall (gc/shipyard-v3 0e223393: west wall x -41, facade z +22..+24.6, front door x -42..+41) and
// the old HB-1 (front apron to z +47) with the ST-10B footprint (28 m along x, 31 m across). The apron leg at z +66 clears both halls' fronts
// by >= 3 m. PLACEHOLDER: the stop inside bay B (x +22, z +10) and the door x are data for Art & Animation's Lv20 wide hall (bay B), retune here.
export const BAY_B_ROUTE = { pts: [[-100, -13], [-100, 66], [22, 66], [22, 10]], turnM: 5 };        // jobs that take a bay spot (rings use the welding platforms)

const clampLv = (lv) => Math.max(1, Math.min(BAY_MAX, Math.floor(+lv) || 1));
export const bayCost = (lv) => (lv | 0) >= BAY_MAX ? 0 : Math.round(BAY_COST0 * BAY_COST_GROWTH ** (clampLv(lv) - 1));   // the step lv -> lv + 1
export const bayTotalTo = (lv) => { let s = 0; for (let i = 1; i < clampLv(lv); i++) s += bayCost(i); return s; };
export const bayTimeMul = (lv) => BAY_TIME_MUL_PER_LV ** (clampLv(lv) - 1);
export const baySlots = (lv) => clampLv(lv) >= BAY_SLOTS2_LV ? 2 : 1;
export const bayRingLanes = (lv) => clampLv(lv) >= BAY_WELD2_LV ? 2 : 1;
export const bayRackCap = (lv) => clampLv(lv) >= BAY_RACK2_LV ? BAY_RACK2 : BAY_RACK;
export const bayLookTier = (lv) => BAY_LOOK_TIERS.reduce((a, t) => (clampLv(lv) >= t ? t : a), 0);
const MILESTONES = [[BAY_WELD2_LV, 'Second welding platform'], [BAY_SLOTS2_LV, '2 ship spots + second ship'], [BAY_BOOSTER_LV, 'Extended roof + booster'],
  [BAY_RACK2_LV, 'Second ring rack (12)'], [BAY_GOLD_LV, 'Gold-tier hall trim']];
const GATE_POP = { [BAY_WELD2_LV]: '2 welding platforms', [BAY_SLOTS2_LV]: '2 ship spots · second ship unlocked', [BAY_BOOSTER_LV]: 'Extended roof · booster unlocked',
  [BAY_RACK2_LV]: 'Ring rack 12', [BAY_GOLD_LV]: 'Gold-tier hall' };

export function migrateBay(S) {   // additive: never removes or renames another key
  const b = S.bay && typeof S.bay === 'object' ? S.bay : (S.bay = {});
  b.lv = clampLv(b.lv);
  if (!Array.isArray(b.jobs)) b.jobs = [];
  b.jobs = b.jobs.filter(j => j && typeof j.k === 'string' && j.t0 > 0 && j.sec > 0);
  if (!b.own || typeof b.own !== 'object') b.own = {};
  b.own.ship2 = b.own.ship2 ? 1 : 0; b.own.booster = b.own.booster ? 1 : 0;
  b.rings = Math.max(0, Math.floor(+b.rings) || 0);
  return b;
}

const CSS = `#bayTgls{display:flex;flex-direction:column;align-items:stretch;gap:8px;margin-top:12px}#bayTgls[hidden]{display:none}
#bayTgls .tgl{box-sizing:border-box;width:100%;margin:0;flex:none;border:0;background:none;color:#eafcff;font:700 12px/1.2 system-ui;font-stretch:condensed;letter-spacing:.1em;text-align:left;cursor:pointer}
#bayTgls .tgl.shipup{display:grid;grid-template-columns:1fr auto;grid-template-rows:auto auto;height:auto;min-height:44px;padding:6px 2px;column-gap:8px;row-gap:3px;align-items:center}
#bayTgls .tgl.shipup .tg-lab{grid-column:1;grid-row:1;white-space:nowrap}
#bayTgls .su-meta{grid-column:1;grid-row:2;margin:0;font:700 11px/1.2 system-ui;letter-spacing:.02em;color:#7ff3ff;font-variant-numeric:tabular-nums;white-space:nowrap}
#bayTgls .su-go{grid-column:2;grid-row:1 / span 2;margin:0;min-width:84px;padding:10px 8px;text-align:center;font:800 11px/1 system-ui;letter-spacing:.1em;color:#04202c;background:linear-gradient(180deg,#7fe6ff,#2fbdf0);clip-path:polygon(6px 0,100% 0,100% calc(100% - 6px),calc(100% - 6px) 100%,0 100%,0 6px)}
#bayTgls .tgl:not(.afford) .su-go{background:#232a38;color:#9aa1ae}
#bayTgls .tgl.afford .su-go{animation:bayAfford 1.5s ease-in-out infinite}
@keyframes bayAfford{0%,100%{filter:brightness(1)}50%{filter:brightness(1.45) saturate(1.3)}}
@media (prefers-reduced-motion:reduce){#bayTgls .tgl.afford .su-go{animation:none;filter:brightness(1.25)}}
#upBig.bayBig{white-space:normal;overflow-wrap:anywhere}#upBig.bayBig small{display:block;margin:5px 0 0;white-space:normal}`;   /* bay card only: the label wraps under the % so it can't run past the panel */

export function createBayUpgrades(getS) {
  const A = { D: null, lookTier: -1, looks: Object.fromEntries(BAY_LOOK_TIERS.map(t => [t, []])), lookAny: [], lookLog: [], row: null, glowT: null, lastDone: [] };
  const S = () => getS();
  const bay = () => migrateBay(S());

  function lvNow() {   // ?baylv=N (dev QA, read from QD like ?padlv) or S.bay.lv
    const q = A.D && A.D.QD && A.D.QD.get('baylv');
    if (q != null && q !== '' && isFinite(+q) && +q >= 1) return clampLv(q);
    return bay().lv;
  }
  const locked = () => !!(A.D && !A.D.isBuilt('yard'));   // the hall must be built first
  const shipUpBusy = () => !!(A.D && A.D.shipUpgradeBusy());
  const jobsOf = (ks) => bay().jobs.filter(j => ks.includes(j.k));
  function slotsUsed() { return (shipUpBusy() ? 1 : 0) + jobsOf(SHIP_KINDS).length; }
  function spotsTaken() { const t = new Set(jobsOf(SHIP_KINDS).map(j => j.spot || 'A')); const u = S().upg; if (shipUpBusy() && u) t.add(u.bayB ? 'B' : 'A'); return t; }
  function freeSpot(lv = lvNow()) { const t = spotsTaken(); return !t.has('A') ? 'A' : (baySlots(lv) > 1 && !t.has('B') ? 'B' : null); }
  function why(k, lv = lvNow()) {   // every reason a build can't start now ([] = it can)
    const b = bay(), r = [], D = A.D; if (!D) return ['not ready'];
    if (locked()) r.push('Build the Shipyard first');
    if (k === 'ship2' || k === 'booster') {
      const gate = k === 'ship2' ? BAY_SHIP2_LV : BAY_BOOSTER_LV;
      if (lv < gate) r.push(k === 'ship2' ? `Needs Bay Lv ${gate}` : `Needs Bay Lv ${gate} (extended roof)`);
      if (b.own[k]) r.push('Already built'); else if (jobsOf([k]).length) r.push('Already building');
      if (slotsUsed() >= baySlots(lv)) r.push(`Bay full (${slotsUsed()}/${baySlots(lv)} spots)`);
    } else if (k === 'ring') {
      const rj = jobsOf(['ring']).length;
      if (b.rings + rj >= bayRackCap(lv)) r.push(`Ring rack full (${bayRackCap(lv)})`);
      if (rj >= bayRingLanes(lv)) r.push(bayRingLanes(lv) > 1 ? 'Both welding platforms busy' : 'Welding platform busy');
    } else return ['unknown build'];
    const c = price(k); if (!D.canPay(c)) r.push('Need ' + D.fmt(c));
    return r;
  }
  const price = (k) => k === 'ship2' ? ((A.D && A.D.CFG && A.D.CFG.econ && +A.D.CFG.econ.p2Prices.ship2) || BAY_SHIP2_PRICE) :   // CFG.econ.p2Prices.ship2 (2.5M) is the source
    k === 'booster' ? BAY_BOOSTER_PRICE : BAY_RING_PRICE;
  function start(k) {   // logic entry for a ship / booster / ring build (no button yet; QA hook and the future build UI call this)
    const D = A.D, w = why(k); if (w.length) return { ok: false, why: w };
    const t = D.nowMs(), lv = lvNow(), mul = bayTimeMul(lv), c = price(k); D.settle(t); D.pay(c);
    const j = { k, t0: t, sec: +(BAY_BASE_SEC[k] * mul).toFixed(3), mul: +mul.toFixed(6) }; if (SHIP_KINDS.includes(k)) j.spot = freeSpot(lv) || 'A'; bay().jobs.push(j);
    D.save(); D.refresh(); D.logU('upgrade', `Shipyard: ${k === 'ship2' ? 'second ship' : k} build started (${D.fmt(c)}, ${Math.round(j.sec)} s)`);
    return { ok: true, job: Object.assign({}, j) };
  }
  function tick(t) {   // every frame: finish due jobs, scale a new ship upgrade's work time once
    const D = A.D; if (!D) return; const s = S(), b = bay(); let ch = false;
    for (let i = b.jobs.length - 1; i >= 0; i--) { const j = b.jobs[i]; if (t < j.t0 + j.sec * 1000) continue;
      b.jobs.splice(i, 1); ch = true; A.lastDone.push({ k: j.k, at: t });
      if (j.k === 'ring') b.rings = Math.min(b.rings + 1, BAY_RACK2); else b.own[j.k] = 1;
      D.logU('upgrade', `Shipyard: ${j.k === 'ship2' ? 'second ship' : j.k} built`); }
    if (shipUpBusy() && s.upg && !(s.upg.bayK > 0)) {
      const u = (t - s.upg.t0) / 1000, tw0 = D.shipUpgradeWork0();
      if (u < tw0 && s.upg.workSec > 0) { const mul = bayTimeMul(lvNow()); s.upg.bayW0 = +s.upg.workSec; s.upg.workSec = +(s.upg.workSec * mul).toFixed(3); s.upg.bayK = +mul.toFixed(6);
        // bay B: Lv20+, bay A held by a ship / booster build, and the transporter is still on its empty leg to the pad (before pickup; a long
        // frame hitch at the start can't drop the job into the busy bay A). The empty leg is re-posed from bay A, so a late switch only nudges it.
        const e0 = D.suEnv();
        if (u < Math.abs(e0.bayX - e0.padX) / D.driveV && freeSpotForUpgrade() === 'B') { const e = e0; s.upg.bayB = 1; s.upg.bayPadX = +e.padX; s.upg.bayPadZ = +e.padZ; s.upg.bayL = +routeLen(routePts(e.padX, e.padZ)).toFixed(3); } }
      else s.upg.bayK = 1;   // already in (or past) its work phase when first seen (e.g. a save from before this module): left as it was
      ch = true;
    }
    crawlerStop();
    if (ch) { D.save(); D.refresh(); }
  }
  // Game Coder hook API: '' when a ship upgrade may start, else the reason ('Bay full (2/2 spots)'). A ship upgrade needs a free bay spot
  // (A, or B from Lv20); bay builds hold their spot until done. Read-only; his shipUpgradeLocked / shipUpgradeLockReason call it.
  function upgradeBlockReason() { if (!A.D || shipUpBusy() || freeSpotForUpgrade()) return ''; const n = baySlots(lvNow()); return `Bay full (${n}/${n} spot${n > 1 ? 's' : ''})`; }
  function freeSpotForUpgrade() { const t = new Set(jobsOf(SHIP_KINDS).map(j => j.spot || 'A')); return !t.has('A') ? 'A' : (baySlots(lvNow()) > 1 && !t.has('B') ? 'B' : null); }
  // ---- bay B transporter route (data + pose override; Game Coder's ST-10B code is read, not edited) ----
  // The ST-10B schedule (ship_upgrade.mjs schedule / phaseAt) times each drive leg from |bayX - padX|. For a bay-B job, crawlerStop() sets
  // CFG.shipyardCrawlerStopX (which suEnv reads every frame) to padX + the bay-B route length, so the same schedule gives the longer drive at the
  // same 5 m/s; the SU.poseAt wrapper (wrapPose) then re-places the transporter on the route right after his poseAt. The value goes back to the stored
  // original (700) the moment the job ends. Loaded legs (to bay B, back to the pad) follow the route; the empty legs drive straight between
  // bay A's stop and the pad at normal speed (waiting at bay A, then parking there).
  const routePts = (padX, padZ) => [[padX, padZ], ...BAY_B_ROUTE.pts.map(([x, z]) => [A.D.stationX() + x, z])];
  const routeLen = (P) => { let L = 0; for (let i = 1; i < P.length; i++) L += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); return L; };
  function routeAt(P, d) { d = Math.max(0, d); for (let i = 1; i < P.length; i++) { const l = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]);
      if (d <= l || i === P.length - 1) { const f = l > 0 ? Math.min(1, d / l) : 1; return [P[i - 1][0] + (P[i][0] - P[i - 1][0]) * f, P[i - 1][1] + (P[i][1] - P[i - 1][1]) * f]; } d -= l; }
    return P[P.length - 1].slice(); }
  function crawlerStop() {
    const D = A.D, s = S(); if (!D || !D.CFG) return; if (A.stop0 == null) A.stop0 = D.CFG.shipyardCrawlerStopX;
    const want = shipUpBusy() && s.upg && s.upg.bayB && s.upg.bayL > 0 ? s.upg.bayPadX + s.upg.bayL : A.stop0;
    if (D.CFG.shipyardCrawlerStopX !== want) D.CFG.shipyardCrawlerStopX = want;
  }
  const sm = (u) => { u = Math.max(0, Math.min(1, u)); return u * u * u * (u * (u * 6 - 15) + 10); };   // same easing as ship_upgrade.mjs
  function wrapPose() {   // the only ST-10B hook: wrap SU.poseAt (Game Coder's suggestion). His poseAt runs unchanged (place, setCradle, attach /
    // detach ship); for a bay-B job the wrapper then re-places the drive origin on the route. Nothing else in ship_upgrade.mjs is touched.
    const SU = A.D && A.D.SU; if (!SU || SU.__bayWrapped || typeof SU.poseAt !== 'function') return; const orig = SU.poseAt;
    SU.poseAt = function (u, sch, env) { const r = orig.call(this, u, sch, env); const p = poseBayB(u, sch, env); if (r && p) { r.x = p.x; r.z = p.z; r.bayB = p; } return r; };
    SU.__bayWrapped = 1;
  }
  function poseBayB(u, sch, e) {
    const D = A.D, s = S(), SU = D && D.SU; A.bayB = null; if (!SU || !SU.T || !SU.T.ready || !shipUpBusy() || !(s.upg && s.upg.bayB)) return null;
    const ph = SU.phaseAt(u, sch);
    const P = routePts(s.upg.bayPadX, s.upg.bayPadZ), L = routeLen(P), ax = A.stop0, az = s.upg.bayPadZ, px = s.upg.bayPadX, tA = Math.abs(ax - px) / D.driveV;
    let x, z, d = null;
    if (ph.k === 'to_pad') { const f = (u - (sch.toPad - tA)) / tA; x = ax + (px - ax) * sm(f); z = az; }
    else if (ph.k === 'pickup' || ph.k === 'drop') { x = px; z = az; }
    else if (ph.k === 'to_bay') d = L * sm((u - sch.tToBay0) / sch.toBay);
    else if (ph.k === 'work') d = L;
    else if (ph.k === 'to_pad_back') d = L * (1 - sm((u - sch.tBack0) / sch.back));
    else if (ph.k === 'to_bay_home') { const f = (u - sch.tHome0) / tA; x = px + (ax - px) * sm(f); z = az; }
    else { x = ax; z = az; }
    let yaw = 0;
    if (d != null) { [x, z] = routeAt(P, d); const w = BAY_B_ROUTE.turnM, a = routeAt(P, d - w), b = routeAt(P, d + w); yaw = Math.atan2(-(b[1] - a[1]), b[0] - a[0]); }
    SU.place(x, (e.shipY0 != null ? e.shipY0 : 0) - 0.45, z); SU.T.root.rotation.y = yaw; SU.T.root.updateMatrixWorld(true);
    return (A.bayB = { ph: ph.k, x: +x.toFixed(2), z: +z.toFixed(2), yaw: +yaw.toFixed(3), d: d == null ? null : +d.toFixed(2), L: +L.toFixed(2) });
  }
  function shift(d) { const s = getS(); if (!s || !s.bay || !Array.isArray(s.bay.jobs)) return; for (const j of s.bay.jobs) if (j && j.t0 > 0) j.t0 += d; }

  // ---- look hooks (no art yet: the approved hall stays at every level) ----
  // Named hooks for Art & Animation's bay looks (tonight: Lv20 wide hall with bay B, Lv30 wide hall + extended roof). Each gets (tier, lv, ctx);
  // ctx.hall is the Shipyard station root, ctx.slots / ctx.rack / ctx.lanes the current numbers, ctx.prev the previous tier.
  const onLv10Look = (fn) => onLook(10, fn), onLv20WideHall = (fn) => onLook(20, fn), onLv30ExtendedRoof = (fn) => onLook(30, fn), onLv40Rack = (fn) => onLook(40, fn), onLv50Gold = (fn) => onLook(50, fn);
  function onLook(tier, fn) { if (tier === '*') A.lookAny.push(fn); else if (A.looks[tier]) A.looks[tier].push(fn); else throw new Error('bay look tier must be one of ' + BAY_LOOK_TIERS.join('/') + " or '*'"); }
  function applyLook(force) {   // called on load, on every buy and on setLv. Handlers get (tier, lv, ctx); tier 0 = the approved hall (Lv1-9).
    const lv = lvNow(), tier = bayLookTier(lv); if (!force && tier === A.lookTier) return tier; const prev = A.lookTier; A.lookTier = tier;
    const ctx = { prev, lv, slots: baySlots(lv), rack: bayRackCap(lv), lanes: bayRingLanes(lv), hall: A.D && A.D.hall ? A.D.hall() : null };
    const fns = [...(A.looks[tier] || []), ...A.lookAny]; for (const f of fns) { try { f(tier, lv, ctx); } catch (e) { console.warn('bay look hook', tier, e); } }
    A.lookLog.push({ tier, lv, name: BAY_LOOK_NAMES[tier], handlers: fns.length }); if (A.lookLog.length > 20) A.lookLog.shift();
    return tier;
  }

  // ---- card ----
  const tp = (lv) => Math.round(bayTimeMul(lv) * 100);
  function nextLine(lv, m) {
    if (m) return 'All bay upgrades built';
    const n = MILESTONES.find(([at]) => at > lv); if (!n) return '';
    return n[0] === lv + 1 ? `Next level: ${n[1]}` : `${n[1]} at Lv ${n[0]}`;
  }
  function card() {
    return { name: 'Shipyard Bay', ico: 'shipyard', lock: () => locked(), lockSub: 'Build the Shipyard first',
      lv: () => lvNow(), max: () => lvNow() >= BAY_MAX, cost: () => bayCost(lvNow()), buy: () => buy(),
      big: (m) => { const lv = lvNow(); return [m ? `${tp(lv)}%` : `${tp(lv)}% → ${tp(lv + 1)}%`, 'build + upgrade time']; },
      sub: (m) => { const lv = lvNow(); return `${baySlots(lv)} ship spot${baySlots(lv) > 1 ? 's' : ''} · ring rack ${bayRackCap(lv)}\n${nextLine(lv, m)}`; },
      meter: () => { const lv = lvNow(); return [10, lv >= BAY_MAX ? 10 : (lv - 1) % 10 + 1]; } };   // 10-segment tier meter (like the Drill's 50-level path)
  }
  function buy() {
    const D = A.D, lv = lvNow(), c = bayCost(lv); if (lv >= BAY_MAX || locked() || !D.canPay(c)) return false;
    D.settle(D.nowMs()); D.pay(c); bay().lv = lv + 1; applyLook();
    D.save(); D.refresh();
    D.popAtBuy(GATE_POP[lv + 1] || `Build time ${tp(lv + 1)}%`);
    D.logU('upgrade', `Shipyard Bay Lv ${lv + 1} (${D.fmt(c)}): build + upgrade time ${tp(lv + 1)}%${GATE_POP[lv + 1] ? ' · ' + GATE_POP[lv + 1] : ''}`);
    return true;
  }
  function setLv(lv) { bay().lv = clampLv(lv); applyLook(); if (A.D) { A.D.save(); A.D.refresh(); } return lvNow(); }   // QA

  // the BAY UPGRADE row on the Shipyard card (like PAD UPGRADE on the ship card); cyan pulse on its button while affordable
  function ui(upCur) {
    const D = A.D; if (!D) return;
    if (!document.getElementById('bayCss')) { const st = document.createElement('style'); st.id = 'bayCss'; st.textContent = CSS; document.head.append(st); }
    const bg = document.getElementById('upBig'); if (bg) bg.classList.toggle('bayBig', upCur === 'bayUp');
    const show = upCur === 'soonShipyard' && !locked();
    if (!A.row) { if (!show) return;
      const w = document.createElement('div'); w.id = 'bayTgls';
      const b = document.createElement('button'); b.className = 'tgl shipup'; b.dataset.k = 'bayUp';
      const l = document.createElement('span'); l.className = 'tg-lab'; l.textContent = 'BAY UPGRADE';
      const m = document.createElement('span'); m.className = 'su-meta'; const g = document.createElement('span'); g.className = 'su-go';
      b.append(l, m, g); b.addEventListener('pointerdown', (e) => e.stopPropagation()); b.addEventListener('click', (e) => { e.stopPropagation(); D.openUp('bayUp'); });
      w.append(b); A.row = { w, b, m, g, k: '' }; }
    const R = A.row, sub = document.getElementById('upSub');
    if (show && sub && R.w.previousElementSibling !== sub) sub.insertAdjacentElement('afterend', R.w);
    R.w.hidden = !show; if (!show) return;
    const lv = lvNow(), mx = lv >= BAY_MAX, c = bayCost(lv), ok = !mx && D.canPay(c), k = [lv, mx, c, ok].join('|'); if (k === R.k) return; R.k = k;
    R.m.textContent = mx ? `LV ${lv} · MAX` : `LV ${lv} · ${D.fmt(c)}`; R.g.textContent = mx ? 'MAX' : ok ? 'UPGRADE' : 'NEED ' + D.fmt(c);
    R.b.classList.toggle('afford', ok);
  }

  function install(D) {   // D: main.js deps (see the call site)
    A.D = D; bay();
    D.UP.bayUp = card();
    // world glow (gc-afford): the hall pulses cyan while the next bay level is affordable. Glow-only entry (no tap target, no new tap rect).
    // It yields to the Shipyard card's own ship-upgrade pulse on the same meshes (and is listed before it), so the two never clone one mesh twice.
    const shipT = D.UPT.find(t => t.id === 'shipyard');
    if (shipT && D.GLOW_T) {
      D.UP.bayGlow = { name: 'Shipyard Bay', lv: () => lvNow(), max: () => lvNow() >= BAY_MAX, cost: () => bayCost(lvNow()),
        lock: () => locked() || D.glowWant(shipT) || !!D.GLOW.on[shipT.id] };
      A.glowT = { id: 'bayUp', p: 'bayGlow', site: shipT.site, hl: () => shipT.hl() };
      const i = D.GLOW_T.indexOf(shipT); D.GLOW_T.splice(i < 0 ? D.GLOW_T.length : i, 0, A.glowT);
    }
    wrapPose();
    crawlerStop();   // before the first frame, so a saved bay-B job resumes on its own schedule
    applyLook(true);
  }
  function info() {
    const lv = lvNow(), b = bay();
    return { lv, saved: b.lv, max: BAY_MAX, cost: bayCost(lv), totalTo: bayTotalTo(lv), mul: +bayTimeMul(lv).toFixed(6), timePct: tp(lv), slots: baySlots(lv), slotsUsed: slotsUsed(),
      shipUpgradeBusy: shipUpBusy(), lanes: bayRingLanes(lv), rackCap: bayRackCap(lv), rings: b.rings, own: Object.assign({}, b.own),
      jobs: b.jobs.map(j => Object.assign({ left: A.D ? +Math.max(0, j.t0 + j.sec * 1000 - A.D.nowMs()) / 1000 : null }, j)), lookTier: A.lookTier,
      look: BAY_LOOK_NAMES[A.lookTier], lookLog: A.lookLog.slice(), canStart: { ship2: why('ship2'), booster: why('booster'), ring: why('ring') },
      glow: A.D && A.D.GLOW ? !!A.D.GLOW.on.bayUp : false, locked: locked(), spots: [...spotsTaken()], upgradeSpot: shipUpBusy() && S().upg ? (S().upg.bayB ? 'B' : 'A') : null,
      bayB: A.bayB, crawlerStopX: A.D && A.D.CFG ? A.D.CFG.shipyardCrawlerStopX : null, route: BAY_B_ROUTE };
  }
  return { install, tick, shift, ui, buy, start, why, setLv, lvNow, upgradeBlockReason, onLook, onLv10Look, onLv20WideHall, onLv30ExtendedRoof, onLv40Rack, onLv50Gold, applyLook, info, slotsUsed, routeBayB: BAY_B_ROUTE,
    consts: { BAY_MAX, BAY_COST0, BAY_COST_GROWTH, BAY_TIME_MUL_PER_LV, BAY_SHIP2_PRICE, BAY_BOOSTER_PRICE, BAY_RING_PRICE, BAY_BASE_SEC, BAY_LOOK_TIERS } };
}
