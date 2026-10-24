# door visibility vs crane/hoses/ship legs at 375x667 under the Lv2 camera; door rotated about the ship axis to test azimuths
import math,numpy as np,sys
from gl import *
from PIL import Image,ImageDraw
from spare2 import world
j,B=load('pad_lv2_raw.glb')
def q(r):
    x,y,z,w=r; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def tris(root):
    out=[]
    def walk(i,M):
        n=j['nodes'][i]; S=np.diag(list(n.get('scale',[1,1,1]))+[1]); R=np.eye(4); R[:3,:3]=q(n.get('rotation',[0,0,0,1])); T=np.eye(4); T[:3,3]=n.get('translation',[0,0,0]); M2=M@T@R@S
        if 'mesh' in n:
            for pr in j['meshes'][n['mesh']]['primitives']:
                P=acc(j,B,pr['attributes']['POSITION']).astype(float); P=(np.c_[P,np.ones(len(P))]@M2.T)[:,:3]; I=acc(j,B,pr['indices']).reshape(-1,3); out.append(P[I])
        for c in n.get('children',[]): walk(c,M2)
    walk(root,np.eye(4)); return np.concatenate(out)
W,H=375,667; SC=3; fw=84; ct=(0,5.5,2.75)
asp=W/H; t=math.tan(math.radians(19)); d=fw/2/(t*asp); Tg=np.array(ct); el=math.radians(18)
C=Tg+d*np.array([0,math.sin(el),math.cos(el)]); f=(Tg-C)/d; r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f)
def proj(P):
    v=P-C; z=v@f; return np.c_[W/2*(1+(v@r)/z/(t*asp))*SC, H/2*(1-(v@u)/z/t)*SC], z
door=tris(24); occl=np.concatenate([tris(20),tris(21),tris(22)])
ax=np.array([0,0,-13.0])
def vis(az_new):
    da=math.radians(az_new-5.0); Ry=np.array([[math.cos(da),0,math.sin(da)],[0,1,0],[-math.sin(da),0,math.cos(da)]])
    D=(door-ax)@Ry.T+ax; dp,dz=proj(D.reshape(-1,3)); dp=dp.reshape(-1,3,2); dz=dz.reshape(-1,3)
    md=Image.new('L',(W*SC,H*SC)); g=ImageDraw.Draw(md)
    for tr in dp: g.polygon([tuple(p) for p in tr],fill=255)
    zmin=dz.min()
    op,oz=proj(occl.reshape(-1,3)); op=op.reshape(-1,3,2); oz=oz.reshape(-1,3)
    mo=Image.new('L',(W*SC,H*SC)); g2=ImageDraw.Draw(mo)
    for tr,zz in zip(op,oz):
        if zz.max()<zmin+0.5: g2.polygon([tuple(p) for p in tr],fill=255)
    a=np.array(md)>0; o=np.array(mo)>0
    return a.sum()/SC/SC, (a&~o).sum()/a.sum()
for az in [float(x) for x in sys.argv[1:]]: s,v=vis(az); print('az',az,'door px',round(s,1),'visible',round(100*v,1),'%')
