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
STEP_H, STEP_R = 0.16, 4.10        # weld step: 16 cm tall ring, 10 cm proud
STRAKE_AZ=(-40.0,-14.0,24.0)       # vertical strakes on the camera side, clear of door frame top (y<17.53 -> they live in the new section) and the ladder
POD_AZ=(-27.0,10.0)                # latch pods
if not LV1:
    a0,a1=LADDER_GAP[1],LADDER_GAP[0]+360
    for yl in (YS, YS+DH-STEP_H): arc_band(yl,yl+STEP_H,STEP_R,STEEL_D,a0,a1,18,top=4.0)
    arc_band(BAND[0],BAND[1],4.07,BLUE_,a0,a1,24)                       # r 4.07 so the 24-seg chords stay outside the hull facets (no strip-through); skips the ladder
    for az in STRAKE_AZ: obox(az,YS+DH/2,0.22,DH-2*STEP_H,3.98,4.16,STEEL_M)
    for az in POD_AZ:    obox(az,YS+DH*0.5,0.55,0.80,3.98,4.22,STEEL_D)
# cargo opening fill: Lv1's black [6,7,8] well -> recessed 25 cm, shadow fill #3a3e44 (no black; seen only when the door opens)
C=np.array(C); blk=(C[:,:3]==[6,7,8]).all(1)
if blk.any():
    rr_=np.hypot(W2[blk,0],W2[blk,2]); f=(rr_-0.25)/rr_; W2[blk,0]*=f; W2[blk,2]*=f; C[blk]=SHADOW
print('details: opening verts',int(blk.sum()))
