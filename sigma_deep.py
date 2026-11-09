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
clean = []
for r in rows:
    hg = num(get(r, "home_goals","home_score","hg","homeGoals","home"))
    ag = num(get(r, "away_goals","away_score","ag","awayGoals","away"))
    ht = get(r, "home_team","home","homeTeam") or "?"
    at = get(r, "away_team","away","awayTeam") or "?"
    lg = get(r, "league","competition") or "All"
    if hg is None or ag is None: continue
    clean.append((hg,ag,ht,at,lg))
n = len(clean)
hg_avg = sum(x[0] for x in clean)/n
ag_avg = sum(x[1] for x in clean)/n
score = collections.Counter((x[0],x[1]) for x in clean)
cs_home = sum(1 for x in clean if x[1]==0)/n*100
cs_away = sum(1 for x in clean if x[0]==0)/n*100
# فرق - هجوم ودفاع وثبات
teams = collections.defaultdict(lambda: {"sc": [], "co": [], "n": 0})
for hg,ag,ht,at,lg in clean:
    teams[ht]["sc"].append(hg); teams[ht]["co"].append(ag); teams[ht]["n"]+=1
    teams[at]["sc"].append(ag); teams[at]["co"].append(hg); teams[at]["n"]+=1
def avg(a): return sum(a)/len(a) if a else 0
attack = sorted([(k, avg(v["sc"]), v["n"]) for k,v in teams.items() if v["n"]>=20], key=lambda x: x[1], reverse=True)
defense = sorted([(k, avg(v["co"]), v["n"]) for k,v in teams.items() if v["n"]>=20], key=lambda x: x[1])
volatile = sorted([(k, statistics.pstdev(v["sc"]) if len(v["sc"])>1 else 0, v["n"]) for k,v in teams.items() if v["n"]>=20], key=lambda x: x[1], reverse=True)
# رهانات مركبة
def rate(f): 
    h=sum(1 for x in clean if f(x)); return f"{h}/{n} = {h/n*100:.1f}%"
out=[]
out.append("Sigma DEEP Learn - 2150 Real - Mahmoud Emad")
out.append(f"n={n} Home goals avg={hg_avg:.2f} Away goals avg={ag_avg:.2f} Gap={hg_avg-ag_avg:.2f}")
out.append(f"Clean Sheet Home: {cs_home:.1f}%  Clean Sheet Away: {cs_away:.1f}%")
out.append("")
out.append("Top 10 Scorelines (Exact is lottery - even top 10 cover <50%):")
for (a,b),c in score.most_common(10):
    out.append(f"{a}-{b}: {c} = {c/n*100:.1f}%")
out.append("")
out.append("Double Chance (safer than 1X2 alone):")
out.append(f"1X (Home or Draw): {rate(lambda x: x[0]>=x[1])}")
out.append(f"X2 (Draw or Away): {rate(lambda x: x[0]<=x[1])}")
out.append(f"12 (No Draw): {rate(lambda x: x[0]!=x[1])}")
out.append("")
out.append("Combo - BTTS + Over 2.5: "+rate(lambda x: x[0]>0 and x[1]>0 and x[0]+x[1]>2.5))
out.append("Combo - BTTS No + Under 2.5: "+rate(lambda x: not (x[0]>0 and x[1]>0) and x[0]+x[1]<2.5))
out.append("")
out.append("Top 5 Attack (n>=20):")
for k,v,nn in attack[:5]: out.append(f"{k}: {v:.2f} goals/match n={nn}")
out.append("Top 5 Defense (lowest conceded, n>=20):")
for k,v,nn in defense[:5]: out.append(f"{k}: {v:.2f} conceded/match n={nn}")
out.append("Most Volatile (unpredictable - avoid exact bets):")
for k,v,nn in volatile[:5]: out.append(f"{k}: std={v:.2f} n={nn}")
out.append("")
out.append("DEEP RULES:")
out.append("1. League first, team second, form third. Never bet same market on all leagues.")
out.append("2. Exact Score = lottery. BTTS/Over = predictable. Double Chance = safety.")
out.append("3. Volatile teams: avoid exact, use Over/BTTS only.")
out.append("4. Avg per team is still noisy: avg n=28 per team, need shrinkage to league avg.")
out.append("5. Future = Update All (9) + Predict All (6) using these deep stats.")
txt="\n".join(out)
print(txt)
pathlib.Path("DEEP_REPORT.txt").write_text(txt, encoding="utf-8")
print("Saved: DEEP_REPORT.txt")
