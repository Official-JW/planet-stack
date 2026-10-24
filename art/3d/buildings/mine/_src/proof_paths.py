"""Top-down haul path diagram (glTF x right, glTF z down = toward the station camera).
 1) Blender: orthographic top-down render of the game meshes (+ the shared HT-04 on Path_Load)
    $B -b -P proof_paths.py -- --glb /tmp/mine/raw_pruned.glb --truck /tmp/mine/ht04_raw_pruned.glb --out /tmp/mine/paths_base.png
 2) python3: overlay markers, legs, arrows, operator deck, deposit tap circles and the phone-frame right edge
    python3 proof_paths.py /tmp/mine/paths_base.png /tmp/mine/raw_info.json art/3d/buildings/mine/haul_paths_topdown.png"""
import sys, math
X0, X1, Z0, Z1, PPM = -12.0, 28.0, -12.0, 18.0, 40      # glTF x / z window, pixels per metre
W, H = int((X1 - X0) * PPM), int((Z1 - Z0) * PPM)
def px(x, z): return ((x - X0) * PPM, (z - Z0) * PPM)
try:
    import bpy
    BL = True
except ImportError:
    BL = False
if BL:
    a = sys.argv[sys.argv.index('--') + 1:]; A = {a[i].lstrip('-'): a[i + 1] for i in range(0, len(a) - 1, 2)}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=A['glb'])
    if A.get('truck'):
        bpy.ops.import_scene.gltf(filepath=A['truck']); bpy.context.view_layer.update()
        bpy.data.objects['Truck'].matrix_world = bpy.data.objects['Path_Load'].matrix_world.copy()
    for o in bpy.data.objects:
        if o.animation_data: o.animation_data.action = None
        if o.type == 'ARMATURE':
            for pb in o.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        if o.name.startswith('Tier_'): o.hide_render = True          # tiers hidden by default in game
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'VERTEX'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(X1 - X0, Z1 - Z0); cam.data.clip_end = 500
    cam.location = ((X0 + X1) / 2, -(Z0 + Z1) / 2, 80); cam.rotation_euler = (0, 0, 0)    # Blender y = -glTF z
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.2, 0.2, 0.22, 1)
    sc.render.filepath = A['out']; bpy.ops.render.render(write_still=True)
