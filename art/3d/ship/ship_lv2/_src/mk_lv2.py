# Lv2 ship = Lv1 (pad 82131aba ship node) + widened cargo section (r x1.10, y 12.8-18.8, 0.7 m tapers),
# 2nd mid-blue stripe band on the cargo collar, one extra crew window (porthole). Scratch only.
import sys, os
from gl import *
LV1=os.environ.get('LV1')=='1'   # LV1=1: scratch Lv1 proof copy = 82131aba ship + the AA2 door only (never committed to launch_pad/)
K=1.0 if LV1 else 1.10; Y0,Y1,TP=12.8,18.8,0.7
BAND=(17.50,18.62); WIN_Y,WIN_A,WIN_R=26.6,-10.0,0.62   # porthole moved off the az -33..-27 vertical pipe (>=6 deg / 0.4 m clear)
j,B=load('pad_raw.glb'); nd=j['nodes'][5]; s=np.array(nd['scale']); t=np.array(nd['translation'])
pr=j['meshes'][5]['primitives'][0]; A=pr['attributes']
P=acc(j,B,A['POSITION']); N=acc(j,B,A['NORMAL']); C=acc(j,B,A['COLOR_0']); I=acc(j,B,pr['indices'])
W=P*s+t; y=W[:,1]; r=np.hypot(W[:,0],W[:,2])
def k_of(y):
    f=np.clip(np.minimum((y-(Y0-TP))/TP,((Y1+TP)-y)/TP),0,1); f=f*f*(3-2*f); return 1+(K-1)*f
import scipy.sparse as sp, scipy.sparse.csgraph as cg
Ii=I.reshape(-1,3); key=np.round(W,3); _,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.ravel(); T_=inv[Ii]; n_=inv.max()+1
g=sp.coo_matrix((np.ones(T_.size*2),(np.r_[T_[:,0],T_[:,1],T_[:,2],T_[:,1],T_[:,2],T_[:,0]],np.r_[T_[:,1],T_[:,2],T_[:,0],T_[:,0],T_[:,1],T_[:,2]])),shape=(n_,n_))
_,lab=cg.connected_components(g); vl=lab[inv]
big=np.bincount(vl).argmax(); ok=np.zeros(len(W),bool)
for c in np.unique(vl):
    mm=vl==c
    if c==big or (y[mm].min()>=Y0-TP and y[mm].max()<=Y1+TP): ok|=mm
# ladder (rails/rungs/cage, az 40-80, r>4.25, y<=22): NEVER radially scaled; Director 10/24: the 0.4 m collar must not clip the climb ->
# push the whole ladder OUT along its axis (az 60) by LADDER_PUSH instead of narrowing the collar
LADDER_AZ, LADDER_PUSH = 60.0, (0.0 if LV1 else float(os.environ.get('LADDER_PUSH', 0.0)))
lad=np.zeros(len(W),bool)
for c in np.unique(vl):
    mm=vl==c; a_=np.degrees(np.arctan2(W[mm,0].mean(),W[mm,2].mean()))
    if 40<a_<80 and r[mm].min()>4.25 and y[mm].max()<=22.0: lad|=mm
m=(r>3.3)&(r<6.0)&ok&~lad   # hull skin (+ parts wholly inside the collar); thin rails/raceways crossing it stay put (collar covers them)
k=np.where(m,k_of(y),1.0); W2=W.copy(); W2[:,0]*=k; W2[:,2]*=k
LU_=np.array([np.sin(np.radians(LADDER_AZ)),0,np.cos(np.radians(LADDER_AZ))]); W2[lad]+=LU_*LADDER_PUSH
print('ladder verts',int(lad.sum()),'pushed',LADDER_PUSH)
print('moved verts',int((k>1.0001).sum()))
# --- new geometry: band (lathe) + porthole
nv=[];nn=[];nc=[];ni=[]
def addtri(verts,norms,col,tris):
    base=sum(len(v) for v in nv); nv.append(np.array(verts,float)); nn.append(np.array(norms,float)); nc.append(np.tile(col,(len(verts),1))); ni.append(np.array(tris)+base)
BLUE=[35,51,141,255]; DARK=[37,41,49,255]; RIM=[114,121,130,255]
SEG=48; R0=4.0*K+0.035
for (ya,yb) in ([] if LV1 else [BAND]):
    vs=[];ns=[];tr=[]
    for i in range(SEG+1):
        a=2*np.pi*i/SEG; c,sn=np.cos(a),np.sin(a)
        vs+= [(R0*sn,ya,R0*c),(R0*sn,yb,R0*c)]; ns+=[(sn,0,c)]*2
    for i in range(SEG): q=2*i; tr+=[(q,q+2,q+1),(q+1,q+2,q+3)]
    # top/bottom lips
    addtri(vs,ns,BLUE,tr)
