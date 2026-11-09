import csv, pathlib, collections
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
t=input("Research team: ").strip()
k=find(t)
print(f"Research: {t} -> {k}")
if not k: print("NOT FOUND"); raise SystemExit
home=[x for x in clean if x[2]==k]; away=[x for x in clean if x[3]==k]
def stats(data, is_home):
    n=len(data)
    if n==0: return "n=0"
    gf=sum(x[0] if is_home else x[1] for x in data)/n
    ga=sum(x[1] if is_home else x[0] for x in data)/n
    w=sum(1 for x in data if (x[0]>x[1] if is_home else x[1]>x[0]))/n*100
    btts=sum(1 for x in data if x[0]>0 and x[1]>0)/n*100
    over=sum(1 for x in data if x[0]+x[1]>2.5)/n*100
    cs=sum(1 for x in data if (x[1]==0 if is_home else x[0]==0))/n*100
    return f"n={n} GF={gf:.2f} GA={ga:.2f} Win={w:.1f}% BTTS={btts:.1f}% Over25={over:.1f}% CS={cs:.1f}%"
print("Home: "+stats(home, True))
print("Away: "+stats(away, False))
sc=collections.Counter((x[0],x[1]) for x in clean if x[2]==k or x[3]==k)
print("Most common scoreline:")
for (a,b),c in sc.most_common(3): print(f"{a}-{b}: {c}")
