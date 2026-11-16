import re, json, pathlib
from datetime import date
BASE = pathlib.Path(".")
DATA = BASE / "data"
TODAY = str(date.today())
# READ fakes from V54 on disk
v54_txt = pathlib.Path("sigma_v54_check.py").read_text(encoding="utf-8")
m = re.search(r"MANUAL_FAKES_6\s*=\s*\[(.*?)\]", v54_txt, re.S)
fakes = []
if m:
    for mm, dd in re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', m.group(1)):
        fakes.append((mm, dd))
print("FAKES:", len(fakes), "TODAY:", TODAY)
pu_p = DATA / "sigma_passed_unverified.json"
pu = json.loads(pu_p.read_text(encoding="utf-8")) if pu_p.exists() else {"generated": TODAY, "today": TODAY, "total": 0, "matches": []}
matches = pu.get("matches", [])
keys = set((str(r.get("date",""))[:10], str(r.get("home","")).lower(), str(r.get("away","")).lower()) for r in matches)
added = 0
for mm, dd in fakes:
    if dd < TODAY:
        h = mm.split(" vs ")[0].strip() if " vs " in mm else ""
        a = mm.split(" vs ")[1].strip() if " vs " in mm else ""
        if (dd, h.lower(), a.lower()) not in keys:
            matches.append({"date": dd, "home": h, "away": a, "match": mm, "league": "Default", "status": "PASSED_WITHOUT_VERIFIED_RESULT", "reason": "Passed fake - quarantined, no invented score - tracked here", "home_goals": None, "away_goals": None, "score": None})
            added += 1
            print("ADDED to passed_unverified:", dd, mm)
pu["matches"] = matches
pu["total"] = len(matches)
pu["generated"] = TODAY
pu["today"] = TODAY
pu_p.write_text(json.dumps(pu, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"DONE: added {added}, passed_unverified total now {len(matches)}")
