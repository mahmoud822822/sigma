import re, json, csv, pathlib, sys
from datetime import date
BASE = pathlib.Path(".")
DATA = BASE / "data"
TODAY = str(date.today())
NO_DATA = "No confirmed data"
LB = chr(12304)
RB = chr(12305)
BAR = chr(166)
# 1. CLEAN manual csv - generic, no team names inside this file
mp = DATA / "sigma_manual_fixtures.csv"
t = mp.read_text(encoding="utf-8")
t = re.sub(LB + r".*?canonical_name=([^" + RB + r"]+)" + RB, r"\1", t)
t = re.sub(LB + r".*?" + RB, "", t)
t = t.replace(BAR, "").replace("canonical_name=", "").replace("entity-", "")
lines = []
for line in t.splitlines():
    parts = line.split(",")
    out = []
    for part in parts:
        if "|" in part:
            a, b = [x.strip() for x in part.split("|", 1)]
            part = a if a == b else a
        out.append(part)
    lines.append(",".join(out))
t = "\n".join(lines) + "\n"
mp.write_text(t, encoding="utf-8")
print("CLEANED:")
print(t)
# 2. READ fakes from V54 file on disk, not from chat
v54_txt = pathlib.Path("sigma_v54_check.py").read_text(encoding="utf-8")
m = re.search(r"MANUAL_FAKES_6\s*=\s*\[(.*?)\]", v54_txt, re.S)
fakes = []
if m:
    for mm, dd in re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', m.group(1)):
        fakes.append((mm, dd))
print("FAKES from V54:", len(fakes))
# 3. PATCH review to accept quarantine
rp = pathlib.Path("sigma_v44_review.py")
rt = rp.read_text(encoding="utf-8")
if "quar_keys" not in rt:
    rt = rt.replace("    pu_keys = set()", "    quar_keys = set()\n    try:\n        _q = json.load(open(DATA / \"sigma_quarantine_fake_v54.json\", encoding=\"utf-8\"))\n        for _r in _q.get(\"manual\", []):\n            _mm = (_r.get(\"match\") or \"\").strip()\n            if \" vs \" in _mm:\n                _h,_a = _mm.split(\" vs \",1)\n                quar_keys.add((str(_r.get(\"date\",\"\"))[:10], _h.strip().lower(), _a.strip().lower()))\n    except Exception:\n        pass\n    pu_keys = set()")
    rt = rt.replace("                in_pu = (d, h, a) in pu_keys", "                in_pu = (d, h, a) in pu_keys\n                in_quar = (d, h, a) in quar_keys")
    rt = rt.replace("                if not (in_pred or in_hist or in_pu):", "                if not (in_pred or in_hist or in_pu or in_quar):")
    rp.write_text(rt, encoding="utf-8")
    print("PATCHED review")
# 4. PATCH V54 to read v44 bulk
vp = pathlib.Path("sigma_v54_check.py")
vt = vp.read_text(encoding="utf-8")
if "sigma_bulk_predictions_v44.json" not in vt:
    vt = vt.replace('bulk_p = DATA / "sigma_bulk_predictions.json"', 'bulk_p = DATA / "sigma_bulk_predictions_v44.json"')
    vp.write_text(vt, encoding="utf-8")
    print("PATCHED V54")
