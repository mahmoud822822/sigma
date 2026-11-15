#!/usr/bin/env python3
# Sigma FAKE CLEANUP - Automatic, date-safe
# Task 2 - Mahmoud Emad
# Rule: NEVER remove a future fake before its date passes.
#   - Remove ONLY if date < today (strictly passed, not today).
#   - Today itself is KEPT (match may still be played today).
# Removes from 3 places TOGETHER, so files never drift:
#   1. data/sigma_no_confirmed_data.json
#   2. data/sigma_no_confirmed_data.csv (regenerated from JSON)
#   3. data/sigma_v44.json (counts + passed_skipped updated)
# Defensive: also removes passed fake if it leaked into bulk files.
# Manual fakes are ALREADY in quarantine (59) - do NOT add again, do NOT
# add to passed_unverified (passed_unverified is for REAL fixtures only).
# Real passed no-data rows (not manual fakes) go to passed_unverified
# with status PASSED_WITHOUT_VERIFIED_RESULT - no invented score.
# No Arabic inside .py (Termux safety). Stdlib only.
# Usage in Termux:
#   python3 sigma_fake_cleanup.py --dry-run   # show what WOULD be removed, touch nothing
#   python3 sigma_fake_cleanup.py             # real cleanup
#   python3 sigma_fake_cleanup.py --check     # cleanup + run V54 check
# Next fake to clean: Al Hilal vs Al Nassr 2026-11-16 -> run on 2026-11-17.
import argparse, csv, json, shutil, subprocess, sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
NO_DATA = "No confirmed data"

MANUAL_FAKES_6 = [
    ("Al Ahly vs Zamalek", "2026-11-15"),
    ("Al Hilal vs Al Nassr", "2026-11-16"),
    ("Real Madrid vs Barcelona", "2026-11-17"),
    ("Man City vs Arsenal", "2026-11-18"),
    ("Inter vs Milan", "2026-11-19"),
    ("Brazil vs Argentina", "2026-11-20"),
]
MANUAL_SET = set(MANUAL_FAKES_6)

def key_of(match, d):
    return (str(match or "").strip(), str(d or "")[:10])

