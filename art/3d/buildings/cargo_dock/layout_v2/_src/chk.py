import json,numpy as np
d=json.load(open('wmap.json')); NX,NZ,C,X0,Z0=d['NX'],d['NZ'],d['C'],d['X0'],d['Z0']
raw=np.fromfile('wmap.bin',dtype=np.uint8); H=np.frombuffer(raw[:NX*NZ*4].tobytes(),dtype=np.float32).reshape(NZ,NX); ID=np.frombuffer(raw[NX*NZ*4:].tobytes(),dtype=np.int16).reshape(NZ,NX)
names=[i['name'] for i in d['info']]
def band(x0,x1,z0,z1,hmin=0.15,label=''):
  a=int((x0-X0)/C);b=int((x1-X0)/C);c=int((z0-Z0)/C);e=int((z1-Z0)/C)
  h=H[c:e,a:b]; idd=ID[c:e,a:b]
  print('==',label,(x0,x1,z0,z1))
  for k,n in enumerate(names):
    m=(idd==k)&(h>hmin)
    if m.any():
      zz,xx=np.nonzero(m); print(f"  {n:9s} cells {m.sum():5d} x {X0+(xx.min()+a)*C:.1f}..{X0+(xx.max()+a+1)*C:.1f} z {Z0+(zz.min()+c)*C:.1f}..{Z0+(zz.max()+c+1)*C:.1f} hmax {h[m].max():.2f}")
band(290.5,462.5,10.2,24.8,0.15,'FB road band (lanes z13/22, x west U-turn..pad U-turn)')
band(340,429,9.2,10.2,0.15,'FB 1 m clear strip z 9.2-10.2 between Refinery and pad')
band(457,908,-26.3,0.3,0.15,'transport road band (ship axis z -13 +-13.3), pad centre -> shipyard edge')
band(908,945,-5,30,0.15,'shipyard left approach x908-945 z-5..30')
band(330,352,-45,20,0.15,'Refinery|Dock seam')
band(419,430,-50,25,0.15,'Dock|Pad seam')
