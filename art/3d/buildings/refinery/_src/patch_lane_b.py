"""10/24 lane B (Director): station order Life Support 0 | Mine 160 | Refinery 320 | Cargo Space Dock 480 | Launch Pad 640.
PL-1 now ends at the Dock's FROM REFINERY riser vault (Dock Pipe_Refinery, world (494.5, 0.6, -12.6)), so Pipeline_Exit spans 160 m
(was 320 m to the pad). JSON-only patch of refinery_game.glb marker extras (no geometry change; meshopt buffers untouched).
python3 patch_lane_b.py ../refinery_game.glb"""
import json, struct, sys
EXTRAS = {
    'Pipeline_Exit': {'kind': 'pipe_connection', 'lines': ['LOX', 'LCH4'], 'direction': '+X', 'buried': True, 'span_m': 160,
                      'meets': 'Cargo Space Dock Pipe_Refinery', 'meets_world': [494.5, 0.6, -12.6],
                      'route_world': [[335.9, 0.0, -18.62], [480.0, 0.0, -18.62], [494.5, 0.0, -12.6]],
                      'note': 'buried PL-1 leaves the Refinery footprint here and runs +X 160 m (station gap) to the Dock riser vault Pipe_Refinery; '
                              'it no longer continues to the Launch Pad (the Dock feeds the pad). No tanker, no hose cart'},
    'Pipe_TankFarm': {'kind': 'pipe_connection', 'lines': ['LOX', 'LCH4'], 'direction': '+X', 'buried': True,
                      'note': 'PL-1 fuel pipeline head: pipes drop below grade here and run buried along +X (glTF z -18.62) to Pipeline_Exit, then 160 m to the Dock'}}
def patch(path):
    b = open(path, 'rb').read(); jl = struct.unpack('<I', b[12:16])[0]; js = json.loads(b[20:20 + jl]); rest = b[20 + jl:]
    hit = []
    for n in js['nodes']:
        if n.get('name') in EXTRAS: n['extras'] = EXTRAS[n['name']]; hit.append(n['name'])
    gn = js['scenes'][0].get('extras', {}).get('game_nodes')
    if gn:
        g = json.loads(gn); me = g.setdefault('marker_extras', {}); me.update(EXTRAS); js['scenes'][0]['extras']['game_nodes'] = json.dumps(g)
    nj = json.dumps(js, separators=(',', ':')).encode(); nj += b' ' * ((4 - len(nj) % 4) % 4)
    out = b[:12] + struct.pack('<I', len(nj)) + b'JSON' + nj + rest; out = out[:8] + struct.pack('<I', len(out)) + out[12:]
    open(path, 'wb').write(out); print('patched', path, hit, len(out))
if __name__ == '__main__': patch(sys.argv[1])