def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser(description="Sigma fake cleanup - date-safe")
    ap.add_argument("--dry-run", action="store_true", help="Show only, change nothing")
    ap.add_argument("--check", action="store_true", help="Run V54 check after cleanup")
    args = ap.parse_args()
    today = date.today()
    today_s = str(today)
    print(f"Sigma FAKE CLEANUP - Today {today_s} - Rule: remove ONLY date < today")
    nd_json = DATA / "sigma_no_confirmed_data.json"
    nd_csv = DATA / "sigma_no_confirmed_data.csv"
    v44_p = DATA / "sigma_v44.json"
    if not nd_json.exists():
        print("FAIL: data/sigma_no_confirmed_data.json missing - run engine first")
        return 1
    nd = load_json(nd_json) or {}
    rows = nd.get("matches", []) if isinstance(nd, dict) else nd
    print(f"No-data before: {len(rows)}")
    passed = []
    kept = []
    for r in rows:
        d = str(r.get("date", ""))[:10]
        if d and d < today_s:
            passed.append(r)
        else:
            kept.append(r)
    if not passed:
        print("NOTHING TO CLEAN - all no-data rows are future (date >= today).")
        print("Kept:")
        for r in kept:
            print(f"  KEPT (future): {r.get('date')} {r.get('match')}")
        return 0
    manual_passed = [r for r in passed if key_of(r.get("match"), r.get("date")) in MANUAL_SET]
    real_passed = [r for r in passed if key_of(r.get("match"), r.get("date")) not in MANUAL_SET]
    print(f"Passed to remove: {len(passed)} = manual fakes {len(manual_passed)} + real no-data {len(real_passed)}")
    for r in manual_passed:
        print(f"  REMOVE (passed fake, already in quarantine 59): {r.get('date')} {r.get('match')}")
    for r in real_passed:
        print(f"  REMOVE (passed real, -> passed_unverified): {r.get('date')} {r.get('match')}")
    print(f"Kept future: {len(kept)}")
    for r in kept:
        print(f"  KEPT (future): {r.get('date')} {r.get('match')}")
    if args.dry_run:
        print("DRY-RUN - no files changed. Run without --dry-run to apply.")
        return 0
    # Backup
    stamp = today_s.replace("-", "") + "_" + __import__("datetime").datetime.now().strftime("%H%M%S")
    for src in [nd_json, nd_csv, v44_p]:
        if src.exists():
            dst = src.with_suffix(src.suffix + f".bak_{stamp}")
            shutil.copy(src, dst)
            print(f"Backup: {dst.name}")
    # 1+2. Write no-data JSON + CSV together from kept rows
    nd["matches"] = kept
    nd["total"] = len(kept)
    nd["last_fake_cleanup"] = today_s
    nd["removed_passed"] = [{"date": str(r.get("date", ""))[:10], "match": r.get("match"), "type": "manual_fake" if key_of(r.get("match"), r.get("date")) in MANUAL_SET else "real_no_data"} for r in passed]
    nd_json.write_text(json.dumps(nd, ensure_ascii=False, indent=2), encoding="utf-8")
    nd_fields = ["date", "home_team", "away_team", "match", "league", "competition", "competition_type",
                 "stage", "group", "source", "source_detail", "country", "status", "reason",
                 "xG", "pick", "tier", "grade", "n", "n_home", "n_away", "is_default", "golden"]
    with open(nd_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=nd_fields)
        w.writeheader()
        for r in sorted(kept, key=lambda x: (str(x.get("date", "")), str(x.get("match", "")))):
            w.writerow({k: r.get(k, "") for k in nd_fields})
    print(f"Saved: no-data JSON+CSV now {len(kept)} rows")
    # Real passed -> passed_unverified (no invented score)
    if real_passed:
        pu_p = DATA / "sigma_passed_unverified.json"
        pu = load_json(pu_p) if pu_p.exists() else {}
        pu_rows = pu.get("matches", []) if isinstance(pu, dict) else []
        seen = {key_of(r.get("match"), r.get("date")) for r in pu_rows}
        added = 0
        for r in real_passed:
            k = key_of(r.get("match"), r.get("date"))
            if k in seen:
                continue
            pu_rows.append({
                "date": str(r.get("date", ""))[:10], "match": r.get("match"),
                "home_team": r.get("home_team"), "away_team": r.get("away_team"),
                "league": r.get("league"), "status": "PASSED_WITHOUT_VERIFIED_RESULT",
                "reason": "Passed, no verified result - not invented. Was in no-data, cleaned by sigma_fake_cleanup.",
                "xG": NO_DATA, "pick": NO_DATA,
            })
            seen.add(k); added += 1
        pu_out = {"generated": today_s, "total": len(pu_rows), "matches": pu_rows}
        pu_p.write_text(json.dumps(pu_out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: passed_unverified +{added} -> total {len(pu_rows)}")
    # Defensive: remove passed fakes from bulk if leaked
    for bulk_name in ["sigma_bulk_predictions.json", "sigma_bulk_predictions_v44.json"]:
        bp = DATA / bulk_name
        if not bp.exists():
            continue
        b = load_json(bp)
        if not b:
            continue
        brows = b.get("matches", []) if isinstance(b, dict) else b
        before = len(brows)
        brows2 = [r for r in brows if not (key_of(r.get("match"), r.get("date")) in MANUAL_SET and str(r.get("date", ""))[:10] < today_s)]
        if len(brows2) != before:
            if isinstance(b, dict):
                b["matches"] = brows2; b["total"] = len(brows2)
                bp.write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Cleaned bulk leak: {bulk_name} {before} -> {len(brows2)}")
    # 3. Update v44.json counts together
    if v44_p.exists():
        snap = load_json(v44_p) or {}
        bulk_len = 0
        bp = DATA / "sigma_bulk_predictions.json"
        if bp.exists():
            b = load_json(bp)
            if b:
                bulk_len = len(b.get("matches", []) if isinstance(b, dict) else b)
        old_skipped = snap.get("passed_skipped_matches", []) or []
        old_keys = {key_of(r.get("match") if isinstance(r, dict) else "", r.get("date") if isinstance(r, dict) else "") for r in old_skipped}
        new_skipped = list(old_skipped)
        for r in passed:
            entry = {"date": str(r.get("date", ""))[:10], "match": r.get("match"), "reason": "Passed fake cleaned" if key_of(r.get("match"), r.get("date")) in MANUAL_SET else "Passed no-data cleaned"}
            if key_of(r.get("match"), r.get("date")) not in old_keys:
                new_skipped.append(entry)
        snap["no_confirmed_data"] = len(kept)
        snap["no_confirmed_data_count"] = len(kept)
        snap["future"] = bulk_len
        snap["passed_skipped"] = len(new_skipped)
        snap["passed_skipped_matches"] = new_skipped
        snap["total_fixtures"] = bulk_len + len(kept) + len(new_skipped)
        snap["last_fake_cleanup"] = today_s
        snap["last_fake_cleanup_removed"] = [{"date": str(r.get("date", ""))[:10], "match": r.get("match")} for r in passed]
        v44_p.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: v44.json future={bulk_len} no-data={len(kept)} passed_skipped={len(new_skipped)} total={snap['total_fixtures']}")
    # Log
    log_p = DATA / "sigma_fake_cleanup.log"
    with open(log_p, "a", encoding="utf-8") as f:
        f.write(f"{today_s} removed {len(passed)} kept {len(kept)} manual {len(manual_passed)} real {len(real_passed)}\n")
        for r in passed:
            f.write(f"  REMOVED {r.get('date')} {r.get('match')}\n")
    print("DONE - files in sync: no-data JSON + CSV + v44.json")
    if args.check:
        print("\n=== Running V54 check ===")
        for cand in ["sigma_v54_check_v2.py", "sigma_v54_check.py"]:
            cp = BASE / cand
            if cp.exists():
                rr = subprocess.run([sys.executable, str(cp)], cwd=str(BASE))
                return rr.returncode
        print("No V54 check file found")
        return 1
    print("Next: python3 sigma_v54_check_v2.py  (or sigma_v54_check.py if you replaced it)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
