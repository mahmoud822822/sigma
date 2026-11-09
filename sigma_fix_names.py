import csv, unicodedata, re
from pathlib import Path
def clean(n):
    n=unicodedata.normalize("NFKD", n).encode("ascii","ignore").decode()
    n=n.lower().strip()
    n=re.sub(r"[^a-z0-9 ]","",n)
    n=re.sub(r"\b(fc|cf|afc|sc|ac|ssc|us|rcd|real|club|【entity-sporting¦canonical_name=Sporting CP】|sp)\b","",n).strip()
    n=re.sub(r"\s+"," ",n)
    m={"【entity-bayern munich¦canonical_name=Bayern】":"【entity-bayern munich¦canonical_name=Bayern】","【entity-bayern¦canonical_name=Bayern】 munchen":"【entity-bayern munich¦canonical_name=Bayern】","【entity-psv eindhoven¦canonical_name=PSV】":"【entity-psv¦canonical_name=PSV】","【entity-psv¦canonical_name=PSV】":"【entity-psv¦canonical_name=PSV】","【entity-lille osc¦canonical_name=Lille】":"【entity-lille¦canonical_name=Lille】","【entity-lille¦canonical_name=Lille】":"【entity-lille¦canonical_name=Lille】","paris sg":"paris saint germain","paris saint germain":"paris saint germain","man city":"manchester city","manchester city":"manchester city","sp lisbon":"sporting lisbon","sporting lisbon":"sporting lisbon","sporting":"sporting lisbon"}
    return m.get(n, n)
rows=list(csv.DictReader(open("data/sigma_history.csv", encoding="utf-8")))
for r in rows:
    r["home_team"]=clean(r.get("home_team","")); r["away_team"]=clean(r.get("away_team",""))
rows.sort(key=lambda x: x["date"])
with open("data/sigma_history.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["date","home_team","away_team","home_goals","away_goals","league","status","match_id"]); w.writeheader(); w.writerows(rows)
print(f"Fixed names: {len(rows)} - check: bayern count {sum(1 for r in rows if 'bayern' in r['home_team'] or 'bayern' in r['away_team'])}")
