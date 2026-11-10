# V24: Date fix + Aliases + Missing report - Mahmoud Emad
import csv, json, re
from pathlib import Path
from datetime import datetime
def parse_date(s):
    s=str(s).strip()
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d","%d-%m-%Y","%Y/%m/%d"):
        try: return datetime.strptime(s, fmt)
        except: continue
    return datetime(2000,1,1)
ALIASES = {
 "Real Madrid CF":"Real Madrid","Athletic Club":"Athletic Bilbao","Man City":"Man City","Man Utd":"Man Utd",
 "FC Barcelona":"Barcelona","Barca":"Barcelona","Atletico":"Atletico Madrid","Atletico de Madrid":"Atletico Madrid",
 "Inter":"Inter","AC Milan":"AC Milan","Milan":"AC Milan","Juventus":"Juventus","Juve":"Juventus",
 "Paris Saint-Germain":"Paris SG","PSG":"Paris SG","Bayern":"Bayern Munich","Bayern Munchen":"Bayern Munich",
 "Tottenham":"Tottenham","Spurs":"Tottenham","Man United":"Man Utd","Man City":"Man City",
 "Brighton":"Brighton","Brighton and Hove Albion":"Brighton","Wolves":"Wolves","Wolverhampton":"Wolves",
 "Leeds":"Leeds United","Leicester":"Leicester City","West Ham":"West Ham","Newcastle":"Newcastle",
 "Real Sociedad":"Real Sociedad","Real Betis":"Real Betis","Sevilla":"Sevilla","Valencia":"Valencia",
 "Borussia Dortmund":"Dortmund","Dortmund":"Dortmund","RB Leipzig":"RB Leipzig","Leverkusen":"Bayer Leverkusen",
 "Ajax":"Ajax","PSV":"PSV","Feyenoord":"Feyenoord","Porto":"Porto","Benfica":"Benfica","Sporting":"Sporting CP",
}
Path("data").mkdir(exist_ok=True)
Path("data/sigma_aliases.json").write_text(json.dumps(ALIASES, ensure_ascii=False, indent=2), encoding="utf-8")
# Fix history dates + sort + report missing
p = Path("data/sigma_history_all.csv")
if not p.exists(): p = Path("data/sigma_history.csv")
rows = list(csv.DictReader(open(p, encoding="utf-8")))
for r in rows:
    r["_dt"] = parse_date(r.get("date",""))
    # Normalize names
    for k in ["home","away"]:
        if r.get(k) in ALIASES: r[k] = ALIASES[r[k]]
rows = sorted(rows, key=lambda x: x["_dt"])
# Last N now correct because sorted by datetime
from collections import Counter
c = Counter()
for r in rows: c[r["home"]]+=1; c[r["away"]]+=1
missing = [t for t,n in c.items() if n<5]
print(f"History sorted by datetime: {len(rows)} - First: {rows[0]['date']} Last: {rows[-1]['date']}")
print(f"Teams: {len(c)} - Missing/low (n<5): {len(missing)}")
print(f"Missing sample: {missing[:20]}")
Path("data/sigma_missing_teams.json").write_text(json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8")
# Save sorted back
for r in rows: r.pop("_dt", None)
with open("data/sigma_history_all.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=["season","league_code","league","date","home","away","home_goals","away_goals","result"]); w.writeheader(); w.writerows(rows)
print("Saved: data/sigma_aliases.json + data/sigma_missing_teams.json + sorted history")
print("Rule: Any team in missing list -> Label DEFAULT, excluded from Golden/Acca")
