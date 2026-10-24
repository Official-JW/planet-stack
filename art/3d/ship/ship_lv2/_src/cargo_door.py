# Cargo door = AA2's committed CD-1 (8b3d46c art/3d/buildings/launch_pad/_src/lp_cargo_door.py, launch_pad_game_lv1door.glb c527d5e3), read-only port.
# AA2: DOOR_A 275 deg (Blender XY, pad frame) == glTF azimuth atan2(x,z) 5 deg here; half-angle 23.8 deg on R 4.0 -> chord 3.228 m, along-facets ~3.32 m;
# H 4.80 from sill 12.65 (centre 15.05). Frame/light/hinges/latch sit INSIDE the opening (0..S), geometry follows the hull's facets:
# two sheets either side of the 0.08 m weld seam column at the door centre. Cyan = the ring glow swatch #2fe3ff, painted (emission 0) -> COLOR_0 here, 0 extra draws.
DOOR = dict(
    HW_DEG=23.8, H=4.80, SILL=12.65, R=4.0*K, AZ=5.0,
    INSET=0.02, FRAME_W=0.08, FRAME_PROUD=0.02,
    HINGE_N=3, HINGE_D=0.06, HINGE_L=0.18, HINGE_END=0.15,   # LEFT edge seen from outside, barrels centred on the frame strip
    CYAN_W=0.03, CYAN_PROUD=0.01,                            # 1 cm proud of the frame; top + both sides, none on the bottom
    LATCH=(0.06, 0.20, 0.015), LATCH_IN=0.05,                 # w, h, depth; RIGHT edge, 5 cm in from the frame, mid-height
    SEAM_W=0.02,
    PANEL='8a9097', FRAME='2b2f35', CYAN='2fe3ff', SHADOW='3a3e44', DUST='9a8f80')
def lin(h):
    c=np.array([int(h[i:i+2],16)/255 for i in (0,2,4)]); c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); return np.round(c*255).astype(np.uint8)
