# AA2 cargo-door spec (Director-confirmed 10/24 11:22) -> Cargo_Door mesh (mesh 6), closed panel on the collar surface.
# ONE place for every parameter. Colours are COLOR_0 (linear) of the sRGB hexes; all on the ship's one SHM_Stainless primitive set -> 0 draws.
DOOR = dict(
    W=3.44, H=4.80,            # Lv1 cargo opening/leaf size from 82131aba (Cargo_Door mesh, x -1.718..1.720, y 0..4.80)
    R=4.0*K,                   # door sits on the Lv2 collar surface (r 4.40); Lv1 = 4.00
    AZ=5.0,                    # azimuth (deg, atan2(x,z)) = Lv1's Cargo_Door yaw
    INSET=0.02,                # panel inset from hull skin
    FRAME_W=0.08, FRAME_PROUD=0.02,
    HINGE_N=3, HINGE_D=0.06, HINGE_L=0.18, HINGE_END=0.15,   # left edge seen from outside (-local X)
    CYAN_W=0.03, CYAN_PROUD=0.01,                            # proud of the frame; top + both sides, NONE on the bottom
    LATCH=(0.06, 0.20, 0.015),                               # w, h, recess depth; right edge, mid-height
    SEAM_W=0.02,
    PANEL='8a9097', FRAME='2b2f35', CYAN='2fe3ff', SHADOW='3a3e44', DUST='9a8f80')
def lin(h):
    c=np.array([int(h[i:i+2],16)/255 for i in (0,2,4)]); c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); return np.round(c*255).astype(np.uint8)
