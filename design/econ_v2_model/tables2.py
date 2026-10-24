import sys; sys.argv=['x']
import sim3 as S
from model import *
S.P.update(G=1.17)
def money(v): return '$'+format(int(round(v)),',')
def price(b,L): return S.cost(b,L-1)   # buy level L
Ls=[2,5,10,20,30,40,50]
print('| Building | Base | Lv1 | '+' | '.join(f'Lv{L}' for L in Ls)+' | Total to reach Lv50 |')
print('|---|---|---|'+'---|'*(len(Ls)+1))
for b in B:
    lv1=money(S.build(b))+' to build' if b in ('Shipyard','Habitat','Engineering') else 'start'
    tot=sum(price(b,L) for L in range(2,51))+(S.build(b) if b in ('Shipyard','Habitat','Engineering') else 0)
    print(f'| {b} | {money(B[b])} | {lv1} | '+' | '.join(money(price(b,L)) for L in Ls)+f' | {money(tot)} |')
print()
print('| Level bought | ×Base | Level bought | ×Base | Level bought | ×Base | Level bought | ×Base | Level bought | ×Base |')
print('|---|---|---|---|---|---|---|---|---|---|')
rows=[]
for r in range(10):
    cells=[]
    for c in range(5):
        L=2+r+c*10
        if L>50: cells+=['','']; continue
        m=1.17**(L-2)*(1.5 if L%10==0 else 1)
        cells+=[f'{L}'+(' (new look)' if L%10==0 else ''), f'{m:.2f}']
    rows.append('| '+' | '.join(cells)+' |')
print('\n'.join(rows))
