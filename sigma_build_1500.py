import csv, pathlib, collections, math
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
    dt=get(r,"date","match_date") or "2025-01-01"
    if hg is None or ag is None: continue
    clean.append([dt,hg,ag,ht,at,lg])
clean.sort(key=lambda x: x[0])
print(f"History: {len(clean)}")
def pois(l,g): return math.exp(-l)*l**g/math.factorial(g)
out=[]
for i in range(500, min(len(clean), 2000)):
    dt,hg,ag,ht,at,lg = clean[i]
    past = clean[:i]
    # احصائيات الفرق من الماضي بس - اخر 50 ماتش لكل فريق
    def team_stats(team, is_home):
        ms=[x for x in past if x[3]==team or x[4]==team][-50:]
        if len(ms)<5: return None
        sc=[]; co=[]
        for _,ph,pa,ph_t,pa_t,_ in ms:
            if ph_t==team: sc.append(ph); co.append(pa)
            else: sc.append(pa); co.append(ph)
        return (sum(sc)/len(sc), sum(co)/len(co), len(ms))
    hs=team_stats(ht, True); aws=team_stats(at, False)
    if not hs or not aws: continue
    # متوسط الدوري من الماضي بس
    lg_past=[x for x in past if x[5]==lg]
    base=1.45
    if len(lg_past)>20: base=sum(x[1]+x[2] for x in lg_past)/len(lg_past)/2
    ha=hs[0]/base; hd=hs[1]/base; aa=aws[0]/base; ad=aws[1]/base
    xh=max(0.2, ha*ad*base+0.15); xa=max(0.1, aa*hd*base-0.15)
    ph=int(round(xh)); pa=int(round(xa))
    pick="1" if ph>pa else "X" if ph==pa else "2"
    real="1" if hg>ag else "X" if hg==ag else "2"
    hit=1 if pick==real else 0
    exact=1 if ph==hg and pa==ag else 0
    out.append({"match":f"{ht} vs {at}","date":dt,"league":lg,"predicted_home":ph,"predicted_away":pa,"real_home":hg,"real_away":ag,"xG_home":round(xh,2),"xG_away":round(xa,2),"pick":pick,"real":real,"hit":hit,"exact":exact,"type":"BACKTEST"})
    if len(out)>=1500: break
print(f"Built: {len(out)} backtest rows")
pathlib.Path("data").mkdir(exist_ok=True)
with open("data/sigma_backtest_1500.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
hit=sum(x["hit"] for x in out); ex=sum(x["exact"] for x in out)
print(f"Backtest Hit: {hit}/{len(out)} = {hit/len(out)*100:.1f}%  Exact: {ex}/{len(out)} = {ex/len(out)*100:.1f}%")
print("Saved: data/sigma_backtest_1500.csv - DO NOT copy into verified file")
