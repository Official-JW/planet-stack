"""roles.json from roles_table.py (single source of truth).  python3 write_json.py ../roles.json"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import roles_table as RT
from cards3x import TOOL_LABEL, GROUP
out = dict(version=2, generated_by='art/crew/roles/_src/write_json.py', suit='shared crew suit (white shell / graphite / gold visor / cyan glow); role adds accent + tool + helmet badge',
           suit_colors=dict(shell='#eceef1', graphite='#2b3038', visor='#ffae2e', cyan_glow='#3ad0ff'),
           tool_socket='Op_Hand_R', tool_glb='glb/role_kit.glb',
           tool_frame='tool node origin = grip centre; glTF (Y-up): local +Y = handle axis toward the thumb, +X = finger direction (Blender source: +Z / +X)',
           badge_node_note='Badge_<role> = 0.046 m helmet medallion facing local +Z; worn on both helmet temples', roles=[])
for i, k in enumerate(RT.ORDER):
    R = RT.ROLES[k]
    out['roles'].append(dict(id=k, order=i + 1, name=R['name'], group=R['group'], group_label=GROUP[R['group']], job=R['job'],
        flies_after_habitat=R['group'] == 'flight', accent=R['accent'], badge=R['badge'], badge_desc=RT.BADGE_DESC[R['badge']],
        badge_file=f'proofs/badges/badge_{R["badge"]}_256.png', card_file=f'cards/card_{k}.png',
        tool=R['tool'], tool_label=TOOL_LABEL[R['tool']], tool_node=f'Tool_{k}', badge_node=f'Badge_{k}', extras=R['extras']))
json.dump(out, open(sys.argv[1], 'w'), indent=1); print('JSON', sys.argv[1], len(out['roles']))
