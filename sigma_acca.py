import csv
rows=list(csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")))
# امنع Over 0.5 لوحده - ده فخ 1.01
rows=[r for r in rows if "Over 0.5" not in r.get("Golden","")]
gold=[r for r in rows if float(r.get("GoldenOdds",9))<=1.40]
gold=sorted(gold, key=lambda r: float(r.get("GoldenOdds",9)))
picked=[]; used=set(); types=set()
for r in gold:
 try: h,a=r["match"].split(" vs ")
 except: continue
 if h in used or a in used: continue
 g=r.get("Golden","")
 typ="1X" if "1X" in g else "X2" if "X2" in g else "Over" if "Over" in g else "Other"
 if typ in types: continue
 picked.append(r); used.add(h); used.add(a); types.add(typ)
 if len(picked)==3: break
comb=1.0
print("🏆 ACCA Golden x3 - Diversified Real:")
for r in picked:
 od=float(r["GoldenOdds"]); comb*=od
 print(f"- {r['match']} - {r['Golden']} - Fair {od}")
print(f"Combined Fair Odds: {comb:.2f} - Prob {100/comb:.1f}%")
print("لو Combined أقل من 1.30 - متلعبش")
