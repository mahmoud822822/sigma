#!/usr/bin/env python3
# Sigma V44 Review - Gate before upload. FAIL = do NOT upload.
import csv, sys, json, shutil
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
    p = DATA / "sigma_bulk_predictions_v44.json"
    if not p.exists():
        print("FAIL: data/sigma_bulk_predictions_v44.json not found - run sigma_v44_engine.py first")
        return 1
    data = json.load(open(p, encoding="utf-8"))
    rows = data.get("matches", []) if isinstance(data, dict) else data
    print(f"Review V44 Universal - rows: {len(rows)}")
    fails = []
    bad_names = [r for r in rows if not r.get("home_team") or not r.get("away_team")
                 or is_numeric(r.get("home_team")) or is_numeric(r.get("away_team"))
                 or r.get("home_team") in ("—", "?", "") or r.get("away_team") in ("—", "?", "")]
    if bad_names:
        fails.append(f"Bad team names: {len(bad_names)} - e.g. {bad_names[0] if bad_names else ''}")
    else:
        print("PASS: team names present, none numeric")
    keys = [(r["date"], str(r["home_team"]).lower(), str(r["away_team"]).lower(), str(r.get("league","")).lower()) for r in rows]
    dup = len(keys) - len(set(keys))
    if dup > 0:
        fails.append(f"Duplicates: {dup}")
    else:
        print("PASS: duplicates 0")
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
        print("PASS: all prob sums 90-110")
    bad_xg = []
    for r in rows:
        try:
            h, a = str(r["xG"]).split("-")
            if abs(float(h) - float(r["xG_home"])) > 0.01 or abs(float(a) - float(r["xG_away"])) > 0.01:
                bad_xg.append(r.get("match"))
        except Exception:
            bad_xg.append(r.get("match"))
    if bad_xg:
        fails.append(f"xG mismatch: {len(bad_xg)}")
    else:
        print("PASS: xG string matches xG_home/xG_away")
    bad_conf = [r for r in rows if not (5 <= float(r.get("sigma_cal", 0)) <= 85)]
    if bad_conf:
        fails.append(f"Conf out of 5-85: {len(bad_conf)}")
    else:
        print("PASS: all sigma_cal in 5-85")
    golden = [r for r in rows if r.get("golden") == 1]
    gd = [r for r in golden if r.get("is_default") == 1]
    gg = [r for r in golden if r.get("grade") == "D"]
    if gd:
        fails.append(f"Golden contains DEFAULT: {len(gd)}")
    elif gg:
        fails.append(f"Golden contains Grade D: {len(gg)}")
    else:
        print(f"PASS: Golden {len(golden)} with 0 DEFAULT and 0 Grade D")
    bad_tier = [r for r in rows if r.get("tier") == "Gold" and not (r.get("grade") in ("A", "B") and float(r.get("sigma_cal", 0)) >= 70 and r.get("is_default") == 0)]
    if bad_tier:
        fails.append(f"Tier Gold without A/B+70+not-default: {len(bad_tier)}")
    else:
        print("PASS: Tier Gold rule holds")
    bad_dir = [r for r in rows if not r.get("direction") or not r.get("direction_arrow")]
    if bad_dir:
        fails.append(f"Missing direction: {len(bad_dir)}")
    else:
        print("PASS: direction + direction_arrow present")
    # V44 universal fields
    bad_src = [r for r in rows if r.get("source") not in ("AUTO", "OPEN", "MANUAL")]
    if bad_src:
        fails.append(f"Bad source (must be AUTO/OPEN/MANUAL): {len(bad_src)}")
    else:
        print("PASS: source is AUTO/OPEN/MANUAL for all rows")
    bad_type = [r for r in rows if r.get("competition_type") not in ("LEAGUE", "CUP", "NATIONAL", "FRIENDLY")]
    if bad_type:
        fails.append(f"Bad competition_type: {len(bad_type)} - e.g. {bad_type[:2]}")
    else:
        print("PASS: competition_type is LEAGUE/CUP/NATIONAL/FRIENDLY")
    bad_comp = [r for r in rows if not r.get("competition")]
    if bad_comp:
        fails.append(f"Missing competition: {len(bad_comp)}")
    else:
        print("PASS: competition present for all rows")
    # Manual preservation: every manual fixture must survive to predictions
    manual_p = DATA / "sigma_manual_fixtures.csv"
    if manual_p.exists():
        try:
            mrows = list(csv.DictReader(open(manual_p, encoding="utf-8")))
            mrows = [r for r in mrows if (r.get("home_team") or "").strip() and (r.get("away_team") or "").strip()]
            missing = []
            for mr in mrows:
                h = (mr.get("home_team") or "").strip().lower()
                a = (mr.get("away_team") or "").strip().lower()
                if not any(str(r.get("home_team","")).lower() == h and str(r.get("away_team","")).lower() == a for r in rows):
                    missing.append(f"{mr.get('home_team')} vs {mr.get('away_team')}")
            if missing:
                fails.append(f"Manual fixtures lost: {missing}")
            else:
                print(f"PASS: all {len(mrows)} manual fixtures preserved in predictions")
        except Exception as e:
            print(f"WARN: manual check failed ({e})")
    j = DATA / "sigma_v44.json"
    if not j.exists():
        fails.append("Missing data/sigma_v44.json")
    else:
        snap = json.load(open(j, encoding="utf-8"))
        if snap.get("future") != len(rows):
            fails.append(f"v44.json future {snap.get('future')} != rows {len(rows)}")
        else:
            print(f"PASS: v44.json matches ({len(rows)}), Backtest {snap['backtest']['hit_rate']}%")
            print(f"      By source: {snap.get('by_source')}  By type: {snap.get('by_competition_type')}")
    if fails:
        print("\nREVIEW FAILED - DO NOT UPLOAD:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nREVIEW PASSED - safe to upload")
    print("Promoting v44 JSON+CSV to main files (backup first)...")
    for src_name, dst_name, backup_name in [
        ("sigma_bulk_predictions_v44.json", "sigma_bulk_predictions.json", "sigma_bulk_predictions.backup_v43.json"),
        ("sigma_bulk_predictions_v44.csv", "sigma_bulk_predictions.csv", "sigma_bulk_predictions.backup_v43.csv"),
    ]:
        src = DATA / src_name
        dst = DATA / dst_name
        if dst.exists():
            shutil.copy(dst, DATA / backup_name)
            print(f"Backup: data/{backup_name}")
        shutil.copy(src, dst)
        print(f"Promoted: data/{src_name} -> data/{dst_name}")
    print("Old V43 files preserved as backup, V43 engine/view untouched.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
