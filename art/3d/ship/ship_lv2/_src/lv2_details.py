# Lv2 cargo-ring-section details (exec'd inside mk_lv2.py; uses W2, C, addtri, YS, DH, BAND, LV1). Existing Lv1 swatches only -> 0 draws.
# Read at 375: a weld step at the section's top + bottom, the wider 2nd mid-blue band, strakes + latch pods (all within r 4.0 + 0.25).
STEEL_D=[82,93,107,255]; STEEL_M=[114,121,130,255]; SHADOW=[11,12,15,255]; BLUE_=[35,51,141,255]
LADDER_GAP=(46.0,74.0)   # steps stop either side of the ladder (rails az 56/64)
def arc_band(ya,yb,rr,col,a0,a1,seg,top=None):
    vs=[];ns=[];tr=[]
    for i in range(seg+1):
        a=np.radians(a0+(a1-a0)*i/seg); c_,s_=np.cos(a),np.sin(a)
        vs+=[(rr*s_,ya,rr*c_),(rr*s_,yb,rr*c_)]; ns+=[(s_,0,c_)]*2
    for i in range(seg): q=2*i; tr+=[(q,q+2,q+1),(q+1,q+2,q+3)]
    addtri(vs,ns,col,tr)
    if top is not None:   # flat top ledge back to the skin (the step catches light)
        vs=[];ns=[];tr=[]
        for i in range(seg+1):
            a=np.radians(a0+(a1-a0)*i/seg); c_,s_=np.cos(a),np.sin(a)
            vs+=[(top*s_,yb,top*c_),(rr*s_,yb,rr*c_)]; ns+=[(0,1,0)]*2
        for i in range(seg): q=2*i; tr+=[(q,q+2,q+1),(q+1,q+2,q+3)]
        addtri(vs,ns,col,tr)
def obox(az,yc,w,h,r0,r1,col,faces=(0,1,2)):
    a=np.radians(az); nr=np.array([np.sin(a),0,np.cos(a)]); tg=np.array([np.cos(a),0,-np.sin(a)]); up=np.array([0,1.,0])
    c0=nr*(r0+r1)/2+up*yc; ex=[tg*w/2,up*h/2,nr*(r1-r0)/2]
    for ax in faces:
        for sgn in ((-1,1) if ax!=2 else (1,)):
            n_=ex[ax]/np.linalg.norm(ex[ax])*sgn; o=[e for k2,e in enumerate(ex) if k2!=ax]
            ctr=c0+ex[ax]*sgn; vs=[ctr-o[0]-o[1],ctr+o[0]-o[1],ctr+o[0]+o[1],ctr-o[0]+o[1]]
            addtri(vs,[n_]*4,col,[(0,1,2),(0,2,3)])
STEP_H, STEP_R = 0.26, 4.10        # weld ring: 26 cm tall (reads ~1.5 px at 375), 10 cm proud
def lin8(h):
    c=np.array([int(h[i:i+2],16)/255 for i in (0,2,4)]); c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); return [*np.round(c*255).astype(int),255]
# Bolder pass (A&A 13:36): the cargo ring reads as its own section at 375 -> graphite sleeve (value step vs stainless),
# bright weld rings top + bottom, darker/saturated #687cc4-family band with light-steel edge lines, 3 framed cargo bay panels camera-side.
GRAPH=lin8('353a42'); WELD=lin8('eef1f4'); BLUE_B=lin8('4a5fc0'); BAY_IN=lin8('2b2f35'); BAY_FR=lin8('eef1f4')
BAY_AZ=(-32.0,-2.0,28.0)           # camera side, clear of the ladder gap 46..74; 1.7 m wide x 2.5 m tall
BAY_W, BAY_H, BAY_FW = 1.7, 2.5, 0.10
if not LV1:
    a0,a1=LADDER_GAP[1],LADDER_GAP[0]+360
    arc_band(YS+STEP_H,YS+DH-STEP_H,4.05,GRAPH,a0,a1,28)                 # graphite sleeve; 28 segs -> chord mid 4.028 > hull
    for yl in (YS, YS+DH-STEP_H): arc_band(yl,yl+STEP_H,STEP_R,WELD,a0,a1,15)   # no ledge (tri budget); the bright face carries the read
    arc_band(BAND[0],BAND[1],4.08,BLUE_B,a0,a1,28)                       # band over the sleeve (vertex-aligned, 3 cm out)
    for ye in (BAND[0]-0.05,BAND[1]): arc_band(ye,ye+0.05,4.16,WELD,a0,a1,14)   # thin light-steel edge lines (not cyan)
    yc=YS+DH/2
    for az in BAY_AZ:
        obox(az,yc,BAY_W-2*BAY_FW,BAY_H-2*BAY_FW,4.0,4.10,BAY_IN,faces=(2,))   # recessed dark bay face (flat, behind the frame)
        for (dx,dy,w,h) in ((0,(BAY_H-BAY_FW)/2,BAY_W,BAY_FW),(0,-(BAY_H-BAY_FW)/2,BAY_W,BAY_FW),(-(BAY_W-BAY_FW)/2,0,BAY_FW,BAY_H),((BAY_W-BAY_FW)/2,0,BAY_FW,BAY_H)):
            obox(az+np.degrees(dx/4.1),yc+dy,w,h,4.0,4.17,BAY_FR,faces=(2,))   # bright frame bars, 7 cm proud of the face
# cargo opening fill: Lv1's black [6,7,8] well -> recessed 25 cm, shadow fill #3a3e44 (no black; seen only when the door opens)
C=np.array(C); blk=(C[:,:3]==[6,7,8]).all(1)
if blk.any():
    rr_=np.hypot(W2[blk,0],W2[blk,2]); f=(rr_-0.25)/rr_; W2[blk,0]*=f; W2[blk,2]*=f; C[blk]=SHADOW
print('details: opening verts',int(blk.sum()))
