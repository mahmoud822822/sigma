import csv, pathlib, collections, statistics
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
teams=collections.defaultdict(lambda: {"sc":[],"co":[],"n":0})
for hg,ag,ht,at in clean:
    teams[ht]["sc"].append(hg); teams[ht]["co"].append(ag); teams[ht]["n"]+=1
    teams[at]["sc"].append(ag); teams[at]["co"].append(hg); teams[at]["n"]+=1
def avg(a): return sum(a)/len(a) if a else 0
rows2=[]
for k,v in teams.items():
    if v["n"]<20: continue
    a=avg(v["sc"]); c=avg(v["co"]); vol=statistics.pstdev(v["sc"]) if len(v["sc"])>1 else 0
    rows2.append((k,a,c,vol,v["n"]))
print("SCOUT Hidden Gems:")
for k,a,c,vol,nn in sorted(rows2, key=lambda x: x[1]-x[3], reverse=True)[:5]:
    print(f"{k}: Attack {a:.2f} Vol {vol:.2f} n={nn}")
