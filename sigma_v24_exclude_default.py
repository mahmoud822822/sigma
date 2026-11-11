# V24: Exclude no-data teams from Golden/Acca - Mahmoud Emad
import csv, json
from pathlib import Path
missing = set(json.load(open("data/sigma_missing_teams.json", encoding="utf-8"))) if Path("data/sigma_missing_teams.json").exists() else set()
# Check next month predictions
p = Path("data/sigma_next_month.csv")
if not p.exists(): print("No sigma_next_month.csv - run auto_fetch first"); exit()
rows = list(csv.DictReader(open(p, encoding="utf-8")))
fixed=0
for r in rows:
    m=r.get("match","")
    if " vs " in m:
        h,a=m.split(" vs ")
        if h.strip() in missing or a.strip() in missing:
            if r.get("tier") in ("Gold","Golden"):
                r["tier"]="DEFAULT"; fixed+=1
print(f"Checked {len(rows)} predictions - Fixed {fixed} Golden -> DEFAULT (no data teams)")
# Save
with open("data/sigma_next_month.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("Saved: Golden now only for teams with real data")
