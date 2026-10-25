// re-key crane_lift + crane_swing for the new Pick_Point (same names/lengths/key times; eased profiles taken from the old keys)
import fs from 'fs'; import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions'; import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const [IN, OUT, REP] = process.argv.slice(2); const LH = +(process.env.HOIST_HIGH ?? 12.9);
const doc = await io.read(IN); const R = doc.getRoot(); const N = n => R.listNodes().find(x => x.getName() === n);
const cr = N('Crane'), cT = cr.getTranslation(), pp = N('Pick_Point').getTranslation(); const lx = pp[0] - cT[0], lz = pp[2] - cT[2];
const thN = Math.atan2(-lz, lx), rN = Math.hypot(lx, lz); const TH1 = 3.1089 - 2 * Math.PI, R1 = 10.7057, L0 = 15.3, L1 = 14.3;
const q16 = a => [0, Math.round(Math.sin(a / 2) * 32767), 0, Math.round(Math.cos(a / 2) * 32767)];
const ch = (an, node, path) => R.listAnimations().find(a => a.getName() === an).listChannels().find(c => c.getTargetNode().getName() === node && c.getTargetPath() === path).getSampler();
const setOut = (smp, arr, inputFrom) => { const o = smp.getOutput(); const a = doc.createAccessor().setType(o.getType()).setArray(arr).setNormalized(o.getNormalized()).setBuffer(o.getBuffer()); smp.setOutput(a); if (inputFrom) smp.setInput(inputFrom); };
const ease = u => u * u * (3 - 2 * u);
// crane_lift: slew/trolley/hook-yaw constant at the new pick; hoist 15.3 -> LH with the old easing profile
setOut(ch('crane_lift', 'Slew', 'rotation'), new Int16Array(q16(thN))); setOut(ch('crane_lift', 'Trolley', 'translation'), new Float32Array([rN, 1, 0])); setOut(ch('crane_lift', 'Hook', 'rotation'), new Int16Array(q16(-thN)));
{ const hs = ch('crane_lift', 'Hoist', 'scale'), ht = ch('crane_lift', 'Hook', 'translation'); const o = hs.getOutput().getArray(), n = hs.getInput().getCount(); const S = new Float32Array(3 * n), H = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) { const s = (o[3 * i + 1] - L0) / (L1 - L0); const L = L0 + s * (LH - L0); S.set([1, L, 1], 3 * i); H.set([0, -1.3 - L, 0], 3 * i); } setOut(hs, S); setOut(ht, H); }
// crane_swing: progress from the old slew / trolley keys, new start; hoist held at LH then eased down to 14.3 over the last 35 %
{ const sr = ch('crane_swing', 'Slew', 'rotation'), tr = ch('crane_swing', 'Trolley', 'translation'), hr = ch('crane_swing', 'Hook', 'rotation'); const IN91 = sr.getInput(), n = IN91.getCount(), tt = IN91.getArray();
  const so = sr.getOutput().getArray(), to = tr.getOutput().getArray(); let prev = -2.2896; const SL = new Int16Array(4 * n), HK = new Int16Array(4 * n), TR = new Float32Array(3 * n), HS = new Float32Array(3 * n), HT = new Float32Array(3 * n);
  const dT = TH1 - (-2.2896), T = tt[n - 1];
  for (let i = 0; i < n; i++) { let a = 2 * Math.atan2(so[4 * i + 1] / 32767, so[4 * i + 3] / 32767); while (a - prev > Math.PI) a -= 2 * Math.PI; while (a - prev < -Math.PI) a += 2 * Math.PI; prev = a;
    const s = (a + 2.2896) / dT, sr_ = (to[3 * i] - 7.9727) / (R1 - 7.9727); const th = thN + s * (TH1 - thN), r = rN + sr_ * (R1 - rN);
    SL.set(q16(th), 4 * i); HK.set(q16(-th), 4 * i); TR.set([r, 1, 0], 3 * i); const u = Math.max(0, (tt[i] / T - 0.65) / 0.35); const L = LH + ease(Math.min(1, u)) * (L1 - LH); HS.set([1, L, 1], 3 * i); HT.set([0, -1.3 - L, 0], 3 * i); }
  setOut(sr, SL); setOut(hr, HK); setOut(tr, TR); setOut(ch('crane_swing', 'Hoist', 'scale'), HS, IN91); setOut(ch('crane_swing', 'Hook', 'translation'), HT, IN91); }
const ex = cr.getExtras(); const poses = JSON.parse(ex.poses); poses.pick_low = [+thN.toFixed(4), +rN.toFixed(4), 15.3, +(-thN).toFixed(4)]; poses.pick_high = [+thN.toFixed(4), +rN.toFixed(4), LH, +(-thN).toFixed(4)];
cr.setExtras({ ...ex, poses: JSON.stringify(poses), clips: ex.clips + ` | crane_lift/crane_swing re-keyed 10/24 for the z 19.5 pick spur (lift to hoist ${LH}, swing eases down to 14.3 over the last 35 %)` });
for (const k of ['Pick_Point', 'Pick_Point_02']) { const e = { ...N(k).getExtras() }; delete e.baked_clips; N(k).setExtras(e); }
const e2 = { ...N('Pick_Point').getExtras(), baked_clips: 'crane_lift + crane_swing land on this point (re-keyed 10/24)' }; N('Pick_Point').setExtras(e2);
R.listAccessors().forEach(a => { if (a.listParents().length === 1) a.dispose(); });
R.listExtensionsUsed().find(e => e.extensionName === 'EXT_meshopt_compression').setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });
await io.write(OUT, doc); fs.writeFileSync(REP, JSON.stringify({ slew_new: thN, trolley_new: rN, hoist_high: LH, poses }, null, 1)); console.log('ok', thN, rN);
