#!/usr/bin/env python3
# Sigma V44 Review - Gate before upload. FAIL = do NOT upload.
# V44.1 - NO CONFIRMED DATA RULE + Learn-From-Past:
#  Bulk = ONLY real predictions (both teams n>=5, is_default==0, date >= today).
#  Future fixtures without history -> sigma_no_confirmed_data.json/.csv ONLY.
#  Passed fixtures (date < today) are NEVER in bulk/no-data - they are learned
#  (in history if verified) or tracked (passed_unverified if no verified result).
#  Any DEFAULT / fabricated row in bulk = FAIL.
import csv, sys, json, shutil
from pathlib import Path
from datetime import date

BASE = Path(__file__).parent
DATA = BASE / "data"
NO_DATA = "No confirmed data"
TODAY_S = str(date.today())

def is_numeric(s):
    try: float(str(s).strip()); return True
    except Exception: return False

def main():
    p = DATA / "sigma_bulk_predictions_v44.json"
    nd_p = DATA / "sigma_no_confirmed_data.json"
    if not p.exists():
        print("FAIL: data/sigma_bulk_predictions_v44.json not found - run sigma_v44_engine.py first")
        return 1
    data = json.load(open(p, encoding="utf-8"))
    rows = data.get("matches", []) if isinstance(data, dict) else data
    no_data = []
    if nd_p.exists():
        nd = json.load(open(nd_p, encoding="utf-8"))
        no_data = nd.get("matches", []) if isinstance(nd, dict) else nd
    print(f"Review V44 - REAL predictions: {len(rows)} | No confirmed data: {len(no_data)} | Today {TODAY_S}")
    fails = []
    bad_names = [r for r in rows if not r.get("home_team") or not r.get("away_team")
                 or is_numeric(r.get("home_team")) or is_numeric(r.get("away_team"))
                 or r.get("home_team") in ("-", "?", "") or r.get("away_team") in ("-", "?", "")]
    if bad_names: fails.append(f"Bad team names: {len(bad_names)}")
    else: print("PASS: team names present, none numeric")
    keys = [(r["date"], str(r["home_team"]).lower(), str(r["away_team"]).lower(), str(r.get("league", "")).lower()) for r in rows]
    dup = len(keys) - len(set(keys))
    if dup > 0: fails.append(f"Duplicates: {dup}")
    else: print("PASS: duplicates 0")
    past_in_bulk = [r for r in rows if str(r.get("date", ""))[:10] < TODAY_S]
    if past_in_bulk: fails.append(f"PASSED fixtures predicted as future in bulk: {[r.get('match') for r in past_in_bulk]} - passed events must be learned, not predicted")
    else: print("PASS: no passed fixtures in bulk (passed events are learned, not predicted)")
    default_rows = [r for r in rows if r.get("is_default") == 1]
    if default_rows: fails.append(f"FABRICATED DEFAULT rows in bulk: {len(default_rows)} - e.g. {[r.get('match') for r in default_rows[:3]]}")
    else: print("PASS: 0 DEFAULT rows in bulk (refused, not invented)")
    nodata_in_bulk = [r for r in rows if r.get("xG") == NO_DATA or r.get("pick") == NO_DATA]
    if nodata_in_bulk: fails.append(f"No-confirmed-data rows mixed into bulk: {len(nodata_in_bulk)}")
    else: print("PASS: no No-confirmed-data rows mixed into bulk")
    bad_sum = []
    for r in rows:
        try:
            s = float(r["prob_1"]) + float(r["prob_X"]) + float(r["prob_2"])
            if not (90 <= s <= 110): bad_sum.append((r.get("match"), s))
        except Exception: bad_sum.append((r.get("match"), "missing"))
    if bad_sum: fails.append(f"Prob sum not 90-110: {len(bad_sum)} - e.g. {bad_sum[:3]}")
    else: print("PASS: all prob sums 90-110")
    bad_xg = []
    for r in rows:
        try:
            h, a = str(r["xG"]).split("-")
            if abs(float(h) - float(r["xG_home"])) > 0.01 or abs(float(a) - float(r["xG_away"])) > 0.01: bad_xg.append(r.get("match"))
        except Exception: bad_xg.append(r.get("match"))
    if bad_xg: fails.append(f"xG mismatch: {len(bad_xg)}")
    else: print("PASS: xG string matches xG_home/xG_away")
    bad_conf = [r for r in rows if not (5 <= float(r.get("sigma_cal", 0)) <= 85)]
    if bad_conf: fails.append(f"Conf out of 5-85: {len(bad_conf)}")
    else: print("PASS: all sigma_cal in 5-85")
    golden = [r for r in rows if r.get("golden") == 1]
    gd = [r for r in golden if r.get("is_default") == 1]
    gg = [r for r in golden if r.get("grade") == "D"]
    if gd: fails.append(f"Golden contains DEFAULT: {len(gd)}")
    elif gg: fails.append(f"Golden contains Grade D: {len(gg)}")
    else: print(f"PASS: Golden {len(golden)} with 0 DEFAULT and 0 Grade D")
    bad_tier = [r for r in rows if r.get("tier") == "Gold" and not (r.get("grade") in ("A", "B") and float(r.get("sigma_cal", 0)) >= 70 and r.get("is_default") == 0)]
    if bad_tier: fails.append(f"Tier Gold without A/B+70+not-default: {len(bad_tier)}")
    else: print("PASS: Tier Gold rule holds")
    bad_dir = [r for r in rows if not r.get("direction") or not r.get("direction_arrow")]
    if bad_dir: fails.append(f"Missing direction: {len(bad_dir)}")
    else: print("PASS: direction + direction_arrow present")
    bad_src = [r for r in rows if r.get("source") not in ("AUTO", "OPEN", "MANUAL")]
    if bad_src: fails.append(f"Bad source (must be AUTO/OPEN/MANUAL): {len(bad_src)}")
    else: print("PASS: source is AUTO/OPEN/MANUAL for all rows")
    bad_type = [r for r in rows if r.get("competition_type") not in ("LEAGUE", "CUP", "NATIONAL", "FRIENDLY")]
    if bad_type: fails.append(f"Bad competition_type: {len(bad_type)}")
    else: print("PASS: competition_type is LEAGUE/CUP/NATIONAL/FRIENDLY")
    bad_comp = [r for r in rows if not r.get("competition")]
    if bad_comp: fails.append(f"Missing competition: {len(bad_comp)}")
    else: print("PASS: competition present for all rows")
    # No-data checks
    if not nd_p.exists():
        fails.append("Missing data/sigma_no_confirmed_data.json - engine must write it (even if 0 rows)")
    else:
        past_in_nd = [r for r in no_data if str(r.get("date", ""))[:10] < TODAY_S]
        if past_in_nd: fails.append(f"PASSED fixtures in no-data file (must be learned, not no-data): {[r.get('match') for r in past_in_nd]}")
        else: print(f"PASS: no passed fixtures in no-data (all future)")
        fabricated = []
        for r in no_data:
            nums = [r.get(k) for k in ("prob_1", "prob_X", "prob_2", "prob_sum", "BTTS", "Over15", "Over25", "Over35", "Under25", "DC1X", "DC12", "DCX2", "CS_Home", "CS_Away", "conf", "sigma20", "sigma_cal", "xG_home", "xG_away", "elo_home", "elo_away")]
            if any(v is not None and not (isinstance(v, str) and v.strip() == "") for v in nums):
                fabricated.append(r.get("match"))
            if r.get("xG") != NO_DATA or r.get("pick") != NO_DATA or r.get("tier") != "No Data" or not (r.get("reason") or "").strip():
                fabricated.append(f"{r.get('match')} (bad No-data label/reason)")
        if fabricated: fails.append(f"No-data rows contain fabricated numbers / bad labels: {fabricated[:5]}")
        else: print(f"PASS: all {len(no_data)} No-confirmed-data rows have NO fabricated numbers")
        nd_keys = [(r["date"], str(r["home_team"]).lower(), str(r["away_team"]).lower()) for r in no_data]
        if len(nd_keys) != len(set(nd_keys)): fails.append("Duplicates inside No-confirmed-data file")
        else: print("PASS: No-confirmed-data duplicates 0")
        real_keys = set((r["date"], str(r["home_team"]).lower(), str(r["away_team"]).lower()) for r in rows)
        if real_keys & set(nd_keys): fails.append(f"Overlap: fixture in BOTH predictions and No-data: {list(real_keys & set(nd_keys))[:3]}")
        else: print("PASS: no overlap between predictions and No-confirmed-data")
    # Passed-unverified file must exist (even if 0 rows) - learner must have run
    pu_p = DATA / "sigma_passed_unverified.json"
    if not pu_p.exists():
        fails.append("Missing data/sigma_passed_unverified.json - run sigma_learn_from_past.py before engine (passed events must be tracked)")
    else:
        pu = json.load(open(pu_p, encoding="utf-8"))
        pu_rows = pu.get("matches", []) if isinstance(pu, dict) else pu
        bad_pu = [r for r in pu_rows if r.get("status") != "PASSED_WITHOUT_VERIFIED_RESULT"]
        if bad_pu: fails.append(f"Passed-unverified rows with wrong status: {len(bad_pu)}")
        else: print(f"PASS: passed-unverified tracked: {len(pu_rows)} (no invented scores)")
    # Manual preservation: future manuals in predictions/no-data; passed manuals in history/passed_unverified
    manual_p = DATA / "sigma_manual_fixtures.csv"
    hist_keys = set()
    try:
        for r in csv.DictReader(open(DATA / "sigma_history.csv", encoding="utf-8")):
            hist_keys.add((str(r.get("date", ""))[:10], str(r.get("home", "")).lower(), str(r.get("away", "")).lower()))
    except Exception: pass
    pu_keys = set()
    if pu_p.exists():
        try:
            pu = json.load(open(pu_p, encoding="utf-8"))
            for r in (pu.get("matches", []) if isinstance(pu, dict) else pu):
                pu_keys.add((str(r.get("date", ""))[:10], str(r.get("home", "")).lower(), str(r.get("away", "")).lower()))
        except Exception: pass
    if manual_p.exists():
        try:
            mrows = list(csv.DictReader(open(manual_p, encoding="utf-8")))
            mrows = [r for r in mrows if (r.get("home_team") or "").strip() and (r.get("away_team") or "").strip()]
            missing = []
            for mr in mrows:
                h = (mr.get("home_team") or "").strip().lower(); a = (mr.get("away_team") or "").strip().lower(); d = (mr.get("date") or "").strip()
                in_pred = any(str(r.get("home_team", "")).lower() == h and str(r.get("away_team", "")).lower() == a for r in rows + no_data)
                in_hist = (d, h, a) in hist_keys
                in_pu = (d, h, a) in pu_keys
                if not (in_pred or in_hist or in_pu):
                    missing.append(f"{mr.get('home_team')} vs {mr.get('away_team')} ({d})")
            if missing: fails.append(f"Manual fixtures lost (not in predictions/no-data/history/passed_unverified): {missing}")
            else: print(f"PASS: all {len(mrows)} manual fixtures preserved (predictions/no-data/history/passed_unverified)")
        except Exception as e: print(f"WARN: manual check failed ({e})")
    j = DATA / "sigma_v44.json"
    if not j.exists(): fails.append("Missing data/sigma_v44.json")
    else:
        snap = json.load(open(j, encoding="utf-8"))
        if snap.get("future") != len(rows): fails.append(f"v44.json future {snap.get('future')} != real rows {len(rows)}")
        elif snap.get("total_fixtures") is not None and snap.get("total_fixtures") != len(rows) + len(no_data) + snap.get("passed_skipped", 0):
            fails.append(f"v44.json total_fixtures {snap.get('total_fixtures')} != real+no-data+passed_skipped {len(rows)+len(no_data)+snap.get('passed_skipped',0)}")
        elif snap.get("no_confirmed_data") is not None and snap.get("no_confirmed_data") != len(no_data):
            fails.append(f"v44.json no_confirmed_data {snap.get('no_confirmed_data')} != {len(no_data)}")
        else:
            print(f"PASS: v44.json matches (real {len(rows)}, no-data {len(no_data)}, passed-skipped {snap.get('passed_skipped',0)}), Backtest {snap['backtest']['hit_rate']}%")
            print(f"      By source: {snap.get('by_source')}  By type: {snap.get('by_competition_type')}")
    if fails:
        print("\nREVIEW FAILED - DO NOT UPLOAD:")
        for f in fails: print(f"  - {f}")
        return 1
    print("\nREVIEW PASSED - safe to upload")
    print(f"REAL predictions: {len(rows)} | No confirmed data: {len(no_data)} | Passed learned/tracked (not predicted)")
    print("Promoting v44 JSON+CSV to main files (backup first)...")
    for src_name, dst_name, backup_name in [
        ("sigma_bulk_predictions_v44.json", "sigma_bulk_predictions.json", "sigma_bulk_predictions.backup_v43.json"),
        ("sigma_bulk_predictions_v44.csv", "sigma_bulk_predictions.csv", "sigma_bulk_predictions.backup_v43.csv"),
    ]:
        src = DATA / src_name; dst = DATA / dst_name
        if dst.exists():
            shutil.copy(dst, DATA / backup_name); print(f"Backup: data/{backup_name}")
        shutil.copy(src, dst); print(f"Promoted: data/{src_name} -> data/{dst_name}")
    print(f"No-data file kept as-is: data/sigma_no_confirmed_data.json/.csv ({len(no_data)} rows)")
    print("Old V43 files preserved as backup, V43 engine/view untouched.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
