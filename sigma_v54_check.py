#!/usr/bin/env python3
# Sigma V54 CHECK V54.1 - consistent with V44.1 No confirmed data + Learn-From-Past + V54 REAL COMPLETE.
# OLD (wrong) expectation: bulk must be 835-840 rows. That bulk INCLUDED the 7 manual fakes.
# V54 real complete says: Real total in workspace = 14 verified, NOT 842.
# CORRECTION 2026-11-14: England vs Croatia was listed as FAKE in V54 but web-verified
# 2-1 on 2026-11-12 (Sportradar/Gulf News/Sportsmole). It is CORRECTED: in history, not fake.
# Remaining manual fakes: 6. Quarantine 59 = 6 fakes + 1 corrected + 49 history dup + 3 future unverified.
import json, sys, csv
from pathlib import Path
BASE = Path(__file__).parent; DATA = BASE / "data"
NO_DATA = "No confirmed data"
MANUAL_FAKES_6 = [("Real Madrid vs Barcelona", "2026-11-17"), ("Man City vs Arsenal", "2026-11-18"),
            ("Inter vs Milan", "2026-11-19"), ("Brazil vs Argentina", "2026-11-20"),
            ("Al Ahly vs Zamalek", "2026-11-15"), ("Al Hilal vs Al Nassr", "2026-11-16")]
fails = []
def fail(m): fails.append(m); print("FAIL:", m)
def ok(m): print("OK:", m)
print("Sigma V54 CHECK V54.1 (bulk = real only, fakes in no-data, passed learned)")
rc_p = BASE / "sigma_v54_real_complete.json"
if not rc_p.exists(): fail("sigma_v54_real_complete.json missing")
else:
    rc = json.loads(rc_p.read_text(encoding="utf-8"))
    vc = (rc.get("real", {}) or {}).get("verified_count")
    if vc != 14: fail(f"Real verified_count {vc} != 14")
    else: ok("Real verified = 14 (V54 real complete, NOT 842)")
# History must contain learned results, not the fake row
hist_p = DATA / "sigma_history.csv"
if not hist_p.exists(): fail("History missing")
else:
    hrows = list(csv.DictReader(open(hist_p, encoding="utf-8")))
    print(f"History rows: {len(hrows)} (was 1 fake, now learned)")
    if len(hrows) < 40: fail(f"History {len(hrows)} < 40 - learner did not store passed verified results")
    else: ok(f"History has {len(hrows)} learned rows")
    fake = [r for r in hrows if r.get("date") == "2026-10-01" and (r.get("home") or "") in ("Man Utd",) and (r.get("away") or "") in ("Villa", "Aston Villa")]
    if fake: fail("Fake history row still present (Man Utd vs Villa 2-1 2026-10-01)")
    else: ok("Fake history row quarantined (not learned)")
    eng = [r for r in hrows if r.get("date") == "2026-11-12" and (r.get("home") or "") == "England" and (r.get("away") or "") == "Croatia"]
    if not eng or eng[0].get("home_goals") != "2" or eng[0].get("away_goals") != "1": fail("England vs Croatia 2-1 not in history (corrected, web-verified)")
    else: ok("England vs Croatia 2-1 in history (V54 fake corrected by web verification)")
bulk_p = DATA / "sigma_bulk_predictions.json"
if not bulk_p.exists(): fail("Bulk missing")
else:
    obj = json.loads(bulk_p.read_text(encoding="utf-8"))
    rows = obj.get("matches", obj) if isinstance(obj, dict) else obj
    print(f"Bulk REAL predictions: {len(rows)} (can be 0 - 0 is honest when no team has >=5 history)")
    if any(r.get("is_default") == 1 for r in rows): fail("Bulk contains DEFAULT rows - fabrication")
    else: ok("Bulk: 0 DEFAULT rows")
    for r in rows:
        if (str(r.get("match", "")), str(r.get("date", ""))[:10]) in MANUAL_FAKES_6: fail(f"FAKE still present as prediction: {r.get('match')} {r.get('date')}")
        if (str(r.get("match", "")), str(r.get("date", ""))[:10]) == ("England vs Croatia", "2026-11-12"): fail("Passed England-Croatia predicted as future (must be learned, not predicted)")
    else: ok("No manual fake / passed fixture in bulk as prediction")
    if "canonical_name" in bulk_p.read_text(encoding="utf-8"): fail("canonical leak")
    else: ok("No canonical leak")
    snap_p = DATA / "sigma_v44.json"
    if snap_p.exists():
        snap = json.loads(snap_p.read_text(encoding="utf-8"))
        if snap.get("future") != len(rows): fail(f"v44.json future {snap.get('future')} != bulk {len(rows)}")
        else: ok(f"Bulk matches v44.json future ({len(rows)})")
nd_p = DATA / "sigma_no_confirmed_data.json"
if not nd_p.exists(): fail("No-data file missing")
else:
    nd = json.loads(nd_p.read_text(encoding="utf-8"))
    nd_rows = nd.get("matches", []) if isinstance(nd, dict) else nd
    bad = [r for r in nd_rows if r.get("xG") != NO_DATA or r.get("pick") != NO_DATA or not (r.get("reason") or "").strip()
           or r.get("prob_1") is not None or r.get("sigma_cal") is not None]
    if bad: fail(f"No-data rows with fabricated numbers / bad labels: {len(bad)}")
    else: ok(f"No-data rows OK: {len(nd_rows)} (all xG/pick = No confirmed data + reason, no numbers)")
    bulk_rows = []
    if bulk_p.exists():
        b = json.loads(bulk_p.read_text(encoding="utf-8")); bulk_rows = b.get("matches", []) if isinstance(b, dict) else b
    covered = {(str(r.get("match", "")), str(r.get("date", ""))[:10]) for r in bulk_rows + nd_rows}
    # Future manuals (15-20 Nov) must be in bulk/no-data; passed England-Croatia must be in history (checked above)
    missing = [m for m in MANUAL_FAKES_6 if m not in covered]
    if missing: fail(f"Future manual fixtures lost (neither in bulk nor no-data): {missing}")
    else: ok(f"All {len(MANUAL_FAKES_6)} future manual fixtures accounted for (bulk + no-data)")
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
print("PASS - V54.1 real complete, safe to push (bulk real only, fakes in no-data, passed learned)")
