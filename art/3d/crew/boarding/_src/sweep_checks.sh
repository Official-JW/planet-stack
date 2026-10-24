#!/bin/bash
# usage: sweep.sh TAG G MS QL [extra build args]
S=/workspace/planet-stack/art/3d/crew/boarding/_src; TAG=$1; G=$2; MS=$3; QL=$4; shift 4
cd $S && nice -n 19 python3 build_boarding.py /tmp/suit_A68.npz /tmp/br_$TAG.glb /tmp/bt_$TAG.json --walk-step 2 --climb-step 2 --no-lsq --rung-pair-s 1.0 --climb-gap $G --mantle-scale $MS $( [ "$QL" != "-" ] && echo --queue-lead $QL ) "$@" 2>&1 | grep -E "WARN|CHECKS|clips" | cut -c1-260
nice -n 19 ./pack_boarding.sh /tmp/br_$TAG.glb /tmp/bp_$TAG.glb | tail -1
python3 -c "
import numpy as np, json; d=np.load('/tmp/bt_${TAG}_ref.npz'); json.dump({'P':d['P'].round(4).tolist(),'planted':d['planted'].tolist()},open('/tmp/bref_$TAG.json','w'))"
cd /home/box/apps/gltftools && nice -n 19 env NODE_PATH=$PWD/node_modules node vb.mjs /tmp/bp_$TAG.glb /tmp/bref_$TAG.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('VERIFY', d['bytes'], d['draws'], d['tris'], [(c['name'],c['duration']) for c in d['clips']], d['contacts'], d['planted_foot_slide_percentiles_m'], d['worst_at'])"
nice -n 19 env NODE_PATH=$PWD/node_modules node dp.mjs /tmp/bp_$TAG.glb /tmp/pc_$TAG --every 0.033333 22.3 >/dev/null
nice -n 19 python3 $S/clearance.py /tmp/pc_$TAG
nice -n 19 python3 $S/deck_check.py /tmp/pc_$TAG /tmp/padtris_wip.json /tmp/dc_$TAG.json