def door_mesh(D):
    V=[];Nn_=[];Cc=[];T=[]
    R=D['R']; HW=np.radians(D['HW_DEG']); SA=0.04/R
    ang=np.array([-HW,-SA,SA,HW])                                  # the hull's own columns across the opening (local, 0 = door centre)
    P=np.c_[R*np.sin(ang),R*np.cos(ang)-R]                         # (x,z) local; +Z out, centre of hull at (0,-R)
    L=np.linalg.norm(np.diff(P,axis=0),axis=1); S=L.sum(); cum=np.r_[0,np.cumsum(L)]
    nr=[]
    for i in range(3):
        d=P[i+1]-P[i]; n=np.array([d[1],-d[0]]); n/=np.linalg.norm(n); nr.append(n if n@(P[i]+[0,R])>0 else -n)
    def surf(s,y,dz):           # s = along the facets from the LEFT edge (0..S); mitred offsets at the facet columns like AA2's pt()
        s=min(max(s,0.0),S); i=min(2,int(np.searchsorted(cum,s,side='right')-1)); t=(s-cum[i])/L[i]; p=P[i]+(P[i+1]-P[i])*t; n=nr[i]
        if abs(s-cum[i])<1e-6 and i>0: m=nr[i]+nr[i-1]; m/=np.linalg.norm(m); n=m/(m@nr[i])
        elif abs(s-cum[i+1])<1e-6 and i<2: m=nr[i]+nr[i+1]; m/=np.linalg.norm(m); n=m/(m@nr[i])
        q=p+n*dz; nn=n/np.linalg.norm(n); return (q[0],y,q[1]),(nn[0],0,nn[1])
    def xs(x0,x1): return [x0]+[c for c in cum if x0+1e-4<c<x1-1e-4]+[x1]
    def quad(x0,x1,y0,y1,dz,col,ny=1,shade=None):
        X=xs(x0,x1); nx=len(X)-1; base=len(V)
        for j_ in range(ny+1):
            for x in X:
                y=y0+(y1-y0)*j_/ny; p,n=surf(x,y,dz); V.append(p); Nn_.append(n); Cc.append(shade(x,y) if shade is not None else col)
        for j_ in range(ny):
            for i_ in range(nx):
                q=base+j_*(nx+1)+i_; T.extend([(q,q+1,q+nx+2),(q,q+nx+2,q+nx+1)])
    def walls(x0,x1,y0,y1,dz0,dz1,col):   # rim walls between two offsets
        for y in (y0,y1):                  # bottom/top walls follow the facets
            X=xs(x0,x1); base=len(V)
            for x in X:
                for dz in (dz0,dz1): p,_=surf(x,y,dz); V.append(p); Nn_.append((0,1 if y==y1 else -1,0)); Cc.append(col)
            for k in range(len(X)-1): q=base+2*k; T.extend([(q,q+2,q+3),(q,q+3,q+1)])
        for x in (x0,x1):
            base=len(V); _,n=surf(x,0,0); t=(n[2],0,-n[0]) if x==x1 else (-n[2],0,n[0])
            for y in (y0,y1):
                for dz in (dz0,dz1): p,_=surf(x,y,dz); V.append(p); Nn_.append(t); Cc.append(col)
            T.extend([(base,base+2,base+3),(base,base+3,base+1)])
    H=D['H']; pan,frm,cy,sh,du=(lin(D[k]) for k in ('PANEL','FRAME','CYAN','SHADOW','DUST'))
    rng=np.random.default_rng(7); noise=rng.normal(0,1,(40,40))
    def weather(x,y):   # AA2 LP_DoorPanel: grime toward the sill + lighter worn edges
        u=x/S; v=y/H; n=noise[min(39,int(u*39)),min(39,int(v*39))]
        dust=np.clip(0.45*(1-v)**2+0.06*n,0,0.5); edge=max(0,0.12-min(u,1-u,v,1-v))/0.12
        c=pan*(1+0.05*n)*(1-dust)+du*dust; c=c*(1-0.25*edge)+np.array([185,190,196])*0.25*edge
        return np.clip(np.r_[c,255],40,255).astype(np.uint8)
    fw=D['FRAME_W']; fp=D['FRAME_PROUD']; ins=D['INSET']; G_=np.r_[frm,255]
    lw,lh,ld=D['LATCH']; ls1=S-fw-D['LATCH_IN']; ls0=ls1-lw; ym=H/2; lz0,lz1=ym-lh/2,ym+lh/2; sw=D['SEAM_W']
    for (y0,y1) in ((fw,ym-sw/2),(ym+sw/2,H-fw)):                  # two leaves, 2 cm inside the skin, latch pocket cut out
        quad(fw,ls0,y0,y1,-ins,None,ny=3,shade=weather); quad(ls1,S-fw,y0,y1,-ins,None,ny=1,shade=weather)
        a_,b_=(y0,lz0) if y1<=ym else (lz1,y1); quad(ls0,ls1,a_,b_,-ins,None,ny=1,shade=weather)
    quad(fw,S-fw,ym-sw/2,ym+sw/2,-ins-ld,np.r_[sh,255])            # leaf seam (back plate seen through the 2 cm gap)
    quad(ls0,ls1,lz0,lz1,-ins-ld,G_); walls(ls0,ls1,lz0,lz1,-ins-ld,-ins,G_)                     # latch pocket 1.5 cm deep
    quad(ls0+0.015,ls1-0.015,lz0+0.03,lz1-0.03,-ins-0.005,G_)                                     # latch grip
    for (x0,x1,y0,y1) in ((0,fw,0,H),(S-fw,S,0,H),(fw,S-fw,H-fw,H),(fw,S-fw,0,fw)):                # frame 8 cm, inside the opening
        quad(x0,x1,y0,y1,fp,G_)
    walls(0,S,0,H,-ins,fp,G_); walls(fw,S-fw,fw,H-fw,-ins,fp,G_)
    cw=D['CYAN_W']; cp=fp+D['CYAN_PROUD']; C_=np.r_[cy,255]
    for (x0,x1,y0,y1) in ((fw,fw+cw,fw,H-fw),(S-fw-cw,S-fw,fw,H-fw),(fw+cw,S-fw-cw,H-fw-cw,H-fw)):  # AA2: sides + top, just inside the frame
        quad(x0,x1,y0,y1,cp,C_)
    hl,hd=D['HINGE_L'],D['HINGE_D']; e=D['HINGE_END']
    for yc in (e+hl/2,ym,H-e-hl/2):                                 # 3 barrels at AA2's z: 15 cm in from top/bottom + mid-height
        (cx,_,cz),n=surf(fw/2,0,fp+hd/2); base=len(V)
        for k2 in range(7):
            a=2*np.pi*k2/6
            for yy in (yc-hl/2,yc+hl/2): V.append((cx+hd/2*np.cos(a),yy,cz+hd/2*np.sin(a))); Nn_.append((np.cos(a),0,np.sin(a))); Cc.append(G_)
        for k2 in range(6): q=base+2*k2; T.extend([(q,q+2,q+3),(q,q+3,q+1)])
    V=np.array(V,float); V[:,0]-=0; Nn_=np.array(Nn_,float); Cc=np.array(Cc,np.uint8); T=np.array(T)
    D['S']=S; D['CHORD']=float(np.linalg.norm(P[-1]-P[0]))
    return V,Nn_,Cc,T
dv,dn,dc,dt=door_mesh(DOOR)
dt=fixw(dv,dn,dt)
# s-frame -> centred: the facet polyline is already centred in x (P uses sin(ang)); nothing to shift
d=j['nodes'][24]; a_=np.radians(DOOR['AZ']); d['translation']=[DOOR['R']*np.sin(a_), DOOR['SILL'], -13.0+DOOR['R']*np.cos(a_)]
d['rotation']=[0,float(np.sin(a_/2)),0,float(np.cos(a_/2))]
n6=j['nodes'][6]; s6=np.array(n6['scale']); t6=np.array(n6['translation'])   # keep Lv1's shared quantisation grid (gltfpack)
pr6=j['meshes'][6]['primitives'][0]
pr6['attributes']={'POSITION':addacc(((dv-t6)/s6).astype(np.float32),5126,'VEC3',mm=True),'NORMAL':addacc(dn.astype(np.float32),5126,'VEC3'),
                   'COLOR_0':addacc(dc,5121,'VEC4',norm=True)}
pr6['indices']=addacc(dt.ravel().astype(np.uint32),5125,'SCALAR')
DOOR_OUT={'W_chord':round(DOOR['CHORD'],3),'W_along_facets':round(DOOR['S'],3),'half_angle_deg':DOOR['HW_DEG'],'H':DOOR['H'],'centre_y':DOOR['SILL']+DOOR['H']/2,'az_deg_aa2_frame':275.0,'az_deg':DOOR['AZ'],'R':DOOR['R'],
          'centre_xz_pad':[DOOR['R']*np.sin(a_),-13.0+DOOR['R']*np.cos(a_)],'tris':int(len(dt))}
print('DOOR',DOOR_OUT)
