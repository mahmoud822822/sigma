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
    lg=get(r,"league","competition") or "All"
    if hg is None or ag is None: continue
    clean.append((hg,ag,ht,at,lg))
LG={"Germany":3.37,"Netherlands":3.31,"England":2.75,"Italy":2.69,"Portugal":2.67,"France":2.81,"Belgium":2.80,"Spain":3.10}
def lg_avg(name):
    for k,v in LG.items():
        if k.lower() in name.lower() or name.lower() in k.lower(): return v/2
    return 1.40
teams=collections.defaultdict(lambda: {"sc":[],"co":[],"n":0,"lg":collections.Counter()})
for hg,ag,ht,at,lg in clean:
    teams[ht]["sc"].append(hg); teams[ht]["co"].append(ag); teams[ht]["n"]+=1; teams[ht]["lg"][lg]+=1
    teams[at]["sc"].append(ag); teams[at]["co"].append(hg); teams[at]["n"]+=1; teams[at]["lg"][lg]+=1
def avg(a): return sum(a)/len(a) if a else 0
def find(name):
    name=name.lower().strip()
    for k in teams:
        if name in k.lower(): return k
    return None
print("SUPER V2 - League Adjusted")
h=input("Home: ").strip(); a=input("Away: ").strip()
hk=find(h); ak=find(a)
print(f"Found: {h} -> {hk}  {a} -> {ak}")
if not hk or not ak: print("NO PREDICTION"); raise SystemExit
hlg=teams[hk]["lg"].most_common(1)[0][0]; alg=teams[ak]["lg"].most_common(1)[0][0]
h_base=lg_avg(hlg); a_base=lg_avg(alg); base=(h_base+a_base)/2
ha=avg(teams[hk]["sc"])/h_base; hd=avg(teams[hk]["co"])/h_base
aa=avg(teams[ak]["sc"])/a_base; ad=avg(teams[ak]["co"])/a_base
xh=ha*ad*base+0.15
xa=aa*hd*base-0.15
if xa<0.1: xa=0.1
print(f"League: {hlg} base {h_base:.2f} vs {alg} base {a_base:.2f} -> combined {base:.2f}")
print(f"V2 SUPER xG: {xh:.2f} - {xa:.2f}  (Home Att {ha:.2f}x vs Away Def {ad:.2f}x)")
print(f"V1 was 1.46-1.51 with global 1.45. V2 uses league bases.")
print("Rule: sum>3.0 Over lean, both>1.0 BTTS lean, gap>1.5 Strong.")
