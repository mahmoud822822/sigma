import csv
rows=list(csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")))
gold=[r for r in rows if float(r.get("GoldenOdds",9))<=1.25]
gold=sorted(gold, key=lambda r: float(r.get("GoldenOdds",9)))
picked=[]; used=set()
for r in gold:
    try: h,a=r["match"].split(" vs ")
    except: continue
    if h in used or a in used: continue
    # ننوع: واحد 1X وواحد Over وواحد X2/12
    picked.append(r); used.add(h); used.add(a)
    if len(picked)==3: break
comb=1.0
print("🏆 ACCA Golden x3 - Diversified:")
for r in picked:
    od=float(r["GoldenOdds"]); comb*=od
    print(f"- {r['match']} - {r['Golden']} - Fair {od}")
print(f"Combined Fair Odds: {comb:.2f} - Prob {100/comb:.1f}%")
