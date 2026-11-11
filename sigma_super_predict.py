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
teams=collections.defaultdict(lambda: {"sc":[],"co":[],"n":0})
for hg,ag,ht,at in clean:
    teams[ht]["sc"].append(hg); teams[ht]["co"].append(ag); teams[ht]["n"]+=1
    teams[at]["sc"].append(ag); teams[at]["co"].append(hg); teams[at]["n"]+=1
def avg(a): return sum(a)/len(a) if a else 0
def find(name):
    name=name.lower().strip()
    for k in teams:
        if name in k.lower() or k.lower() in name: return k
    return None
print("SUPER Predict - uses Adj Attack/Defense")
h=input("Home: ").strip(); a=input("Away: ").strip()
hk=find(h); ak=find(a)
print(f"Found: {h} -> {hk}  {a} -> {ak}")
if not hk or not ak: print("NO PREDICTION"); raise SystemExit
ha=avg(teams[hk]["sc"])/1.45; hd=avg(teams[hk]["co"])/1.45
aa=avg(teams[ak]["sc"])/1.45; ad=avg(teams[ak]["co"])/1.45
xh=ha*ad*1.45+0.15
xa=aa*hd*1.45-0.15
if xa<0.1: xa=0.1
print(f"SUPER xG: {xh:.2f} - {xa:.2f}  (Home Att {ha:.2f}x vs Away Def {ad:.2f}x)")
print("Rule: If xG sum > 3.0 -> Over lean. If both xG > 1.0 -> BTTS lean. If gap > 1.5 -> Strong Home/Away.")