def disk(rad,off,col,yc,ang,rr,nseg=16):
    a=np.radians(ang); nrm=np.array([np.sin(a),0,np.cos(a)]); tg=np.array([np.cos(a),0,-np.sin(a)]); up=np.array([0,1,0.])
    ctr=np.array([0,yc,0])+nrm*(rr+off); vs=[ctr];tr=[]
    for i in range(nseg): th=2*np.pi*i/nseg; vs.append(ctr+rad*(np.cos(th)*tg+np.sin(th)*up))
    for i in range(nseg): tr.append((0,1+i,1+(i+1)%nseg))
    addtri(vs,[nrm]*len(vs),col,tr)
if not LV1: disk(WIN_R+0.14,0.03,RIM,WIN_Y,WIN_A,4.0); disk(WIN_R,0.05,DARK,WIN_Y,WIN_A,4.0)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lv2_details.py')).read())   # collar lips/pods/latches + door fill
if not nv: nv,nn,nc,ni=[np.zeros((0,3))],[np.zeros((0,3))],[np.zeros((0,4))],[np.zeros((0,3),int)]
NV=np.concatenate(nv);NN=np.concatenate(nn);NC=np.concatenate(nc).astype(np.uint8);NI=np.concatenate(ni)
# winding: make outward-facing CCW
def fixw(V,Nr,T):
    out=[]
    for a_,b_,c_ in T:
        n=np.cross(V[b_]-V[a_],V[c_]-V[a_]); out.append((a_,b_,c_) if n@Nr[a_]>0 else (a_,c_,b_))
    return np.array(out)
NI=fixw(NV,NN,NI.reshape(-1,3)).ravel()
# assemble new buffers for mesh 5 (positions back to quant units)
Pn=np.concatenate([W2,NV]); Qn=((Pn-t)/s).astype(np.float32)
Nn=np.concatenate([N.astype(np.float32) if N.dtype==np.float32 else N.astype(np.float32)/127.0,NN.astype(np.float32)])
Cn=np.concatenate([C,NC]).astype(np.uint8); In=np.concatenate([I.ravel().astype(np.uint32),NI.astype(np.uint32)+len(W2)])
print('N dtype',N.dtype,'C',C.dtype,'tris +',len(NI)//3)
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
# cargo door + hold markers out with the collar
d=j['nodes'][24]; tr_=np.array(d['translation']); rel=tr_-np.array([0,0,-13.0]); rel[[0,2]]*=K; d['translation']=(rel+[0,0,-13.0]).tolist()
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cargo_door.py')).read())   # AA2 cargo-door spec (closed panel) -> mesh 6
for nn_ in j['nodes']:
    if nn_.get('name') in ('Ladder_Foot','Crew_Path_05'): nn_['translation']=(np.array(nn_['translation'])+LU_*LADDER_PUSH).tolist()
hd=j['nodes'][42]; tr_=np.array(hd['translation']); rel=tr_-np.array([0,0,-13.0]); rel[[0,2]]*=K; hd['translation']=(rel+[0,0,-13.0]).tolist()
BF=np.array([3.854,15.861,-10.775])+LU_*LADDER_PUSH   # crew_boarding Board_Focus_Top (8d2c18d) moved with the ladder
j['nodes'][23]['extras']=({'ship':'LV1 + AA2 cargo door (scratch proof copy, not for commit)','size_m':[8.0,40.25,8.0]} if LV1 else
  {'ship':'LV2 MOCKUP (scratch): Lv1 stainless ship + widened cargo collar (x1.10, 12 boxes, +0.00 m height), lips/pods/latches, 2nd mid-blue band, 5th-seat porthole, AA2 cargo door',
   'size_m':[8.8,40.25,8.8],'boarding':'LADDER (tower/elevator = Lv10 pad)',
   'hatch':{'landing_top_y':21.85,'sill_y':22.11,'top_y':24.90,'w_m':2.15,'h_m':2.79,'az_deg':50.0,'same_as_lv1':True},
   'ladder':{'az_deg':LADDER_AZ,'pushed_out_m':LADDER_PUSH,'foot':[round(v,3) for v in (np.array([4.50333214,0.25,-10.3999996])+LU_*LADDER_PUSH)],'top_y':21.85},
   'Board_Focus_Top':{'translation':[round(v,3) for v in BF],'frame_w':16.1,'note':'Lv1 8d2c18d value + ladder push along az 60'}})
save(sys.argv[1] if len(sys.argv)>1 else 'pad_lv2_raw.glb',j,B)
