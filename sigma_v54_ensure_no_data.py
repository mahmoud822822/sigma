import json
from pathlib import Path
BASE = Path("."); DATA = BASE / "data"
NO = "No confirmed data"
MANUAL_6 = [
  ("【entity-Real Madrid¦canonical_name=Real Madrid】 vs 【entity-Barcelona¦canonical_name=Barcelona】", "2026-11-17", "【entity-Real Madrid¦canonical_name=Real Madrid】", "【entity-Barcelona¦canonical_name=Barcelona】"),
  ("Man City vs 【entity-Arsenal¦canonical_name=Arsenal】", "2026-11-18", "Man City", "【entity-Arsenal¦canonical_name=Arsenal】"),
  ("【entity-Inter¦canonical_name=Inter】 vs 【entity-Milan¦canonical_name=AC Milan】", "2026-11-19", "【entity-Inter¦canonical_name=Inter】", "【entity-Milan¦canonical_name=AC Milan】"),
  ("Brazil vs Argentina", "2026-11-20", "Brazil", "Argentina"),
  ("【entity-Al Ahly¦canonical_name=Al Ahly】 vs 【entity-Zamalek¦canonical_name=Zamalek】", "2026-11-15", "【entity-Al Ahly¦canonical_name=Al Ahly】", "【entity-Zamalek¦canonical_name=Zamalek】"),
  ("【entity-Al Hilal¦canonical_name=Al Hilal】 vs 【entity-Al Nassr¦canonical_name=Al Nassr】", "2026-11-16", "【entity-Al Hilal¦canonical_name=Al Hilal】", "【entity-Al Nassr¦canonical_name=Al Nassr】"),
]
nd_p = DATA / "sigma_no_confirmed_data.json"
nd = json.loads(nd_p.read_text(encoding="utf-8"))
rows = nd.get("matches", [])
covered = {(r.get("match"), str(r.get("date"))[:10]) for r in rows}
added = 0
for match, d, h, a in MANUAL_6:
    if (match, d) in covered:
        continue
    rows.append({"date": d, "home_team": h, "away_team": a, "match": match, "league": "Manual", "competition": "Manual", "competition_type": "LEAGUE", "stage": "", "group": "", "source": "MANUAL", "source_detail": "sigma_v54_real_complete.json quarantine", "country": "", "status": NO, "reason": f"V54 quarantine: {match} {d} - FAKE manual date, no verified fixture. No confirmed data, NOT a prediction.", "xG": NO, "xG_home": None, "xG_away": None, "prob_1": None, "prob_X": None, "prob_2": None, "prob_sum": None, "BTTS": None, "Over15": None, "Over25": None, "Over35": None, "Under25": None, "DC1X": None, "DC12": None, "DCX2": None, "CS_Home": None, "CS_Away": None, "conf": None, "sigma20": None, "sigma_cal": None, "grade": "No Data", "pick": NO, "top3": NO, "n": 0, "n_home": 0, "n_away": 0, "is_default": 1, "golden": 0, "is_future": 0, "elo_home": None, "elo_away": None, "elo_diff": None, "form_home": "", "form_away": "", "form_points_home": None, "form_points_away": None, "direction": NO, "direction_arrow": "", "form_trend": NO, "elo_trend": NO, "xg_trend": NO, "tier": "No Data"})
    added += 1
rows = sorted(rows, key=lambda x: (x["date"], x["match"]))
nd["matches"] = rows; nd["total"] = len(rows)
nd_p.write_text(json.dumps(nd, ensure_ascii=False, indent=2), encoding="utf-8")
import csv
with open(DATA / "sigma_no_confirmed_data.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["date","home_team","away_team","match","league","competition","competition_type","stage","group","source","source_detail","country","status","reason","xG","pick","tier","grade","n","n_home","n_away","is_default","golden"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k,"") for k in ["date","home_team","away_team","match","league","competition","competition_type","stage","group","source","source_detail","country","status","reason","xG","pick","tier","grade","n","n_home","n_away","is_default","golden"]})
print(f"V54 no-data ensured: added {added}, total {len(rows)}")
