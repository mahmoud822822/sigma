import csv, math
from datetime import datetime
from pathlib import Path
def parse_date(s):
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d"):
        try: return datetime.strptime(str(s).strip(), fmt)
        except: continue
    return datetime(2000,1,1)
def poisson(lam,g): return (math.exp(-lam)*lam**g)/math.factorial(g)
rows=list(csv.DictReader(open("data/sigma_history_all.csv", encoding="utf-8")))
rows=sorted(rows, key=lambda x: parse_date(x["date"]))
print(f"Backtest on {len(rows)} matches - Walk-Forward")
test=rows[-5000:]
brier=0; logloss=0; hit=0; n=0
for start in range(0, len(test), 500):
    chunk=test[start:start+500]
    cutoff=parse_date(chunk[0]["date"])
    train=[r for r in rows if parse_date(r["date"]) < cutoff]
    stats={}
    for r in train:
        try: hg=int(r["home_goals"]); ag=int(r["away_goals"])
        except: continue
        for team, sc in [(r["home"],hg),(r["away"],ag)]:
            s=stats.get(team, {"n":0,"sc":0}); s["n"]+=1; s["sc"]+=sc; stats[team]=s
    for r in chunk:
        try: hg=int(r["home_goals"]); ag=int(r["away_goals"])
        except: continue
        hs=stats.get(r["home"]); aws=stats.get(r["away"])
        hxg=1.55; axg=1.25
        if hs and hs["n"]>=5: hxg=hs["sc"]/hs["n"]*1.10
        if aws and aws["n"]>=5: axg=aws["sc"]/aws["n"]
        hw=d=aw=0
        for x in range(11):
            for y in range(11):
                p=poisson(hxg,x)*poisson(axg,y)
                if x>y: hw+=p
                elif x==y: d+=p
                else: aw+=p
        tot=hw+d+aw; hw/=tot; d/=tot; aw/=tot
        real=0 if hg>ag else 1 if hg==ag else 2
        probs=[hw,d,aw]
        brier+=sum((probs[i]-(1 if i==real else 0))**2 for i in range(3))
        logloss+=-math.log(max(1e-9, probs[real]))
        if probs.index(max(probs))==real: hit+=1
        n+=1
print(f"Walk-Forward n={n}")
print(f"Brier (lower better, 0-2): {brier/n:.4f}")
print(f"Log-Loss (lower better): {logloss/n:.4f}")
print(f"1X2 Hit: {hit/n*100:.1f}% ({hit}/{n})")
print("Note: Train only on past - No future leakage")
