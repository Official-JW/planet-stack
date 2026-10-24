import math
BOX0=2000; HAUL=60; BOARD=56/60; TRIP0=616
def fill(M): return max(15, 60*0.85**(M-1))
def trucks(M): return 1 + (M>=20) + (M>=30) + (M>=40) + (M>=50)
def mine_bph(M):
    f=fill(M); n=trucks(M); return 3600*min(n/(f+HAUL), 1/f)
def q(P): return 2*1.035**(P-1)          # pump %/min
def p(R): return 2*1.045**(R-1)          # fuel line %/min
def tank(R): return 100+10*(R-1)         # tank farm storage %
def trip_s(E): return TRIP0*(1-0.005*max(0,E-1))
def hold(N): return 10+2*(N-1)
def seats(N): return 4+N//2
def dock(L): return 20+4*(L-1) if L<=10 else 56+int(1.6*(L-10))
def ships(S,P): return 1+(S>=20 and P>=20)+(S>=40 and P>=40)
def spec(H,LS): return min(2*H, 2*(LS-1)) if H>0 else 0
def boxval(M,R,E,H,LS): return BOX0*(1+0.02*(M-1))*(1+0.03*(R-1))*(1+0.01*max(0,E-1))*(1+0.01*spec(H,LS))
def cycle_min(P,R,E):
    t=trip_s(E)/60; stored=min(tank(R),(t+BOARD)*p(R))
    refuel=max(100/q(P), max(0,100-stored)/p(R)); return refuel+BOARD+t, refuel
def income(L, shipLv=None, nships=None):
    M=R=P=LS=D=L; S=L; H=L; E=L
    N=shipLv or min(10,L); n=nships or ships(S,P)
    cyc,ref=cycle_min(P,R,E)
    trips=n*60/cyc
    trips=min(trips, 60*p(R)/100 + (0 if n==1 else 0)) if n>1 else trips
    demand=trips*hold(N); prod=mine_bph(M)
    boxes=min(demand,prod)
    v=boxval(M,R,E,H,LS)
    return dict(L=L,ref=ref,cyc=cyc,trips=trips,hold=hold(N),n=n,demand=demand,prod=prod,boxes=boxes,v=v,inc=boxes*v,pertrip=hold(N)*v)
B={'Life Support':2000,'Mine':1000,'Refinery':1500,'Cargo Dock':1500,'Launch Pad':3000,'Shipyard':5000,'Habitat':4000,'Engineering':6000}
BUILD={'Shipyard':25000,'Habitat':40000,'Engineering':80000}
G=1.15
def cost(b,L):  # L -> L+1
    c=B[b]*G**(L-1)*(1.5 if (L+1)%10==0 else 1)
    return sig(c)
def sig(c):
    d=10**max(0,int(math.log10(c))-1); return int(round(c/d)*d)
def shipcost(N): return sig(8000*1.7**(N-1))
if __name__=='__main__':
    for L in [1,2,5,10,20,30,40,50]:
        r=income(L); print({k:(round(v,2) if isinstance(v,float) else v) for k,v in r.items()})
    print()
    for L in [1,2,5,10,20,30,40,49]:
        rnd=sum(cost(b,L) for b in B); inc=income(L)['inc']
        print(L,[cost(b,L) for b in B], 'round',rnd,'hours',round(rnd/inc,2))
    print('ship',[ (N,shipcost(N)) for N in range(1,10)])
    tot=sum(cost(b,L) for b in B for L in range(1,50)); print('total',tot)
    for L in range(1,51): print(L, round(fill(L),1), round(mine_bph(L),1), dock(L), round(q(L),2), round(100/q(L),1), round(p(L),2), tank(L))
