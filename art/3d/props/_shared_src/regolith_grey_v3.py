"""10/24 01:10 (Director): the ore / deposit grey (13,12,11) read as coal. Lift the HT-04 load (heap + rocks + chute_pour / rich chunks),
the Mine Deposit_01/02 rock and the Mine conveyor lumps together to sRGB ~(100, 97, 92) under neutral light.
glTF COLOR_0 is LINEAR: sRGB (100,97,92) -> linear (0.1274, 0.1195, 0.1070) -> u8 ~(32.5, 30.5, 27.3); white base x COLOR_0 = albedo.
Per-vertex variation: the old shade steps are kept (compressed) plus a small positional hash, clamped to +-6 %, R >= G >= B always (no blue).
The deposits' light cracks (SHM_DepositGlow, no COLOR_0) are raised by the same luminance factor as the rock (baseColorFactor and
emissiveFactor x k, hue / alphaMode / everything else unchanged) so they still read lighter than the rock.
COLOR_0 alpha, geometry, morphs, clips, nodes, draws are untouched. Works on UNPACKED GLBs (pack afterwards; Mine: set_deposit_blend.py).
usage: python3 regolith_grey_v3.py ht04 IN_plain.glb OUT_plain.glb
       python3 regolith_grey_v3.py mine IN_plain.glb OUT_plain.glb"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbskin import GLB
SRGB = np.array((100, 97, 92)) / 255.0
def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def l2s(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)
LIN = s2l(SRGB)                                   # (0.1274, 0.1195, 0.1070)
OLD = np.array((13, 12, 11)) / 255.0
LUM = np.array((0.2126, 0.7152, 0.0722))
K = float(LIN @ LUM / (OLD @ LUM))                # rock luminance lift, also applied to the cracks
VAR = 0.06
def hsh(P):                                       # deterministic per-vertex jitter in [-1, 1]
    s = np.sin(P[:, 0] * 127.1 + P[:, 1] * 311.7 + P[:, 2] * 74.7) * 43758.5453
    return (s - np.floor(s)) * 2 - 1
def grey(Cold, P, amp=0.025):
    lum = (Cold[:, :3].astype(float) / 255) @ LUM
    s_old = lum / (OLD @ LUM)
    s = np.clip(1 + (s_old - 1) * 0.5 + amp * hsh(P), 1 - VAR, 1 + VAR)
    c = np.round(LIN[None] * 255 * s[:, None])
    c[:, 1] = np.minimum(c[:, 1], c[:, 0]); c[:, 2] = np.minimum(c[:, 2], c[:, 1] - 1)   # warm grey, never blue
    out = Cold.copy(); out[:, :3] = np.clip(c, 0, 255).astype(np.uint8); return out
mode, src, dst = sys.argv[1:4]
g = GLB(src); j = g.j; repl = {}; st = {'target_srgb_u8': [100, 97, 92], 'target_linear': [round(x, 4) for x in LIN], 'target_linear_u8': [round(x * 255, 1) for x in LIN], 'K_lum': round(K, 3)}
def check(C, tag):
    c = C[:, :3].astype(int); st[tag + '_verts'] = int(len(c)); st[tag + '_u8_min'] = c.min(0).tolist(); st[tag + '_u8_max'] = c.max(0).tolist()
    st[tag + '_blue_or_cyan_verts'] = int(((c[:, 2] >= c[:, 0]) | (c[:, 2] > c[:, 1]) | (c[:, 1] > c[:, 0])).sum())
    st[tag + '_srgb_mean'] = np.round(l2s(c.mean(0) / 255) * 255).astype(int).tolist()
if mode == 'ht04':
    names = [j['nodes'][n].get('name') for n in j['skins'][0]['joints']]
    ks = [k for k, n in enumerate(names) if n.startswith(('Truck_Load', 'Truck_Pour', 'Truck_Rich'))]
    p = j['meshes'][0]['primitives'][0]; ci = p['attributes']['COLOR_0']
    C = g.acc(ci).copy(); P = g.acc(p['attributes']['POSITION']).astype(float); J = g.acc(p['attributes']['JOINTS_0'])[:, 0]
    sel = np.isin(J, ks); C[sel] = grey(C[sel], P[sel]); repl[ci] = C
    ref = np.zeros(len(C), bool); ref[g.acc(p['indices'])] = True; check(C[sel & ref], 'load')
elif mode == 'mine':
    for nm in ('Deposit_01', 'Deposit_02'):
        n = g.find(nm); p = j['meshes'][j['nodes'][n]['mesh']]['primitives'][0]
        assert j['materials'][p['material']]['name'] == 'SHM_DepositRock'
        ci = p['attributes']['COLOR_0']; C = g.acc(ci).copy(); P = g.acc(p['attributes']['POSITION']).astype(float) + n
        C = grey(C, P, amp=VAR); repl[ci] = C; check(C, nm)   # deposits were one flat colour: full +-6 % positional variation
    n = g.find('Conveyor'); n = n if 'mesh' in j['nodes'][n] else next(c for c in j['nodes'][n]['children'] if 'mesh' in j['nodes'][c])
    p = j['meshes'][j['nodes'][n]['mesh']]['primitives'][0]; ci = p['attributes']['COLOR_0']; C = g.acc(ci).copy(); P = g.acc(p['attributes']['POSITION']).astype(float)
    c = C[:, :3].astype(int); lump = (c[:, 0] <= 16) & (c[:, 0] >= 10) & (c[:, 2] < c[:, 0])   # recolour_conveyor_lumps.py output (13,12,11) x shade; belt is (23,24,26)
    C[lump] = grey(C[lump], P[lump] * 0.01); repl[ci] = C; check(C[lump], 'conveyor_lumps')
    m = next(m for m in j['materials'] if m['name'] == 'SHM_DepositGlow'); pb = m['pbrMetallicRoughness']
    st['crack_base_before'] = pb['baseColorFactor'][:3]; st['crack_emissive_before'] = m['emissiveFactor']
    pb['baseColorFactor'] = [min(1.0, x * K) for x in pb['baseColorFactor'][:3]] + pb['baseColorFactor'][3:]
    m['emissiveFactor'] = [min(1.0, x * K) for x in m['emissiveFactor']]
    st['crack_base_after'] = [round(x, 4) for x in pb['baseColorFactor'][:3]]; st['crack_emissive_after'] = [round(x, 4) for x in m['emissiveFactor']]
_o = g.acc; g.acc = lambda i: repl[i] if i in repl else _o(i)
g.save(dst, {}); print(json.dumps(st))
