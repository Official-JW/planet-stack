import sys; sys.argv=['x']
import sim3 as S
from model import *
S.P.update(G=1.17,GMR=1.19,KNEE=10,NEW2=1e7,NEW3=2e8)
cost=S.cost
def money(v):
    return '$'+format(int(round(v)),',')
Ls=[1,2,5,10,20,30,40,50]
print('### income')
print('| All buildings at | Ships (level) | Box value | Pay per full trip | Refuel | Trip | Cycle | Trips/h (fleet) | Boxes/h needed | Mine boxes/h | Limit | $/h active | $/session (check-in) |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for L in Ls:
    n=1+(L>=20)+(L>=40); N=min(10,L)
    st={'Life Support':L,'Mine':L,'Refinery':L,'Cargo Dock':L,'Launch Pad':L,'Shipyard':L,'Habitat':L if L>1 else 0,'Engineering':L if L>1 else 0,'ships':[N]*n}
    M=R=P=L; H=st['Habitat']; E=st['Engineering']
    cyc,ref=cycle_min(P,R,E); trips=n*60/cyc
    lim='ship/fuel'
    if n>1 and trips>60*p(R)/100: trips=60*p(R)/100; lim='fuel line'
    dem=trips*hold(N); prod=mine_bph(M)
    if prod<dem: lim='mine'
    v=boxval(M,R,E,H,LS:=L)
    inc=S.active_inc(st); sb,strips,k=S.session(st)
    print(f'| Lv{L} | {n} × Lv{N} ({hold(N)} boxes) | {money(v)} | {money(hold(N)*v)} | {ref:.1f} min | {trip_s(E):.0f} s | {cyc:.1f} min | {trips:.2f} | {dem:.0f} | {prod:.0f} | {lim} | {money(inc)} | {money(sb*v)} ({strips} trips) |')
print('### costs')
names=list(B)
print('| Building | Unlock | '+' | '.join(f'Lv{L}→{L+1}' if L<50 else 'Lv49→50' for L in Ls)+' | Total Lv1→50 |')
print('|---|---|'+'---|'*(len(Ls)+1))
for b in names:
    row=[money(cost(b,min(L,49))) for L in Ls]
    tot=sum(cost(b,L) for L in range(1,50))
    unlock=money(S.build(b)) if b in ('Shipyard','Habitat','Engineering') else 'starts Lv1'
    print(f'| {b} | {unlock} | '+' | '.join(row)+f' | {money(tot)} |')
print('### ship')
print('| Ship level | Hold | Seats | Upgrade cost to reach it | Needs Shipyard / Launch Pad / Cargo Dock |')
print('|---|---|---|---|---|')
for N in range(1,11):
    print(f'| Lv{N} | {hold(N)} | {seats(N)} | {money(S.shipcost(N-1)) if N>1 else "starter"} | {"—" if N==1 else f"Lv{N}"} |')
print('### storage')
print('| Dock Lv | Dock cap | Cranes | Stack height | Total buffer (dock+pallet 8+flatbed 2+bay 12) | Hours to fill, Mine same level | Hours to fill with Mine Lv1 + parked Lv1 hold |')
print('|---|---|---|---|---|---|---|')
for L in [1,2,3,4,5,6,10,20,27,28,30,40,50]:
    c=dock(L); buf=c+22
    print(f'| {L} | {c} | {cranes(L)} | {stack(L)} high | {buf} | {buf/mine_bph(L):.1f} h | {(buf+10)/mine_bph(1):.1f} h |')
print('### fuel')
print('| Level | Pump (Launch Pad) %/min | Full refuel by pump | Fuel line (Refinery) %/min | Line: one tank takes | Tank farm stores | Refuel at landing (both at this level) |')
print('|---|---|---|---|---|---|---|')
for L in Ls:
    cyc,ref=cycle_min(L,L,L if L>1 else 0)
    print(f'| {L} | {q(L):.2f} ({30*2/q(L):.1f} s per 1%) | {100/q(L):.1f} min | {p(L):.2f} | {100/p(L):.1f} min | {tank(L)}% | {ref:.1f} min |')
print('### mine')
print('| Mine Lv | Chute fill | Trucks | Boxes/h | Box value bonus |')
print('|---|---|---|---|---|')
for L in Ls+[3,9]:
    pass
for L in [1,2,3,5,9,10,20,30,40,50]:
    print(f'| {L} | {fill(L):.1f} s | {trucks(L)} | {mine_bph(L):.0f} | +{2*(L-1)}% |')