def door_mesh(D):
    V=[];Nn_=[];Cc=[];T=[]
    R=D['R']
    def surf(x,y,dz):   # local frame: origin = hinge line at sill on the skin, +Z out, cylinder of radius R about local (0,*, -R)
        a=x/R; rr=R+dz; return (rr*np.sin(a), y, rr*np.cos(a)-R), (np.sin(a),0,np.cos(a))
    def quad(x0,x1,y0,y1,dz,col,nx=1,ny=1,shade=None):
        base=len(V)
        for j_ in range(ny+1):
            for i_ in range(nx+1):
                x=x0+(x1-x0)*i_/nx; y=y0+(y1-y0)*j_/ny; p,n=surf(x,y,dz); V.append(p); Nn_.append(n)
                Cc.append(shade(x,y) if shade else col)
        for j_ in range(ny):
            for i_ in range(nx):
                q=base+j_*(nx+1)+i_; T.extend([(q,q+1,q+nx+2),(q,q+nx+2,q+nx+1)])
    def side_walls(x0,x1,y0,y1,dz0,dz1,col):   # rim walls between two offsets (so proud parts read as solid)
        for (xa,ya,xb,yb) in ((x0,y0,x1,y0),(x1,y0,x1,y1),(x1,y1,x0,y1),(x0,y1,x0,y0)):
            base=len(V)
            for (x,y) in ((xa,ya),(xb,yb)):
                for dz in (dz0,dz1):
                    p,_=surf(x,y,dz); V.append(p)
                    d=np.array([yb-ya,0,0]) if xa==xb else np.array([0,np.sign(ya-((y0+y1)/2)) or 1,0])
                    Nn_.append(tuple(np.array([np.sign(xa-(x0+x1)/2),0,0]) if xa==xb else d)); Cc.append(col)
            T.extend([(base,base+2,base+3),(base,base+3,base+1)])
    W,H=D['W'],D['H']; pan,frm,cy,sh,du=(lin(D[k]) for k in ('PANEL','FRAME','CYAN','SHADOW','DUST'))
    rng=np.random.default_rng(7)
    noise=rng.normal(0,1,(40,40))
    def weather(x,y):   # dust toward the sill + worn (lighter) edges; stays mid-gray, never dark
        u=(x+W/2)/W; v=y/H; n=noise[int(u*39),int(v*39)]
        dust=np.clip(0.45*(1-v)**2+0.06*n,0,0.5); edge=max(0,0.12-min(u,1-u,v,1-v))/0.12
        c=pan*(1+0.05*n)*(1-dust)+du*dust; c=c*(1-0.25*edge)+np.array([150,156,164])*0.25*edge
        return np.clip(np.r_[c,255],40,255).astype(np.uint8)
    hw=W/2; fw=D['FRAME_W']
    quad(-hw,hw,0,H,-D['INSET'],None,nx=6,ny=6,shade=weather)                       # panel (inset 2 cm)
    quad(-hw,hw,H/2-D['SEAM_W']/2,H/2+D['SEAM_W']/2,-D['INSET']+0.002,np.r_[sh,255],nx=4)   # horizontal seam line
    fp=D['FRAME_PROUD']
    for (x0,x1,y0,y1) in ((-hw-fw,hw+fw,-fw,0),(-hw-fw,hw+fw,H,H+fw),(-hw-fw,-hw,0,H),(hw,hw+fw,0,H)):   # frame 8 cm all round
        quad(x0,x1,y0,y1,fp,np.r_[frm,255],nx=max(1,int((x1-x0)/0.9)),ny=1); side_walls(x0,x1,y0,y1,-D['INSET'],fp,np.r_[frm,255])
    cw=D['CYAN_W']; cp=fp+D['CYAN_PROUD']
    for (x0,x1,y0,y1) in ((-hw,hw,H-cw,H),(-hw,-hw+cw,0,H-cw),(hw-cw,hw,0,H-cw)):      # cyan: top + sides just inside the frame, none on the bottom
        quad(x0,x1,y0,y1,cp,np.r_[cy,255],nx=max(1,int((x1-x0)/0.9)),ny=1)
    hl,hd=D['HINGE_L'],D['HINGE_D']; e=D['HINGE_END']
    ys=np.linspace(e+hl/2,H-e-hl/2,D['HINGE_N'])
    for yc in ys:   # graphite barrels (6-sided cylinders) on the left frame edge
        cx=-hw-fw/2; p,_=surf(cx,0,0); zc=p[2]+fp+hd/2; base=len(V)
        for k2 in range(7):
            a=2*np.pi*k2/6
            for yy in (yc-hl/2,yc+hl/2): V.append((cx+hd/2*np.cos(a),yy,zc+hd/2*np.sin(a))); Nn_.append((np.cos(a),0,np.sin(a))); Cc.append(np.r_[frm,255])
        for k2 in range(6): q=base+2*k2; T.extend([(q,q+2,q+3),(q,q+3,q+1)])
    lw,lh,ld=D['LATCH']   # recessed latch: graphite pocket face 1.5 cm behind the panel + its 4 walls
    lx=hw-cw-0.12-lw/2
    quad(lx-lw/2,lx+lw/2,H/2-lh/2,H/2+lh/2,-D['INSET']-ld,np.r_[frm,255]); side_walls(lx-lw/2,lx+lw/2,H/2-lh/2,H/2+lh/2,-D['INSET']-ld,-D['INSET']+0.001,np.r_[frm,255])
    # punch the latch pocket out of the panel: panel quads overlapping it are tinted graphite instead (cheap, reads the same at game scale)
    V=np.array(V,float); Nn_=np.array(Nn_,float); Cc=np.array(Cc,np.uint8); T=np.array(T)
    inl=(abs(V[:,0]-lx)<lw/2+0.02)&(abs(V[:,1]-H/2)<lh/2+0.02)&(abs(V[:,2]-(-D['INSET']))<0.12)
    return V,Nn_,Cc,T
dv,dn,dc,dt=door_mesh(DOOR)
dt=fixw(dv,dn,dt)
d=j['nodes'][24]; a_=np.radians(DOOR['AZ']); d['translation']=[DOOR['R']*np.sin(a_), 12.65, -13.0+DOOR['R']*np.cos(a_)]
d['rotation']=[0,float(np.sin(a_/2)),0,float(np.cos(a_/2))]
n6=j['nodes'][6]; s6=np.array(n6['scale']); t6=np.array(n6['translation'])   # keep Lv1's shared quantisation grid (gltfpack)
pr6=j['meshes'][6]['primitives'][0]
pr6['attributes']={'POSITION':addacc(((dv-t6)/s6).astype(np.float32),5126,'VEC3',mm=True),'NORMAL':addacc(dn.astype(np.float32),5126,'VEC3'),
                   'COLOR_0':addacc(dc,5121,'VEC4',norm=True)}
pr6['indices']=addacc(dt.ravel().astype(np.uint32),5125,'SCALAR')
DOOR_OUT={'W':DOOR['W'],'H':DOOR['H'],'centre_y':12.65+DOOR['H']/2,'az_deg':DOOR['AZ'],'R':DOOR['R'],
          'centre_xz_pad':[DOOR['R']*np.sin(a_),-13.0+DOOR['R']*np.cos(a_)],'tris':int(len(dt))}
print('DOOR',DOOR_OUT)
