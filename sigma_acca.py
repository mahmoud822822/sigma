import csv
rows=list(csv.DictReader(open("data/sigma_mega_predictions.csv", encoding="utf-8")))
print(f"Pred rows: {len(rows)} - cols: {list(rows[0].keys())[:12]}")
def f(r,k,default=0):
    try: return float(r.get(k, default) or default)
    except: return default
cands=[]
for r in rows:
    match=r.get("match") or f"{r.get('home','')} vs {r.get('away','')}"
    p1=f(r,"1"); px=f(r,"X"); p2=f(r,"2")
    btts=f(r,"BTTS"); over=f(r,"Over25") if "Over25" in r else f(r,"Over 2.5")
    # Convert 0-1 to 0-100 if needed
    if p1<=1.5: p1*=100; px*=100; p2*=100
    if btts<=1.5: btts*=100
    if over<=1.5: over*=100
    opts=[]
    # Only value range 70-85% - not trivial 95% and not risky 50%
    for name, prob in [("1X",p1+px),("X2",px+p2),("BTTS",btts),("Over 2.5",over)]:
        if 70 <= prob <= 85:
            opts.append((name, prob, 100/prob))
    for name, prob, odds in opts:
        cands.append({"match":match,"market":name,"prob":prob,"odds":odds})
# Sort by prob desc - safest value first
cands=sorted(cands, key=lambda x: x["prob"], reverse=True)
picked=[]; used=set(); markets=set()
for c in cands:
    try: h,a=c["match"].split(" vs ")
    except: continue
    if h in used or a in used: continue
    if c["market"] in markets: continue
    picked.append(c); used.add(h); used.add(a); markets.add(c["market"])
    if len(picked)==3: break
if len(picked)<3:
    print("NO VALID ACCA - Do not force. Need 3 different markets 70-85%")
    for c in cands[:8]: print(f" - {c['match']} - {c['market']} {c['prob']:.1f}% - {c['odds']:.2f}")
else:
    comb=1.0
    print("ACCA x3 - Value 70-85% - Diversified:")
    for c in picked:
        comb*=c["odds"]
        print(f"- {c['match']} - {c['market']} {c['prob']:.1f}% - Fair {c['odds']:.2f}")
    print(f"Combined: {comb:.2f} - Prob {100/comb:.1f}%")