else:
    import json
    from PIL import Image, ImageDraw, ImageFont
    base, info, out = sys.argv[1:4]
    I = json.load(open(info)); M = I['markers']; HAUL = I['haul']
    im = Image.open(base).convert('RGB'); d = ImageDraw.Draw(im)
    def F(sz):
        try: return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', sz)
        except Exception: return ImageFont.load_default()
    f1, f2, f3 = F(21), F(17), F(15)
    for gx in range(int(X0), int(X1) + 1, 2):                      # 2 m grid ticks
        x, _ = px(gx, Z0); d.line([(x, 0), (x, 8)], fill=(200, 200, 200)); 
        if gx % 4 == 0: d.text((x + 2, 10), 'x%d' % gx, font=f3, fill=(220, 220, 220))
    for gz in range(int(Z0), int(Z1) + 1, 2):
        _, y = px(X0, gz); d.line([(0, y), (8, y)], fill=(200, 200, 200))
        if gz % 4 == 0: d.text((10, y - 8), 'z%d' % gz, font=f3, fill=(220, 220, 220))
    # phone frame right edge at ground level, from the station camera (Cam_Target extras, 393x852 portrait)
    ct = M['Cam_Target']; T = ct['glTF_pos']; ex = ct['extras']; pa = math.radians(ex['pitch_down_deg']); th = math.tan(math.radians(ex['fov_y_deg']) / 2)
    Cc = (T[0], T[1] + ex['distance_m'] * math.sin(pa), T[2] + ex['distance_m'] * math.cos(pa)); asp = 393 / 852
    def sx(x, z):
        r = (x - Cc[0], -Cc[1], z - Cc[2]); zz = -r[1] * math.sin(pa) - r[2] * math.cos(pa)
        return 393 / 2 * (1 + r[0] / (zz * th * asp))
    def edge_x(z):
        lo, hi = -60.0, 90.0
        for _ in range(50):
            m = (lo + hi) / 2; lo, hi = (m, hi) if sx(m, z) < 393 else (lo, m)
        return lo
    EDGE = [(edge_x(z), z) for z in (Z0, Z1)]
    d.line([px(*t) for t in EDGE], fill=(255, 210, 60), width=3)
    lx, lz = edge_x(Z0 + 1.0), Z0 + 1.0
    d.text((px(lx, lz)[0] - 250, px(lx, lz)[1]), 'phone frame right edge ->', font=f2, fill=(255, 210, 60), stroke_width=3, stroke_fill=(0, 0, 0))
    # deposit tap circles + operator deck
    for nm in ('Dep_01', 'Dep_02'):
        p = M[nm]['glTF_pos']; r = float(M[nm]['extras']['radius_m']); c = px(p[0], p[2])
        d.ellipse([c[0] - r * PPM, c[1] - r * PPM, c[0] + r * PPM, c[1] + r * PPM], outline=(80, 255, 140), width=3)
        d.text((c[0] - 30, c[1] - 9), nm, font=f2, fill=(80, 255, 140))
    od = M['Operator_Deck']['glTF_pos']
    d.rectangle([px(od[0] - 1.42, od[2] - 1.75), px(od[0] + 1.42, od[2] + 1.05)], outline=(255, 120, 255), width=3)
    d.text(px(od[0] - 1.4, od[2] - 2.6), 'Operator_Deck', font=f2, fill=(255, 120, 255))
    # legs (exact arcs) + markers
    def leg_pts(p, lg, n=24):
        if lg['type'] == 'straight': return None
        c = lg['centre_glTF']; a0 = math.atan2(p[2] - c[2], p[0] - c[0]); sw = math.radians(lg['sweep_deg'])
        sg = -1 if lg['turn'] == 'left' else 1                         # glTF x-z (z down on the image): a left turn is CCW in Blender = CW here
        return [(c[0] + lg['radius_m'] * math.cos(a0 + sg * sw * k / n), c[2] + lg['radius_m'] * math.sin(a0 + sg * sw * k / n)) for k in range(n + 1)]
    COL = {'Path_Out': (0, 200, 255), 'Path_Ret': (255, 140, 40)}
    for pre in ('Path_Out', 'Path_Ret'):
        seq = HAUL[pre]['markers']; c_ = COL[pre]
        chain = ([M['Path_Load']['glTF_pos']] if pre == 'Path_Out' else []) + [m['glTF'] for m in seq] + ([M['Path_Load_Approach']['glTF_pos']] if pre == 'Path_Ret' else [])
        legs = ([json.loads(M['Path_Load']['extras']['next_leg'])] if pre == 'Path_Out' else []) + [m.get('next_leg') for m in seq]
        for k in range(len(chain) - 1):
            p, q, lg = chain[k], chain[k + 1], legs[k]
            pts = leg_pts(p, lg) if lg else None
            pts = pts or [(p[0], p[2]), (q[0], q[2])]
            d.line([px(*t) for t in pts], fill=c_, width=5)
            m_ = pts[len(pts) // 2] if len(pts) > 2 else ((p[0] + q[0]) / 2, (p[2] + q[2]) / 2)
            if lg and lg.get('length_m'): d.text(px(m_[0] + 0.3, m_[1] - 0.7), '%.1f m' % lg['length_m'], font=f3, fill=c_, stroke_width=2, stroke_fill=(0, 0, 0))
        for m in seq:
            x, z = m['glTF'][0], m['glTF'][2]; cx, cy = px(x, z); yw = math.radians(m['yaw_deg'])
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=c_, outline=(0, 0, 0), width=2)
            hx, hy = cx + 34 * math.cos(yw), cy - 34 * math.sin(yw)          # yaw about +Y: heading (cos, -sin) in x-z; z is image-down
            d.line([(cx, cy), (hx, hy)], fill=(255, 255, 255), width=4)
            d.polygon([(hx + 10 * math.cos(yw), hy - 10 * math.sin(yw)), (hx + 8 * math.cos(yw + 2.2), hy - 8 * math.sin(yw + 2.2)), (hx + 8 * math.cos(yw - 2.2), hy - 8 * math.sin(yw - 2.2))], fill=(255, 255, 255))
            lab = m['name'].replace('Path_', '') + ' %g°' % m['yaw_deg']
            off = {'Path_Ret_01': (-150, -34), 'Path_Ret_02': (-40, -38), 'Path_Ret_03': (-190, -12), 'Path_Out_01': (70, 14), 'Path_Out_02': (-150, 14)}.get(m['name'], (14, -30) if pre == 'Path_Out' else (14, 10))
            d.text((cx + off[0], cy + off[1]), lab, font=f2, fill=c_, stroke_width=3, stroke_fill=(0, 0, 0))
    pa_, pl_ = M['Path_Load_Approach']['glTF_pos'], M['Path_Load']['glTF_pos']            # the short straight reverse (dashed white)
    for k in range(6):
        t0, t1 = k / 6, (k + 0.5) / 6
        d.line([px(pa_[0] + (pl_[0] - pa_[0]) * t0, pa_[2] + 0.5), px(pa_[0] + (pl_[0] - pa_[0]) * t1, pa_[2] + 0.5)], fill=(255, 255, 255), width=4)
    for nm, c_ in (('Path_Load', (255, 255, 255)), ('Path_Load_Approach', (255, 255, 255)), ('Road_Entry', (0, 200, 255)), ('Rich_Pop', (255, 230, 120))):
        p = M[nm]['glTF_pos']; cx, cy = px(p[0], p[2])
        d.rectangle([cx - 7, cy - 7, cx + 7, cy + 7], outline=c_, width=3)
        d.text((cx + {'Path_Load': -110, 'Rich_Pop': -40}.get(nm, -20), cy + {'Rich_Pop': -60, 'Path_Load_Approach': 40, 'Road_Entry': 62, 'Path_Load': 40}.get(nm, 12)), nm, font=f2, fill=c_, stroke_width=3, stroke_fill=(0, 0, 0))
    o, r = HAUL['Path_Out'], HAUL['Path_Ret']
    d.rectangle([0, H - 118, W, H], fill=(18, 20, 26))
    tm_ = HAUL['times']; rl = dict(tm_['return_legs']); ol = dict(tm_['out_legs'])
    d.text((16, H - 110), 'OUT loaded (cyan): Path_Load -> Out_01 -> Out_02 (x 26), dead straight %.1f m: %.2f s' % (o['length_m'], tm_['out_s']), font=f1, fill=(0, 200, 255))
    d.text((16, H - 74), 'RET empty (orange): Ret_01 %.2f + U-turn R4.5 %.2f + %.2f + reverse 1.5 m %.2f = %.2f s' % (rl['Path_Ret_01'], rl['Path_Ret_02'], rl['Path_Ret_03'], rl['reverse Path_Load_Approach -> Path_Load'], tm_['return_s']), font=f1, fill=(255, 140, 40))
    d.text((16, H - 36), 'Mine top-down (glTF x right, z down). Eased 8.33 m/s straights, 4 m/s turns. green = deposit taps, magenta = deck, arrows = yaw', font=f2, fill=(220, 220, 220))
    im.save(out); print('WROTE', out, im.size)
