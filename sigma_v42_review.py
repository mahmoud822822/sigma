#!/usr/bin/env python3
# Sigma V42 Review - Gate before upload. FAIL = do NOT upload.
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# Checks V42 bulk file. Exit 0 = PASS, Exit 1 = FAIL (blocks upload).
import csv, sys, json
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent
DATA = BASE / "data"

def main():
    p = DATA / "sigma_bulk_predictions_v42.csv"
    if not p.exists():
        print("FAIL: data/sigma_bulk_predictions_v42.csv not found - run sigma_v42_engine.py first")
        return 1
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    print(f"Review V42 - rows: {len(rows)}")
    fails = []
    # 1. No missing team names
    missing = [r for r in rows if not r.get("home") or not r.get("away") or r.get("home") in ("—", "?", "") or r.get("away") in ("—", "?", "")]
    if missing:
        fails.append(f"Missing team names: {len(missing)} rows (must be 0)")
    else:
        print("PASS: team names present (0 missing, no '—')")
    # 2. No duplicates
    keys = [(r["date"], r["home"].lower(), r["away"].lower()) for r in rows]
    dup = len(keys) - len(set(keys))
    if dup > 0:
        fails.append(f"Duplicates: {dup} (must be 0)")
    else:
        print("PASS: duplicates 0")
    # 3. Conf range 5-85
    bad_conf = []
    for r in rows:
        try:
            c = float(r.get("sigma_cal") or r.get("sigma20") or 0)
            if not (5 <= c <= 85):
                bad_conf.append(r)
        except Exception:
            bad_conf.append(r)
    if bad_conf:
        fails.append(f"Conf out of 5-85: {len(bad_conf)} rows")
    else:
        print("PASS: all calibrated Conf in 5-85")
    # 4. Golden contains 0 DEFAULT
    golden = [r for r in rows if r.get("golden") == "1"]
    golden_default = [r for r in golden if r.get("is_default") == "1"]
    if golden_default:
        fails.append(f"Golden contains DEFAULT: {len(golden_default)} (must be 0)")
    else:
        print(f"PASS: Golden {len(golden)} with 0 DEFAULT")
    # 5. Golden distinct xG - no mass identical predictions
    if golden:
        c = Counter(r["xG"] for r in golden)
        top_xg, top_n = c.most_common(1)[0]
        if top_n > max(3, len(golden) * 0.3):
            fails.append(f"Golden identical xG: '{top_xg}' repeats {top_n}/{len(golden)} - same-home-unknown-away bug")
        else:
            print(f"PASS: Golden distinct - most common xG '{top_xg}' x{top_n} / {len(golden)}")
    # 6. xG present
    bad_xg = [r for r in rows if not r.get("xG") or "-" not in r.get("xG", "")]
    if bad_xg:
        fails.append(f"Missing xG: {len(bad_xg)}")
    else:
        print("PASS: xG present for all rows")
    # 7. More markets present
    need = ["Over15", "Over35", "Under25", "DC1X", "DC12", "DCX2", "CS_Home", "CS_Away", "sigma_cal", "is_future"]
    missing_cols = [col for col in need if col not in rows[0].keys()] if rows else need
    if missing_cols:
        fails.append(f"Missing market columns: {missing_cols}")
    else:
        print(f"PASS: more markets present: {', '.join(need)}")
    # 8. Future labelled
    fut = [r for r in rows if r.get("is_future") == "1"]
    print(f"INFO: Future (>30d) {len(fut)} rows, DEFAULT {sum(1 for r in rows if r.get('is_default')=='1')} rows")
    # 9. v42.json exists and matches
    j = DATA / "sigma_v42.json"
    if not j.exists():
        fails.append("Missing data/sigma_v42.json")
    else:
        snap = json.load(open(j, encoding="utf-8"))
        if snap.get("future") != len(rows):
            fails.append(f"v42.json future {snap.get('future')} != bulk rows {len(rows)}")
        else:
            print(f"PASS: v42.json matches bulk ({len(rows)}), Backtest {snap['backtest']['hit_rate']}%")
    if fails:
        print("\nREVIEW FAILED - DO NOT UPLOAD:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nREVIEW PASSED - safe to upload")
    print("Promoting v42 bulk to main bulk file (backup first)...")
    import shutil
    main_bulk = DATA / "sigma_bulk_predictions.csv"
    if main_bulk.exists():
        shutil.copy(main_bulk, DATA / "sigma_bulk_predictions.backup_v41.csv")
        print("Backup: data/sigma_bulk_predictions.backup_v41.csv")
    shutil.copy(p, main_bulk)
    print("Promoted: data/sigma_bulk_predictions_v42.csv -> data/sigma_bulk_predictions.csv")
    print("Old V41 file preserved as backup, V41 engine/view untouched.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
