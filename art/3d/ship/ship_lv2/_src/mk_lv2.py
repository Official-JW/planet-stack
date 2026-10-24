# Lv2 ship = Lv1 (pad 82131aba ship node) made TALLER: an extra cargo ring section DH m tall is inserted at YS (hull stays 8.0 m dia).
# Director/Jacob 10/24 11:22 spec (supersedes the 1.10x collar of 711ecb5): everything above YS (crew deck, hatch, porthole, nose, upper
# cyan rings, landing, ladder top) moves up by DH; ladder rails/cage bars stretch, rungs + cage hoops of the climb are repeated into the
# new span (rung pitch 0.6 -> DH is a multiple of it, so the rung lattice is unbroken). Scratch only; never written to launch_pad/.
import sys, os, json
from gl import *
LV1=os.environ.get('LV1')=='1'   # LV1=1: scratch Lv1 proof copy = 82131aba ship + the AA2 door only
K=1.0                            # no collar (hull stays r 4.0); kept for cargo_door.py
YS=18.30                         # split: clean hull row between the Lv1 rungs 18.05/18.65, above the cargo door (top 17.53), below cyan ring 19.56
DH=0.0 if LV1 else float(os.environ.get('DH',3.6))   # 6 rungs; 3 hold decks of 4 at 2.4 m pitch (see HOLD below)
BAND=(YS+1.15, YS+2.45)          # 2nd mid-blue band (1.30 m, wider than Lv1's) on the new section
WIN_Y,WIN_A,WIN_R=26.6+DH,-10.0,0.62   # porthole off the az -33..-27 vertical pipe, raised with the crew deck
j,B=load('pad_raw.glb'); nd=j['nodes'][5]; s=np.array(nd['scale']); t=np.array(nd['translation'])
pr=j['meshes'][5]['primitives'][0]; A=pr['attributes']
P=acc(j,B,A['POSITION']); N=acc(j,B,A['NORMAL']); C=acc(j,B,A['COLOR_0']); I=acc(j,B,pr['indices'])
W=P*s+t; y=W[:,1]; r=np.hypot(W[:,0],W[:,2])
import scipy.sparse as sp, scipy.sparse.csgraph as cg
Ii=I.reshape(-1,3); key=np.round(W,3); _,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.ravel(); T_=inv[Ii]; n_=inv.max()+1
g=sp.coo_matrix((np.ones(T_.size),(T_.ravel(),np.roll(T_,1,1).ravel())),shape=(n_,n_)); _,lab=cg.connected_components(g); vl=lab[inv]
# 1) stretch: every vertex above the split moves up DH (faces crossing YS = hull skin, strips, pipes, rails, cage bars -> stretch)
W2=W.copy(); W2[y>YS,1]+=DH
# 2) ladder rungs + cage hoops (small components, az 40-80, r>4.25) in [YS-DH, YS) are repeated +DH into the new span
LADDER_AZ=60.0
dupv=[]
for c in np.unique(vl):
    mm=vl==c; a_=np.degrees(np.arctan2(W[mm,0].mean(),W[mm,2].mean()))
    if DH>0 and 40<a_<80 and r[mm].min()>4.25 and y[mm].max()-y[mm].min()<0.3 and y[mm].min()>=YS-DH and y[mm].max()<YS: dupv.append(np.where(mm)[0])
dupv=np.concatenate(dupv) if dupv else np.zeros(0,int)
remap=-np.ones(len(W),int); remap[dupv]=len(W)+np.arange(len(dupv))
dupT=Ii[np.isin(Ii,dupv).all(1)]; dupT=remap[dupT]
W2=np.concatenate([W2, W[dupv]+[0,DH,0]]); N=np.concatenate([N,N[dupv]]); C=np.concatenate([C,C[dupv]]); I=np.concatenate([I.ravel(),dupT.ravel()])
print('stretch DH',DH,'repeated ladder parts verts',len(dupv),'tris',len(dupT))
# --- new geometry
nv=[];nn=[];nc=[];ni=[]
def addtri(verts,norms,col,tris):
    base=sum(len(v) for v in nv); nv.append(np.array(verts,float)); nn.append(np.array(norms,float)); nc.append(np.tile(col,(len(verts),1))); ni.append(np.array(tris)+base)