# 5. POST - only when --post is passed, after engine
if "--post" in sys.argv:
    bulk_p = DATA / "sigma_bulk_predictions_v44.json"
    nd_p = DATA / "sigma_no_confirmed_data.json"
    snap_p = DATA / "sigma_v44.json"
    bulk = json.loads(bulk_p.read_text(encoding="utf-8"))
    nd = json.loads(nd_p.read_text(encoding="utf-8"))
    rows = bulk.get("matches", [])
    nd_rows = nd.get("matches", [])
    fake_set = set(fakes)
    new_rows = [r for r in rows if (str(r.get("match","")), str(r.get("date",""))[:10]) not in fake_set]
    removed = len(rows) - len(new_rows)
    nd_keys = set((str(r.get("match","")), str(r.get("date",""))[:10]) for r in nd_rows)
    reasons = {}
    try:
        _q = json.loads((DATA / "sigma_quarantine_fake_v54.json").read_text(encoding="utf-8"))
        for _r in _q.get("manual", []):
            reasons[(_r.get("match",""), str(_r.get("date",""))[:10])] = _r.get("reason","")
    except Exception:
        pass
    added = 0
    for mm, dd in fakes:
        if dd >= TODAY:
            if (mm, dd) not in nd_keys:
                lg = "Default"
                try:
                    for _mr in csv.DictReader(open(mp, encoding="utf-8")):
                        _m2 = f"{_mr.get('home_team','').strip()} vs {_mr.get('away_team','').strip()}"
                        if _m2 == mm and str(_mr.get("date",""))[:10] == dd:
                            lg = _mr.get("league") or _mr.get("competition") or "Default"
                            break
                except Exception:
                    pass
                h2 = mm.split(" vs ")[0] if " vs " in mm else ""
                a2 = mm.split(" vs ")[1] if " vs " in mm else ""
                nd_rows.append({"date": dd, "home_team": h2, "away_team": a2, "match": mm, "league": lg, "competition": lg, "competition_type": "LEAGUE", "stage": "", "group": "", "source": "MANUAL", "source_detail": "sigma_manual_fixtures.csv", "country": "", "status": NO_DATA, "reason": "Manual fake - " + NO_DATA + " - kept in no-data until date passes. " + reasons.get((mm,dd),""), "xG": NO_DATA, "xG_home": None, "xG_away": None, "prob_1": None, "prob_X": None, "prob_2": None, "prob_sum": None, "BTTS": None, "Over15": None, "Over25": None, "Over35": None, "Under25": None, "DC1X": None, "DC12": None, "DCX2": None, "CS_Home": None, "CS_Away": None, "conf": None, "sigma20": None, "sigma_cal": None, "grade": "No Data", "pick": NO_DATA, "top3": NO_DATA, "n": 0, "n_home": 0, "n_away": 0, "is_default": 1, "golden": 0, "is_future": 0, "elo_home": None, "elo_away": None, "elo_diff": None, "form_home": "", "form_away": "", "form_points_home": None, "form_points_away": None, "direction": NO_DATA, "direction_arrow": "", "form_trend": NO_DATA, "elo_trend": NO_DATA, "xg_trend": NO_DATA, "tier": "No Data"})
                added += 1
        else:
            nd_rows = [r for r in nd_rows if not (str(r.get("match",""))==mm and str(r.get("date",""))[:10]==dd)]
    nd_rows = sorted(nd_rows, key=lambda x: (x["date"], x["match"]))
    bulk["matches"] = sorted(new_rows, key=lambda x: x.get("sigma_cal",0), reverse=True)
    bulk["total"] = len(new_rows)
    nd["matches"] = nd_rows
    nd["total"] = len(nd_rows)
    bulk_p.write_text(json.dumps(bulk, ensure_ascii=False, indent=2), encoding="utf-8")
    nd_p.write_text(json.dumps(nd, ensure_ascii=False, indent=2), encoding="utf-8")
    if snap_p.exists():
        snap = json.loads(snap_p.read_text(encoding="utf-8"))
        snap["future"] = len(new_rows)
        snap["real_predictions"] = len(new_rows)
        snap["no_confirmed_data"] = len(nd_rows)
        snap["no_confirmed_data_count"] = len(nd_rows)
        snap["total_fixtures"] = len(new_rows) + len(nd_rows) + snap.get("passed_skipped", 0)
        snap["golden_count"] = sum(1 for r in new_rows if r.get("golden")==1)
        snap_p.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"POST done: removed {removed} from bulk, added {added} to no-data, bulk {len(new_rows)}, no-data {len(nd_rows)}")
