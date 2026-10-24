# Lv2 collar read-at-375 details (exec'd inside mk_lv2.py; uses W2, C, addtri, K, Y0, Y1).
# Director 10/24 11:22: lip/step at collar top + bottom, chunky collar details in EXISTING colours (0 draws), cargo opening no black.
RC=4.0*K                     # collar skin radius (4.40)
STEEL_D=[82,93,107,255]; STEEL_M=[114,121,130,255]; SHADOW=[11,12,15,255]   # existing Lv1 swatches; SHADOW = #3a3e44 (linear)
DOOR_GAP=(5.0-24.5, 5.0+24.5)   # door az 5 +- (W/2 + frame + 0.1 m)/R
LIP_H, LIP_OUT = 0.22, 0.12   # flange step: 22 cm tall, 12 cm proud of the collar skin
PODS_AZ, POD = (-88.0, 98.0), (0.85, 3.2, 0.45)          # side pods: width, height, depth (m), centred on the collar
LATCH_AZ, LATCH = (-40.0, -28.0, 33.0, 43.0), (0.32, 0.55, 0.16)   # cargo latches straddling both lips; right pair clear of the ladder (az 55-65)
LADDER_GAP=(46.0,74.0)   # lips notched round the ladder (rails az 56/64): Lv1 crew climb clears the collar unchanged
def lathe_band(ya,yb,r_in,r_out,col,seg=64,gap=None,arc=False):
    vs=[];ns=[];tr=[]
    if gap and isinstance(gap[0],(tuple,list)):   # several gaps: emit one arc between each pair of gaps
        gs=sorted(gap)
        for k in range(len(gs)): lathe_band(ya,yb,r_in,r_out,col,max(8,seg//len(gs)),(gs[k-1][1]-(360 if k==0 else 0),gs[k][0]),arc=True)
        return
    g0,g1=(np.radians(gap[0]),np.radians(gap[1])) if gap else (0,0)
    prof=[(r_in,ya,(0,-1)),(r_out,ya,(0,-1)),(r_out,ya,(1,0)),(r_out,yb,(1,0)),(r_out,yb,(0,1)),(r_in,yb,(0,1))]
    for i in range(seg+1):
        a=(g0+(g1-g0)*i/seg) if arc else g1+(2*np.pi-(g1-g0))*i/seg; c,sn=np.cos(a),np.sin(a)
        for rr_,yy,(nr,ny) in prof: vs.append((rr_*sn,yy,rr_*c)); ns.append((nr*sn,ny,nr*c))
    P_=len(prof)
    for i in range(seg):
        for k_ in (0,2,4):
            q=i*P_+k_; tr+=[(q,q+P_,q+1),(q+1,q+P_,q+P_+1)]
    addtri(vs,ns,col,tr)
def obox(az,yc,w,h,r0,r1,col):
    a=np.radians(az); nr=np.array([np.sin(a),0,np.cos(a)]); tg=np.array([np.cos(a),0,-np.sin(a)]); up=np.array([0,1.,0])
    c0=nr*(r0+r1)/2+up*yc; ex=[tg*w/2,up*h/2,nr*(r1-r0)/2]
    for ax in range(3):
        for sgn in (-1,1):
            n_=ex[ax]/np.linalg.norm(ex[ax])*sgn; o=[e for k2,e in enumerate(ex) if k2!=ax]
            ctr=c0+ex[ax]*sgn; vs=[ctr-o[0]-o[1],ctr+o[0]-o[1],ctr+o[0]+o[1],ctr-o[0]+o[1]]
            addtri(vs,[n_]*4,col,[(0,1,2),(0,2,3)])
if LV1: LIPS=[]; PODS_AZ=(); LATCH_AZ=()
else: LIPS=(Y0, Y1-LIP_H)
# 1) lips at the collar top + bottom (where the taper meets full width)
for yl in LIPS:
    lathe_band(yl, yl+LIP_H, RC-0.30, RC+LIP_OUT, STEEL_D, gap=[DOOR_GAP,LADDER_GAP])   # lips stop either side of the cargo door frame and the boarding ladder
# 2) side pods (silhouette bulges) + cap strips, and cargo latches over each lip
for az in PODS_AZ:
    yc=(Y0+Y1)/2
    obox(az,yc,POD[0],POD[2+0-0]*0+POD[1],RC-0.2,RC+POD[2],STEEL_M)
    for dy in (-POD[1]/2, POD[1]/2): obox(az,yc+dy,POD[0]+0.12,0.16,RC-0.2,RC+POD[2]+0.06,STEEL_D)
for az in LATCH_AZ:
    for yl in (Y0+LIP_H/2, Y1-LIP_H/2):
        obox(az,yl,LATCH[0],LATCH[1],RC-0.1,RC+LIP_OUT+LATCH[2],STEEL_D)
# 3) cargo opening fill: Lv1's black [6,7,8] well -> recessed 25 cm, shadow fill #3a3e44 (no black anywhere; seen only when the door opens)
C=np.array(C); blk=(C[:,:3]==[6,7,8]).all(1)
if blk.any():
    rr_=np.hypot(W2[blk,0],W2[blk,2]); f=(rr_-0.25)/rr_; W2[blk,0]*=f; W2[blk,2]*=f; C[blk]=SHADOW
print('details: opening verts',int(blk.sum()))
