#!/usr/bin/env python3
# Sigma V43 Review - Gate before upload. FAIL = do NOT upload.
# Checks JSON-first file. Catches the live V42 bug: numeric team names, prob sum != 100, Grade D + Gold.
import csv, sys, json
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"

def is_numeric(s):
    try:
        float(str(s).strip())
        return True
    except Exception:
        return False

def main():
    p = DATA / "sigma_bulk_predictions_v43.json"
    if not p.exists():
        print("FAIL: data/sigma_bulk_predictions_v43.json not found - run sigma_v43_engine.py first")
        return 1
    data = json.load(open(p, encoding="utf-8"))
    rows = data.get("matches", []) if isinstance(data, dict) else data
    print(f"Review V43 - rows: {len(rows)}")
    fails = []
    # 1. Team names present and NOT numeric
    bad_names = [r for r in rows if not r.get("home_team") or not r.get("away_team")
                 or is_numeric(r.get("home_team")) or is_numeric(r.get("away_team"))
                 or r.get("home_team") in ("—", "?", "") or r.get("away_team") in ("—", "?", "")]
    if bad_names:
        fails.append(f"Bad team names (numeric/missing): {len(bad_names)} - e.g. {bad_names[0] if bad_names else ''}")
    else:
        print("PASS: team names present, none numeric (no '3.12' as team)")
    # 2. No duplicates
    keys = [(r["date"], str(r["home_team"]).lower(), str(r["away_team"]).lower()) for r in rows]
    dup = len(keys) - len(set(keys))
    if dup > 0:
        fails.append(f"Duplicates: {dup}")
    else:
        print("PASS: duplicates 0")
    # 3. Prob sum 90-110 (must sum to ~100, catches Home 0 / Draw 12 / Away 0 bug)
    bad_sum = []
    for r in rows:
        try:
            s = float(r["prob_1"]) + float(r["prob_X"]) + float(r["prob_2"])
            if not (90 <= s <= 110):
                bad_sum.append((r.get("match"), s))
        except Exception:
            bad_sum.append((r.get("match"), "missing"))
    if bad_sum:
        fails.append(f"Prob sum not 90-110: {len(bad_sum)} - e.g. {bad_sum[:3]}")
    else:
        print("PASS: all prob sums 90-110 (1/X/2 sum to ~100)")
    # 4. xG matches home/away - xG_home/xG_away must be numbers, xG string must match them
    bad_xg = []
    for r in rows:
        try:
            xg = str(r["xG"])
            h, a = xg.split("-")
            if abs(float(h) - float(r["xG_home"])) > 0.01 or abs(float(a) - float(r["xG_away"])) > 0.01:
                bad_xg.append(r.get("match"))
        except Exception:
            bad_xg.append(r.get("match"))
    if bad_xg:
        fails.append(f"xG mismatch: {len(bad_xg)}")
    else:
        print("PASS: xG string matches xG_home/xG_away")
    # 5. Conf 5-85
    bad_conf = [r for r in rows if not (5 <= float(r.get("sigma_cal", 0)) <= 85)]
    if bad_conf:
        fails.append(f"Conf out of 5-85: {len(bad_conf)}")
    else:
        print("PASS: all sigma_cal in 5-85")
    # 6. Golden 0 DEFAULT, 0 Grade D
    golden = [r for r in rows if r.get("golden") == 1]
    gd = [r for r in golden if r.get("is_default") == 1]
    gg = [r for r in golden if r.get("grade") == "D"]
    if gd:
        fails.append(f"Golden contains DEFAULT: {len(gd)}")
    elif gg:
        fails.append(f"Golden contains Grade D: {len(gg)} (Grade D can never be Gold)")
    else:
        print(f"PASS: Golden {len(golden)} with 0 DEFAULT and 0 Grade D")
    # 7. Tier consistency: Tier Gold requires grade A/B + sigma>=70 + not default
    bad_tier = [r for r in rows if r.get("tier") == "Gold" and not (r.get("grade") in ("A", "B") and float(r.get("sigma_cal", 0)) >= 70 and r.get("is_default") == 0)]
    if bad_tier:
        fails.append(f"Tier Gold without A/B+70+not-default: {len(bad_tier)}")
    else:
        print("PASS: Tier Gold rule holds (no Grade D Gold)")
    # 8. Direction present
    bad_dir = [r for r in rows if not r.get("direction") or not r.get("direction_arrow")]
    if bad_dir:
        fails.append(f"Missing direction: {len(bad_dir)}")
    else:
        print("PASS: direction + direction_arrow present for all rows")
    # 9. v43.json matches
    j = DATA / "sigma_v43.json"
    if not j.exists():
        fails.append("Missing data/sigma_v43.json")
    else:
        snap = json.load(open(j, encoding="utf-8"))
        if snap.get("future") != len(rows):
            fails.append(f"v43.json future {snap.get('future')} != rows {len(rows)}")
        else:
            print(f"PASS: v43.json matches ({len(rows)}), Backtest {snap['backtest']['hit_rate']}%")
    if fails:
        print("\nREVIEW FAILED - DO NOT UPLOAD:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nREVIEW PASSED - safe to upload")
    print("Promoting v43 JSON+CSV to main files (backup first)...")
    import shutil
    for src_name, dst_name, backup_name in [
        ("sigma_bulk_predictions_v43.json", "sigma_bulk_predictions.json", "sigma_bulk_predictions.backup_v42.json"),
        ("sigma_bulk_predictions_v43.csv", "sigma_bulk_predictions.csv", "sigma_bulk_predictions.backup_v42.csv"),
    ]:
        src = DATA / src_name
        dst = DATA / dst_name
        if dst.exists():
            shutil.copy(dst, DATA / backup_name)
            print(f"Backup: data/{backup_name}")
        shutil.copy(src, dst)
        print(f"Promoted: data/{src_name} -> data/{dst_name}")
    print("Old V42 files preserved as backup, V42 engine/view untouched.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
