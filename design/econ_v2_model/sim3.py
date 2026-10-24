import sys, copy, json
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from model import *
P=dict(GMR=1.17, KNEE=10, G=1.15, NEW2=3e6, NEW3=6e7, BUILD_SY=10000, SHIP0=8000, SHIPG=1.7, start=3000)
def growth(b,L):  # multiplier for L -> L+1 (before the look bump)
    if b in ('Mine','Refinery'):
        k=int(P['KNEE']); return P['G']**(min(L,k)-1)*P['GMR']**max(0,L-k)
    return P['G']**(L-1)
def cost(b,L): return sig(B[b]*growth(b,L)*(1.5 if (L+1)%10==0 else 1))
def shipcost(N): return sig(P['SHIP0']*P['SHIPG']**(N-1))
def build(b): return {'Shipyard':P['BUILD_SY'],'Habitat':40000,'Engineering':80000}[b]
def storage(st): return dock(st['Cargo Dock'])+8+2+12
def active_inc(st):
    M,R,Pd,LS,S,H,E=[st[k] for k in ['Mine','Refinery','Launch Pad','Life Support','Shipyard','Habitat','Engineering']]
    cyc,ref=cycle_min(Pd,R,E); n=len(st['ships'])
    trips=n*60/cyc; dem=sum(60/cyc*hold(N) for N in st['ships'])
    if n>1:
        cap=60*p(R)/100
        if trips>cap: dem*=cap/trips; trips=cap
    return min(dem,mine_bph(M))*boxval(M,R,E,H,LS)
GAP=3.0; SESSION=1.0   # check-in: 3 h away, then 1 h in the game
def session(st):
    M,R,Pd,LS,S,H,E=[st[k] for k in ['Mine','Refinery','Launch Pad','Life Support','Shipyard','Habitat','Engineering']]
    cyc,ref=cycle_min(Pd,R,E); t=trip_s(E)/60
    k=1+max(0,int((SESSION*60-(BOARD+0.45*t))//cyc))
    n=len(st['ships'])
    fuel_trips=n+ (tank(R)+60*p(R)*SESSION)/100   # ships come back full + stored tanks + made during the session
    buf=min(mine_bph(M)*GAP, storage(st)+sum(hold(N) for N in st['ships']))+mine_bph(M)*SESSION
    boxes=0; trips=0
    for r in range(k):
        for N in sorted(st['ships'],reverse=True):
            if trips+1>fuel_trips: break
            b=min(hold(N),buf-boxes)
            if b<=0: break
            boxes+=b; trips+=1
    return boxes, trips, k
def checkin_inc(st):
    M,R,Pd,LS,S,H,E=[st[k] for k in ['Mine','Refinery','Launch Pad','Life Support','Shipyard','Habitat','Engineering']]
    return session(st)[0]*boxval(M,R,E,H,LS)/(GAP+SESSION)
def options(st):
    o=[]
    for b in B:
        L=st[b]
        if L==0:
            if b=='Shipyard' or (b=='Habitat' and st['Shipyard']>=1) or (b=='Engineering' and st['Habitat']>=1): o.append((build(b),('lvl',b)))
            continue
        if L>=50: continue
        if b!='Life Support' and L+1>st['Life Support']+10: continue
        o.append((cost(b,L),('lvl',b)))
    for i,N in enumerate(st['ships']):
        if N<10:
            bc,ok=bundle(st,N+1)
            if ok: o.append((shipcost(N)+bc,('ship',i)))
    n=len(st['ships'])
    for k,need in ((2,20),(3,40)):
        if n==k-1:
            bc,ok=bundle(st,need,10 if k==2 else 30)
            if ok: o.append((P['NEW%d'%k]+bc,('new',k)))
    return o
def bundle(st,need,eng=0):
    c=0
    for bb in ('Shipyard','Habitat','Engineering'):
        if st[bb]==0 and (bb=='Shipyard' or eng): c+=build(bb)
    for b in ('Shipyard','Launch Pad','Cargo Dock')+(('Engineering',) if eng else ()):
        tgt=need if b!='Engineering' else eng
        for L in range(max(1,st[b]),tgt):
            if L+1>st['Life Support']+10: return 0,False
            c+=cost(b,L)
    return c,True
def apply(st,a):
    st=copy.deepcopy(st); k,x=a
    if k=='lvl': st[x]+=1
    else:
        need=st['ships'][x]+1 if k=='ship' else (20 if x==2 else 40)
        for b in ('Shipyard','Launch Pad','Cargo Dock'): st[b]=max(st[b],need)
        if k=='new':
            st['Habitat']=max(st['Habitat'],1); st['Engineering']=max(st['Engineering'],10 if x==2 else 30)
        if k=='ship': st['ships'][x]+=1
        else: st['ships'].append(1)
    return st
def run(incf, money=None):
    st={'Life Support':1,'Mine':1,'Refinery':1,'Cargo Dock':1,'Launch Pad':1,'Shipyard':0,'Habitat':0,'Engineering':0,'ships':[1]}
    money=P['start']+20000 if money is None else money; t=0.0; marks={}
    while True:
        o=options(st)
        if not o: break
        i0=incf(st); best=None
        for c,a in o:
            s1=apply(st,a); d=incf(s1)-i0; sc=d/c
            if d<=1e-6:
                for c2,a2 in options(s1):
                    if a2==a: continue
                    d2=incf(apply(s1,a2))-i0
                    if d2>0: sc=max(sc,0.8*d2/(c+c2))
            if best is None or sc>best[0]: best=(sc,c,a)
        sc,c,a=best
        if sc<=0: c,a=min(o,key=lambda x:x[0])
        if money<c: t+=(c-money)/i0; money=c
        money-=c; st=apply(st,a)
        for b in B:
            for m in [2,3,5,10,20,30,40,50]:
                if st[b]>=m and (b,m) not in marks: marks[(b,m)]=t
        for m in [2,3,5,10]:
            if st['ships'][0]>=m and ('Ship #1 level',m) not in marks: marks[('Ship #1 level',m)]=t
        for m in [2,3]:
            if len(st['ships'])>=m and ('Ships owned',m) not in marks: marks[('Ships owned',m)]=t
    return t,marks
if __name__=='__main__':
    for kv in sys.argv[1:]:
        k,v=kv.split('='); P[k]=float(v)
    ta,ma=run(active_inc); tc,mc=run(checkin_inc)
    print('active total h',round(ta,1),' checkin total h',round(tc,1),'= days',round(tc/16,1))
    keys=sorted(set(ma)|set(mc), key=lambda k:ma.get(k,1e9))
    for k in keys: print(k, 'active h',round(ma.get(k,-1),1),' checkin days',round(mc.get(k,-1)/16,1))