BLUE=[35,51,141,255]; DARK=[37,41,49,255]; RIM=[114,121,130,255]
def disk(rad,off,col,yc,ang,rr,nseg=12):
    a=np.radians(ang); nrm=np.array([np.sin(a),0,np.cos(a)]); tg=np.array([np.cos(a),0,-np.sin(a)]); up=np.array([0,1,0.])
    ctr=np.array([0,yc,0])+nrm*(rr+off); vs=[ctr];tr=[]
    for i in range(nseg): th=2*np.pi*i/nseg; vs.append(ctr+rad*(np.cos(th)*tg+np.sin(th)*up))
    for i in range(nseg): tr.append((0,1+i,1+(i+1)%nseg))
    addtri(vs,[nrm]*len(vs),col,tr)
if not LV1: disk(WIN_R+0.14,0.03,RIM,WIN_Y,WIN_A,4.0); disk(WIN_R,0.05,DARK,WIN_Y,WIN_A,4.0)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lv2_details.py')).read())   # section seams/band/strakes/latches + door well fill
if not nv: nv,nn,nc,ni=[np.zeros((0,3))],[np.zeros((0,3))],[np.zeros((0,4))],[np.zeros((0,3),int)]
NV=np.concatenate(nv);NN=np.concatenate(nn);NC=np.concatenate(nc).astype(np.uint8);NI=np.concatenate(ni)
def fixw(V,Nr,T):
    out=[]
    for a_,b_,c_ in T:
        n=np.cross(V[b_]-V[a_],V[c_]-V[a_]); out.append((a_,b_,c_) if n@Nr[a_]>0 else (a_,c_,b_))
    return np.array(out)
