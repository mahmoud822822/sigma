import csv, pathlib, math
p = pathlib.Path("data/sigma_history.csv")
rows = list(csv.DictReader(open(p, encoding="utf-8")))
def get(r, *ns):
    for n in ns:
        if n in r and r[n] not in ("", None): return r[n]
    return None
def num(v):
    try: return int(float(str(v).strip()))
    except: return None
clean=[]
for r in rows:
    hg=num(get(r,"home_goals","home_score","hg","homeGoals","home"))
    ag=num(get(r,"away_goals","away_score","ag","awayGoals","away"))
    ht=get(r,"home_team","home","homeTeam") or "?"
    at=get(r,"away_team","away","awayTeam") or "?"
    if hg is None or ag is None: continue
    clean.append((hg,ag,ht,at))
def find(name):
    name=name.lower().strip()
    for k in set([x[2] for x in clean]+[x[3] for x in clean]):
        if name in k.lower(): return k
    return None
def pois(l,g): return math.exp(-l)*l**g/math.factorial(g)
t=input("Forecast team: ").strip(); k=find(t)
print(f"Forecast: {t} -> {k}")
if not k: print("NOT FOUND"); raise SystemExit
allm=[x for x in clean if x[2]==k or x[3]==k]
gf=sum(x[0] if x[2]==k else x[1] for x in allm)/len(allm)
ga=sum(x[1] if x[2]==k else x[0] for x in allm)/len(allm)
print(f"Current: GF={gf:.2f} GA={ga:.2f} n={len(allm)}")
for opp, oxg, ocon in [("vs Avg Opp",1.45,1.45),("vs Strong Opp",2.00,0.80),("vs Weak Opp",0.90,1.80)]:
    xh=gf/1.45*ocon*1.45+0.15; xa=oxg/1.45*ga/1.45*1.45-0.15
    if xa<0.1: xa=0.1
    p1=sum(pois(xh,i)*pois(xa,j) for i in range(11) for j in range(11) if i>j)*100
    print(f"{opp}: xG {xh:.2f}-{xa:.2f} Win {p1:.1f}%")
print(f"Next 10: Goals {gf*10:.1f} Conceded {ga*10:.1f}")
