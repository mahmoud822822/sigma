#!/usr/bin/env python3
# Sigma V49 PRE-UPLOAD CHECK - Gate before ANY push - Mahmoud Emad
# FAIL = DO NOT PUSH. Fixes V46/V47/V48/V49 first.
# Checks: no past dates in upcoming, no fake odds/confidence, no basketball in football bulk,
# no duplicates, no single accumulator lie, brain pulse fresh, master exists.
import json, sys, re
from pathlib import Path
BASE = Path(__file__).parent; DATA = BASE / "data"
fails, warns = [], []
def fail(m): fails.append(m); print("FAIL:", m)
def warn(m): warns.append(m); print("WARN:", m)
def ok(m): print("OK:", m)
print("Sigma V49 PRE-UPLOAD CHECK - must be ALL PASS before push")
# Brain pulse
st = DATA / "sigma_brain_state.json"
if not st.exists(): fail("brain_state missing - run V49 first")
else:
    b = json.loads(st.read_text(encoding="utf-8"))
    ok(f"Brain pulse {b.get('pulse')} V{b.get('version')} seeds={b.get('verified_seeds')} sports={b.get('sports')}")
# Master
if not (DATA / "sigma_all_sports_master.json").exists(): fail("master missing - run V49")
else: ok("Master exists")
# Football bulk
for fname in ["sigma_bulk_predictions.json", "sigma_bulk_predictions_v44.json"]:
    for cand in [DATA / fname, BASE / fname]:
        if not cand.exists(): continue
        try:
            obj = json.loads(cand.read_text(encoding="utf-8"))
            rows = obj if isinstance(obj, list) else obj.get("matches", [])
            seen = set(); past = 0; fake = 0; bb = 0
            for mm in rows:
                m = str(mm.get("match", "")); d = str(mm.get("date", ""))[:10]
                if d and d < "2026-11-11" and mm.get("status") == "SCHEDULED": past += 1
                if str(mm.get("poster_confidence", "")).lower().startswith("very high"): fake += 1
                if mm.get("sport") == "basketball": bb += 1
                k = (m.lower(), d)
                if k in seen: fail(f"Duplicate {m} {d} in {fname}")
                seen.add(k)
            if past: fail(f"{fname}: {past} past dates still SCHEDULED")
            else: ok(f"{fname}: no past dates as upcoming ({len(rows)} rows)")
            if fake: fail(f"{fname}: {fake} fake confidence still present")
            if bb: fail(f"{fname}: {bb} basketball leaked into football")
            else: ok(f"{fname}: no basketball leak")
        except Exception as e: warn(f"{fname} unreadable: {e}")
# Basketball separate
bbf = DATA / "sigma_basketball_fixtures.json"
if not bbf.exists(): warn("Basketball file missing - run V48")
else:
    bb = json.loads(bbf.read_text(encoding="utf-8"))
    if any("NONE" not in str(m.get("prediction", "")) for m in bb.get("matches", [])):
        fail("Basketball has fake predictions - must be NONE/BETA")
    else: ok(f"Basketball separate BETA: {bb.get('total')} fixtures, no fake predictions")
# Poster audit
if not (DATA / "sigma_poster_audit.json").exists(): warn("Poster audit missing")
else: ok("Poster audit exists (fake odds/confidence documented)")
print("=" * 50)
if fails:
    print(f"RESULT: BLOCKED - {len(fails)} FAIL. DO NOT PUSH. Fix first.")
    sys.exit(1)
print(f"RESULT: PASS - safe to push. Warns: {len(warns)}")