NI=fixw(NV,NN,NI.reshape(-1,3)).ravel()
Pn=np.concatenate([W2,NV]); Qn=((Pn-t)/s).astype(np.float32)
Nn=np.concatenate([N.astype(np.float32) if N.dtype==np.float32 else N.astype(np.float32)/127.0,NN.astype(np.float32)])
Cn=np.concatenate([C,NC]).astype(np.uint8); In=np.concatenate([I.ravel().astype(np.uint32),NI.astype(np.uint32)+len(W2)])
print('tris added (details)',len(NI)//3,'ship tris',len(In)//3)
def addview(arr,target):
    global B
    off=len(B); off+=(4-off%4)%4; B+= b'\0'*(off-len(B)); B+=arr.tobytes()
    j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':arr.nbytes,**({'target':target} if target else {})}); return len(j['bufferViews'])-1
def addacc(arr,ct,typ,norm=False,mm=False):
    tgt=34963 if typ=='SCALAR' else 34962
    a={'bufferView':addview(np.ascontiguousarray(arr),tgt),'componentType':ct,'count':len(arr),'type':typ}
    if norm:a['normalized']=True
    if mm:a['min']=arr.min(0).tolist();a['max']=arr.max(0).tolist()
    j['accessors'].append(a);return len(j['accessors'])-1
A['POSITION']=addacc(Qn,5126,'VEC3',mm=True); A['NORMAL']=addacc(Nn,5126,'VEC3'); A['COLOR_0']=addacc(Cn,5121,'VEC4',norm=True); pr['indices']=addacc(In,5125,'SCALAR')
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cargo_door.py')).read())   # AA2 cargo-door spec (closed panel, r 4.0) -> mesh 6
# 3) hold slots: 12 = 3 decks x 4 (Lv1's 4 outer slots, Hold_02..05 xz); deck pitch 2.4 m (Lv1 1.95) -> top box top <= 17.55+1.8 = 19.35, section ceiling 18.8+DH
HOLD_Y=[12.75,15.15,17.55]
byname={n.get('name'):i for i,n in enumerate(j['nodes'])}
if not LV1:
    xz=[(j['nodes'][byname['Hold_%02d'%k]]['translation'][0],j['nodes'][byname['Hold_%02d'%k]]['translation'][2]) for k in (2,3,4,5)]
    slots=[(d,x,z) for d in range(3) for (x,z) in xz]
    for k,(d,x,z) in enumerate(slots,1):
        nm='Hold_%02d'%k; nd_={'name':nm,'translation':[x,HOLD_Y[d],z],'extras':{'kind':'hold_slot','box_base':True,'box_yaw_deg':5.0,'deck':d}}
        if nm in byname: j['nodes'][byname[nm]]=nd_
        else: j['nodes'].append(nd_); j['scenes'][0]['nodes'].append(len(j['nodes'])-1)
# 4) nodes above the split move up
for nn_ in j['nodes']:
    tr_=nn_.get('translation')
    if tr_ and nn_.get('name') not in (None,'Ship_Placeholder') and not nn_.get('name','').startswith('Hold_') and 'mesh' not in nn_ and nn_.get('name')!='Cam_Target':
        if 19.0<tr_[1]<45 and abs(tr_[0])<6 and abs(tr_[2]+13)<6: nn_['translation']=[tr_[0],tr_[1]+DH,tr_[2]]; print('moved node',nn_['name'])
LAND,SILL,TOP=21.85+DH,22.11+DH,24.90+DH
BF=[3.854,15.861+DH,-10.775]; TRIG=14.0+DH
trig={"bone":"C1_Hips","alt_bone":"C1_Head","threshold_y_m":round(TRIG,3),"y_space":"pad-local (ladder foot 0.25, deck %.2f)"%LAND,
      "rule":"use Board_Focus until the bone world Y >= threshold, then ease to Board_Focus_Top",
      "note":"Lv1 14.0 m hand-off + DH; fallback times need the crew climb re-key (scratch extension adds DH/1.2 s = %.1f s)"%(DH/1.2)}
H=float(j['nodes'][23]['extras']['size_m'][1]) if False else 40.25
j['nodes'][23]['extras']=({'ship':'LV1 + AA2 cargo door (scratch proof copy, not for commit)','size_m':[8.0,40.25,8.0]} if LV1 else
  {'ship':'LV2 (scratch): Lv1 stainless ship + %.2f m cargo ring section (12 boxes, 3 decks x 4), weld steps + strakes/latches, 2nd mid-blue band, 5th-seat porthole, AA2 cargo door'%DH,
   'size_m':[8.0,round(40.25+DH,3),8.0],'added_height_m':DH,'section_y':[YS,YS+DH],'boarding':'LADDER (tower/elevator = Lv10 pad)',
   'hatch':{'landing_top_y':round(LAND,3),'sill_y':round(SILL,3),'top_y':round(TOP,3),'w_m':2.15,'h_m':2.79,'az_deg':50.0},
   'ladder':{'az_deg':LADDER_AZ,'foot':[4.503,0.25,-10.4],'top_y':round(LAND,3),'rungs_added':int(round(DH/0.6))},
   'Board_Focus_Top':{'translation':[round(v,3) for v in BF],'frame_w':16.1,'trigger':trig},
   'hold':{'decks_y':HOLD_Y,'per_deck':4,'slots':12}})
# 5) per-level pad camera (game keys the camera by ship GLB md5): Lv2's own Cam_Target + frame_w (camfit: >= 6.5 px spare on every edge of
#    the safe bands at 393x852 and 375x667 for pad + tanks + crane + hoses + ship + door). Lv1 keeps (0, 4, -0.7) / 78.25.
if not LV1:
    import math
    ct=j['nodes'][byname['Cam_Target']]; CAM_T,CAM_FW=[0.0,5.5,2.75],84.0
    ct['translation']=CAM_T; ex=ct['extras']; ex['frame_w']=CAM_FW
    ex['distance_m']={k:round(CAM_FW/2/(math.tan(math.radians(19))*(w/h)),3) for k,(w,h) in {'393x852':(393,852),'375x667':(375,667)}.items()}
    ex['lv1_camera']={'translation':[0,4,-0.7],'frame_w':78.25}; ex['note']=ex.get('note','')+' | Lv2 per-level camera (keyed by ship md5)'
save(sys.argv[1] if len(sys.argv)>1 else 'pad_lv2_raw.glb',j,B)
