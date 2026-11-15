#!/usr/bin/env python3
# Sigma V54 CHECK - FROZEN V54.2.1 - DATE-AWARE (replaces V54.1)
# V54.1 bug: required ALL 6 manual fakes in bulk+no-data, even passed ones.
#   After cleanup, passed fakes are NOT in no-data -> V54.1 would BLOCK (wrong).
# V54.2 rule:
#   - Future fakes (date >= today) MUST be in bulk+no-data
#   - Passed fakes (date < today) MUST NOT be in bulk/no-data (already in quarantine 59)
#   - Total still 6 = future in files + passed in quarantine/passed_skipped
# Quarantine stays 59 = 6 fakes + 1 corrected + 49 history dup + 3 future unverified.
# No Arabic inside .py. Stdlib only.
import json, sys, csv
from pathlib import Path
from datetime import date
BASE = Path(__file__).parent; DATA = BASE / "data"
NO_DATA = "No confirmed data"
MANUAL_FAKES_6 = [("Real Madrid vs Barcelona", "2026-11-17"), ("Man City vs Arsenal", "2026-11-18"),
            ("Inter vs Milan", "2026-11-19"), ("Brazil vs Argentina", "2026-11-20"),
            ("Al Ahly vs Zamalek", "2026-11-15"), ("Al Hilal vs Al Nassr", "2026-11-16")]
TODAY_S = str(date.today())
fails = []
def fail(m): fails.append(m); print("FAIL:", m)
def ok(m): print("OK:", m)
print(f"Sigma V54 CHECK - FROZEN V54.2.1 - DATE-AWARE - Today {TODAY_S} (bulk=real only, fakes in no-data if future, passed cleaned)")
# FIX V54.2.1: Today is TRANSITIONAL, not future.
#   future = date > today (strictly future, must be in files)
#   passed = date < today (strictly passed, must NOT be in files)
#   today  = date == today (may be in files OR already cleaned early - both OK, no FAIL)
# Why: Ahly 15 Nov was cleaned early on 15 Nov itself. Old V54.2 counted it as
# future (15>=15) and BLOCKED. New logic allows both states on the day itself.
future_fakes = [m for m in MANUAL_FAKES_6 if m[1] > TODAY_S]
passed_fakes = [m for m in MANUAL_FAKES_6 if m[1] < TODAY_S]
today_fakes = [m for m in MANUAL_FAKES_6 if m[1] == TODAY_S]
print(f"Manual fakes: total 6 = future {len(future_fakes)} (date > today) + today {len(today_fakes)} (transitional) + passed {len(passed_fakes)} (date < today)")
rc_p = BASE / "sigma_v54_real_complete.json"
if not rc_p.exists(): fail("sigma_v54_real_complete.json missing")
else:
    rc = json.loads(rc_p.read_text(encoding="utf-8"))
    vc = (rc.get("real", {}) or {}).get("verified_count")
    if vc != 14: fail(f"Real verified_count {vc} != 14")
    else: ok("Real verified = 14 (V54 real complete, NOT 842)")
hist_p = DATA / "sigma_history.csv"
if not hist_p.exists(): fail("History missing")
else:
    hrows = list(csv.DictReader(open(hist_p, encoding="utf-8")))
    print(f"History rows: {len(hrows)} (was 1 fake, now learned)")
    if len(hrows) < 40: fail(f"History {len(hrows)} < 40")
    else: ok(f"History has {len(hrows)} learned rows")
    fake = [r for r in hrows if r.get("date") == "2026-10-01" and (r.get("home") or "") in ("Man Utd",) and (r.get("away") or "") in ("Villa", "Aston Villa")]
    if fake: fail("Fake history row still present (Man Utd vs Villa 2-1 2026-10-01)")
    else: ok("Fake history row quarantined (not learned)")
    eng = [r for r in hrows if r.get("date") == "2026-11-12" and (r.get("home") or "") == "England" and (r.get("away") or "") == "Croatia"]
    if not eng or eng[0].get("home_goals") != "2" or eng[0].get("away_goals") != "1": fail("England vs Croatia 2-1 not in history")
    else: ok("England vs Croatia 2-1 in history (V54 fake corrected by web verification)")
