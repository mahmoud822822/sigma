import csv, pathlib, collections
p = pathlib.Path("data/sigma_history.csv")
rows = list(csv.DictReader(open(p, encoding="utf-8")))
def get(r, *ns):
    for n in ns:
        if n in r and r[n] not in ("", None):
            return r[n]
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
n=len(clean)
teams=collections.defaultdict(lambda: {"sc":[],"co":[],"n":0})
for hg,ag,ht,at in clean:
    teams[ht]["sc"].append(hg); teams[ht]["co"].append(ag); teams[ht]["n"]+=1
    teams[at]["sc"].append(ag); teams[at]["co"].append(hg); teams[at]["n"]+=1
def avg(a): return sum(a)/len(a) if a else 0
adj=[]
for k,v in teams.items():
    if v["n"]<20: continue
    adj.append((k, avg(v["sc"])/1.45, avg(v["co"])/1.45, v["n"]))
att=sorted(adj, key=lambda x: x[1], reverse=True)
dfn=sorted(adj, key=lambda x: x[2])
half=n//2
def tavg(data):
    d=collections.defaultdict(list)
    for hg,ag,ht,at in data:
        d[ht].append(hg); d[at].append(ag)
    return {k: sum(v)/len(v) for k,v in d.items() if len(v)>=10}
f1=tavg(clean[:half]); f2=tavg(clean[half:])
stab=sorted([(k,f1[k],f2[k],abs(f1[k]-f2[k])) for k in f1 if k in f2], key=lambda x: x[3])
btts=sum(1 for x in clean if x[0]>0 and x[1]>0)
over=sum(1 for x in clean if x[0]+x[1]>2.5)
both=sum(1 for x in clean if x[0]>0 and x[1]>0 and x[0]+x[1]>2.5)
out=[]
out.append(f"SUPER n={n}")
out.append("Adj Attack Top 5:")
for k,a,c,nn in att[:5]: out.append(f"{k}: {a:.2f}x n={nn}")
out.append("Adj Defense Top 5:")
for k,a,c,nn in dfn[:5]: out.append(f"{k}: {c:.2f}x n={nn}")
out.append("Most Stable Top 5:")
for k,a,b,d in stab[:5]: out.append(f"{k}: {a:.2f}->{b:.2f} change {d:.2f}")
out.append(f"P(Over|BTTS)={both}/{btts}={both/btts*100:.1f}%")
out.append(f"P(BTTS)={btts/n*100:.1f}% Over={over/n*100:.1f}%")
txt="\n".join(out)
print(txt)
pathlib.Path("SUPER_REPORT.txt").write_text(txt, encoding="utf-8")
print("Saved SUPER_REPORT.txt")
