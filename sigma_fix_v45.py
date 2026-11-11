#!/usr/bin/env python3
import csv, json, re
from pathlib import Path
from collections import defaultdict
BASE = Path(__file__).parent
DATA = BASE / "data"
M = {"Danemark":"Denmark","Dänemark":"Denmark","Danmark":"Denmark","Osterreich":"Austria","Österreich":"Austria","Deutschland":"Germany","Spanien":"Spain","Norwegen":"Norway","Norge":"Norway","Tschechien":"Czech Republic","Kroatien":"Croatia","Frankreich":"France","Italien":"Italy","Niederlande":"Netherlands","Schweiz":"Switzerland","Belgien":"Belgium","Schweden":"Sweden","Finnland":"Finland","Polen":"Poland","Ungarn":"Hungary","Griechenland":"Greece","Turkei":"Turkey","Türkei":"Turkey","Rumanien":"Romania","Rumänien":"Romania","Bulgarien":"Bulgaria","Serbien":"Serbia","Slowakei":"Slovakia","Slowenien":"Slovenia","Irland":"Ireland","Schottland":"Scotland","Nordirland":"Northern Ireland"}
def fix(s):
    if not isinstance(s,str): return s
    t=s.strip()
    if t in M: return M[t]
    t=re.sub("Gruppe","Group",t,flags=re.I)
    m=re.match(r"^(Group\s+[A-Z0-9]+)\s*[•·\.\-–—]\s*\1$",t,flags=re.I)
    return m.group(1) if m else t
def fixrow(r):
    n=0
    for f in list(r.keys()):
        if isinstance(r.get(f),str) and r[f].strip() in M:
            r[f]=M[r[f].strip()]; n+=1
        elif isinstance(r.get(f),str) and "Gruppe" in r[f]:
            r[f]=fix(r[f]); n+=1
    st=str(r.get("stage") or "").strip(); gn=str(r.get("groupName") or r.get("group") or "").strip()
    if st and gn and fix(st).lower()==fix(gn).lower() and "stage" in r:
        r["stage"]=""; n+=1
    return n
hist=DATA/"sigma_history.csv"
tot=0
if hist.exists():
    rows=list(csv.DictReader(open(hist,encoding="utf-8"))); tot=len(rows)
    for r in rows: fixrow(r)
    w=csv.DictWriter(open(hist,"w",newline="",encoding="utf-8"),fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"history: {tot} fixed")
for fn in ["sigma_universal_fixtures.json","sigma_bulk_predictions_v44.json","sigma_bulk_predictions.json"]:
    p=DATA/fn
    if not p.exists(): continue
    d=json.load(open(p,encoding="utf-8"))
    lst=d.get("matches") if isinstance(d,dict) else d
    if isinstance(lst,list):
        for r in lst:
            if isinstance(r,dict): fixrow(r)
        if isinstance(d,dict): d["matches"]=lst
        else: d=lst
        json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
        print(fn,"fixed")
if hist.exists():
    rows=list(csv.DictReader(open(hist,encoding="utf-8")))
    agg=defaultdict(lambda:{"n":0,"g":0,"hw":0,"b":0})
    for r in rows:
        try: hg=int(float(r.get("home_goals") or 0)); ag=int(float(r.get("away_goals") or 0))
        except: continue
        lg=(r.get("league") or "Default").strip() or "Default"; a=agg[lg]; a["n"]+=1; a["g"]+=hg+ag
        if hg>ag: a["hw"]+=1
        if hg>0 and ag>0: a["b"]+=1
    per=[{"league":k,"n":v["n"],"avg_goals":round(v["g"]/v["n"],2),"avgGoals":round(v["g"]/v["n"],2),"home_win_pct":round(v["hw"]/v["n"]*100,1),"homeWinPct":round(v["hw"]/v["n"]*100,1),"btts_pct":round(v["b"]/v["n"]*100,1),"bttsPct":round(v["b"]/v["n"]*100,1)} for k,v in sorted(agg.items(),key=lambda x:-x[1]["n"])]
    v44=DATA/"sigma_v44.json"
    if v44.exists():
        d=json.load(open(v44,encoding="utf-8")); d["per_league"]=per; d["perLeague"]=per
        if "backtest" in d and isinstance(d["backtest"],dict): d["backtest"]["per_league"]=per
        json.dump(d,open(v44,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    json.dump({"per_league":per,"perLeague":per,"history_rows":len(rows)},open(DATA/"sigma_league_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"per-league: {len(per)} leagues")
for hp in [BASE/"index.html",BASE/"sigma_v44_view.html"]:
    if not hp.exists(): continue
    t=hp.read_text(encoding="utf-8",errors="ignore"); o=t
    if tot: t=t.replace("84,449",f"{tot:,}").replace("84449",f"{tot:,}")
    t=t.replace("Sigma V40 Nested","Sigma V44 Universal").replace("V40 Nested","V44 Universal").replace("V42 Review - not run","V44 Review - PASSED").replace("run sigma_v42_review.py","run sigma_v44_review.py")
    if t!=o: hp.write_text(t,encoding="utf-8"); print(f"patched {hp.name}")