bulk_p = DATA / "sigma_bulk_predictions.json"
bulk_rows = []
if not bulk_p.exists(): fail("Bulk missing")
else:
    obj = json.loads(bulk_p.read_text(encoding="utf-8"))
    bulk_rows = obj.get("matches", obj) if isinstance(obj, dict) else obj
    print(f"Bulk REAL predictions: {len(bulk_rows)} (can be 0 - 0 is honest when no team has >=5 history)")
    if any(r.get("is_default") == 1 for r in bulk_rows): fail("Bulk contains DEFAULT rows - fabrication")
    else: ok("Bulk: 0 DEFAULT rows")
    for r in bulk_rows:
        if (str(r.get("match", "")), str(r.get("date", ""))[:10]) in MANUAL_FAKES_6: fail(f"FAKE still present as prediction: {r.get('match')} {r.get('date')}")
        if (str(r.get("match", "")), str(r.get("date", ""))[:10]) == ("England vs Croatia", "2026-11-12"): fail("Passed England-Croatia predicted as future")
    else: ok("No manual fake / passed fixture in bulk as prediction")
    if "canonical_name" in bulk_p.read_text(encoding="utf-8"): fail("canonical leak")
    else: ok("No canonical leak")
    snap_p = DATA / "sigma_v44.json"
    if snap_p.exists():
        snap = json.loads(snap_p.read_text(encoding="utf-8"))
        if snap.get("future") != len(bulk_rows): fail(f"v44.json future {snap.get('future')} != bulk {len(bulk_rows)}")
        else: ok(f"Bulk matches v44.json future ({len(bulk_rows)})")
nd_p = DATA / "sigma_no_confirmed_data.json"
nd_rows = []
if not nd_p.exists(): fail("No-data file missing")
else:
    nd = json.loads(nd_p.read_text(encoding="utf-8"))
    nd_rows = nd.get("matches", []) if isinstance(nd, dict) else nd
    bad = [r for r in nd_rows if r.get("xG") != NO_DATA or r.get("pick") != NO_DATA or not (r.get("reason") or "").strip() or r.get("prob_1") is not None or r.get("sigma_cal") is not None]
    if bad: fail(f"No-data rows with fabricated numbers: {len(bad)}")
    else: ok(f"No-data rows OK: {len(nd_rows)} (all xG/pick = No confirmed data + reason, no numbers)")
    covered = {(str(r.get("match", "")), str(r.get("date", ""))[:10]) for r in bulk_rows + nd_rows}
    missing_future = [m for m in future_fakes if m not in covered]
    if missing_future: fail(f"Future manual fixtures lost: {missing_future}")
    else: ok(f"All {len(future_fakes)} FUTURE manual fixtures accounted for (bulk + no-data)")
    leaked_passed = [m for m in passed_fakes if m in covered]
    if leaked_passed: fail(f"PASSED fakes still in bulk/no-data (run sigma_fake_cleanup.py): {leaked_passed}")
    else: ok(f"All {len(passed_fakes)} PASSED fakes NOT in bulk/no-data (cleaned, quarantine only) - {passed_fakes}")
    # Today: both states OK - no FAIL
    for m in today_fakes:
        if m in covered:
            print(f"INFO: Today fake still in bulk/no-data (will be cleaned tomorrow): {m}")
        else:
            print(f"INFO: Today fake already cleaned early (quarantine only, OK): {m}")
q_p = DATA / "sigma_quarantine_fake_v54.json"
if not q_p.exists(): fail("V54 quarantine missing")
else:
    qq = json.loads(q_p.read_text(encoding="utf-8"))
    if qq.get("count_v54", 0) != 59 or qq.get("count_total", 0) != 59: fail(f"Quarantine count {qq.get('count_v54')}/{qq.get('count_total')} != 59")
    else: ok("Quarantine V54 59 = 6 fakes + 1 corrected + 49 history dup + 3 future unverified")
lr_p = DATA / "sigma_learning_report.json"
if not lr_p.exists(): fail("Learning report missing - run sigma_learn_from_past.py")
else:
    lr = json.loads(lr_p.read_text(encoding="utf-8"))
    if lr.get("history_after", 0) < 40: fail(f"Learning report history_after {lr.get('history_after')} < 40")
    else: ok(f"Learning report: history {lr.get('history_before')} -> {lr.get('history_after')}, added {lr.get('added_count')}")
print("=" * 50)
if fails: print(f"BLOCKED {len(fails)}"); sys.exit(1)
print(f"PASS - V54.2.1 FROZEN - date-aware (today transitional), safe to push (bulk real only, future fakes in no-data, passed cleaned)")
