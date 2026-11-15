import json, re, csv
from pathlib import Path
BASE = Path("."); DATA = BASE / "data"
NO = "No confirmed data"
check_text = (BASE / "sigma_v54_check.py").read_text(encoding="utf-8")
m = re.search(r"MANUAL_FAKES_6\s*=\s*\[(.*?)\]", check_text, re.S)
pairs = re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', m.group(1))
print("FAKES from check:", pairs)
nd_p = DATA / "sigma_no_confirmed_data.json"
nd = json.loads(nd_p.read_text(encoding="utf-8"))
rows = nd.get("matches", [])
cleaned = []; seen = set()
for r in rows:
    r["match"] = str(r.get("match", "")).strip()
    r["home_team"] = str(r.get("home_team", "")).strip()
    r["away_team"] = str(r.get("away_team", "")).strip()
    k = (r["match"], str(r.get("date"))[:10])
    if k in seen: continue
    seen.add(k); cleaned.append(r)
rows = cleaned
covered = {(r.get("match"), str(r.get("date"))[:10]) for r in rows}
added = 0
for match, d in pairs:
    if (match, d) in covered: continue
    h, a = match.split(" vs ")
    rows.append({"date": d, "home_team": h, "away_team": a, "match": match, "league": "Manual", "competition": "Manual", "competition_type": "LEAGUE", "stage": "", "group": "", "source": "MANUAL", "source_detail": "sigma_v54_real_complete.json quarantine", "country": "", "status": NO, "reason": f"V54 quarantine: {match} {d} - FAKE manual date, no verified fixture. No confirmed data, NOT a prediction.", "xG": NO, "pick": NO, "tier": "No Data", "grade": "No Data", "n": 0, "n_home": 0, "n_away": 0, "is_default": 1, "golden": 0})
    added += 1
rows = sorted(rows, key=lambda x: (x["date"], x["match"]))
nd["matches"] = rows; nd["total"] = len(rows)
nd_p.write_text(json.dumps(nd, ensure_ascii=False, indent=2), encoding="utf-8")
with open(DATA / "sigma_no_confirmed_data.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","home_team","away_team","match","league","competition","competition_type","stage","group","source","source_detail","country","status","reason","xG","pick","tier","grade","n","n_home","n_away","is_default","golden"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k,"") for k in ["date","home_team","away_team","match","league","competition","competition_type","stage","group","source","source_detail","country","status","reason","xG","pick","tier","grade","n","n_home","n_away","is_default","golden"]})
print(f"V54 no-data ensured: added {added}, total {len(rows)}")
print("REPR check:", [repr(r["match"]) for r in rows if "【entity-Madrid¦canonical_name=Madrid】" in r["match"] or "City" in r["match"] or r["match"].startswith("【entity-Inter¦canonical_name=Inter】")])
