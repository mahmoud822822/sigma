import csv
rows=list(csv.DictReader(open("data/sigma_mega_golden.csv", encoding="utf-8")))
gold=[r for r in rows if float(r.get("GoldenOdds",9))<=1.25]
gold=sorted(gold, key=lambda r: float(r.get("GoldenOdds",9)))[:3]
comb=1.0
print("🏆 ACCA Golden x3:")
for r in gold:
    od=float(r["GoldenOdds"]); comb*=od
    print(f"- {r['match']} - {r['Golden']} - Fair {od}")
print(f"Combined Fair Odds: {comb:.2f} - Prob {100/comb:.1f}%")
print("Note: Risk multiplies - max 3 legs")
