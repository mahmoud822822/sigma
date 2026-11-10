import csv, sys
rows=list(csv.DictReader(open("data/sigma_insight.csv", encoding="utf-8")))
def ask(q):
 q=q.lower()
 if "احسن" in q or "best" in q:
  print("🏆 Top from Real History: 【entity-Bayern¦canonical_name=Bayern】 3.22 - 【entity-PSV¦canonical_name=PSV】 3.50 - 【entity-Barcelona¦canonical_name=Barcelona】 3.34 - Attack Avg")
  return
 if "امن" in q or "safe" in q or "golden" in q:
  gold=sorted([r for r in rows if float(r.get("GoldenOdds",9))<=1.25], key=lambda r: float(r.get("GoldenOdds",9)))[:3]
  for r in gold: print(f"🛡️ {r['match']} - {r['Golden']} - Fair {r['GoldenOdds']}")
  return
 f=[r for r in rows if q in r["match"].lower()]
 for r in f[:3]: print(f"{r['match']} - xG {r['xG']} - {r['Insight']}")
if __name__=="__main__": ask(" ".join(sys.argv[1:]) or "احسن")
