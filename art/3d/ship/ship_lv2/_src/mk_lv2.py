# Lv2 ship = Lv1 (pad 82131aba ship node) + widened cargo section (r x1.10, y 12.8-18.8, 0.7 m tapers),
# 2nd mid-blue stripe band on the cargo collar, one extra crew window (porthole). Scratch only.
import sys
from gl import *
K=1.10; Y0,Y1,TP=12.8,18.8,0.7
BAND=(17.95,18.65); WIN_Y,WIN_A,WIN_R=26.6,-28.0,0.62
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
m=(r>3.3)&(r<6.0)&ok   # hull skin (+ parts wholly inside the collar); thin rails/raceways crossing it stay put (collar covers them)
k=np.where(m,k_of(y),1.0); W2=W.copy(); W2[:,0]*=k; W2[:,2]*=k
print('moved verts',int((k>1.0001).sum()))
# --- new geometry: band (lathe) + porthole
nv=[];nn=[];nc=[];ni=[]
def addtri(verts,norms,col,tris):
    base=sum(len(v) for v in nv); nv.append(np.array(verts,float)); nn.append(np.array(norms,float)); nc.append(np.tile(col,(len(verts),1))); ni.append(np.array(tris)+base)
BLUE=[35,51,141,255]; DARK=[37,41,49,255]; RIM=[114,121,130,255]
SEG=48; R0=4.0*K+0.035
for (ya,yb) in [BAND]:
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
disk(WIN_R+0.14,0.03,RIM,WIN_Y,WIN_A,4.0); disk(WIN_R,0.05,DARK,WIN_Y,WIN_A,4.0)
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
hd=j['nodes'][42]; tr_=np.array(hd['translation']); rel=tr_-np.array([0,0,-13.0]); rel[[0,2]]*=K; hd['translation']=(rel+[0,0,-13.0]).tolist()
j['nodes'][23]['extras']={'ship':'LV2 MOCKUP (scratch): Lv1 stainless ship + widened cargo collar (x1.10, 12 boxes), 2nd mid-blue band, 5th-seat porthole','size_m':[8.8,40.25,8.8]}
save(sys.argv[1] if len(sys.argv)>1 else 'pad_lv2_raw.glb',j,B)
