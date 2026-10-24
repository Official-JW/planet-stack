#!/bin/bash
S=/workspace/planet-stack/art/3d/crew/boarding/_src
python3 -c "
import numpy as np, json; d=np.load('/tmp/bt_fin_ref.npz'); json.dump({'P':d['P'].round(4).tolist(),'planted':d['planted'].tolist()},open('/tmp/bref_fin.json','w'))"
cd /home/box/apps/gltftools && nice -n 19 env NODE_PATH=$PWD/node_modules node vb.mjs /tmp/bp_fin.glb /tmp/bref_fin.json > /tmp/vb_fin.json
nice -n 19 env NODE_PATH=$PWD/node_modules node dp.mjs /tmp/bp_fin.glb /tmp/pc_fin --every 0.033333 22.3 >/dev/null
nice -n 19 python3 $S/clearance.py /tmp/pc_fin > /tmp/cl_fin.json
nice -n 19 python3 $S/cam_fit.py /tmp/pc_fin 22.3 58.5 > /tmp/camfit_667.json
nice -n 19 python3 $S/cam_fit.py /tmp/pc_fin 22.3 58.5 393 852 184 490 6 > /tmp/camfit_852.json
nice -n 19 python3 $S/deck_check.py /tmp/pc_fin /tmp/padtris_wip.json /tmp/dc_fin.json > /dev/null
echo DONE
