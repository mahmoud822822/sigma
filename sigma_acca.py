import csv, re
rows=list(csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")))
print(f"Golden rows: {len(rows)}")
def market_of(g):
    g=g.strip()
    if "Over 0.5" in g: return "Over0.5"
    if "Over 1.5" in g: return "Over1.5"
    if "Over 2.5" in g: return "Over2.5"
    if "Under 4.5" in g: return "Under4.5"
    if "Under 3.5" in g: return "Under3.5"
    if "1X" in g: return "1X"
    if "X2" in g: return "X2"
    if "12" in g: return "12"
    if "BTTS" in g: return "BTTS"
    return g[:12]
picked=[]; used=set(); markets=set()
for r in sorted(rows, key=lambda x: float(x.get("GoldenOdds",9))):
    try: odds=float(r.get("GoldenOdds",9))
    except: continue
    # Value filter: skip trivial 1.01-1.24 and risky >1.50
    if odds < 1.25 or odds > 1.50: continue
    g=r.get("Golden","")
    if "Over 0.5" in g: continue
    if "Under 4.5" in g: continue
    if "Under 5.5" in g: continue
    try: h,a=r["match"].split(" vs ")
    except: continue
    if h in used or a in used: continue
    m=market_of(g)
    if m in markets: continue
    picked.append(r); used.add(h); used.add(a); markets.add(m)
    if len(picked)==3: break
if len(picked)<3:
    print("NO VALID ACCA - Do not force. Need 3 different markets with odds 1.25-1.50")
else:
    comb=1.0
    print("ACCA Golden x3 - Diversified Real:")
    for r in picked:
        od=float(r["GoldenOdds"]); comb*=od
        print(f"- {r['match']} - {r['Golden']} - Fair {od}")
    print(f"Combined Fair Odds: {comb:.2f} - Prob {100/comb:.1f}%")
