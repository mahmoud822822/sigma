#!/usr/bin/env python3
# Sigma V54 CHECK - Remaining fakes must be gone, real bulk kept
import json, sys
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"
fails=[]
def fail(m): fails.append(m); print("FAIL:",m)
def ok(m): print("OK:",m)
print("Sigma V54 CHECK")
bulk=DATA/"sigma_bulk_predictions.json"
if not bulk.exists(): fail("Bulk missing")
else:
    obj=json.loads(bulk.read_text(encoding="utf-8")); rows=obj.get("matches", obj) if isinstance(obj, dict) else obj
    print(f"Rows: {len(rows)} (V53 was 840, V54 should be 835-840)")
    if len(rows)>840: fail(f"Rows {len(rows)} > 840 - fake re-added?")
    if len(rows)<830: fail(f"Rows {len(rows)} < 830 - real data wiped? V54 must NOT wipe to 14")
    else: ok(f"Real bulk kept: {len(rows)} (not wiped)")
    for r in rows:
        m=str(r.get("match","")); d=str(r.get("date",""))[:10]
        if (m,d) in [("Real Madrid vs Barcelona","2026-11-17"),("Man City vs Arsenal","2026-11-18"),("Inter vs Milan","2026-11-19"),("England vs Croatia","2026-11-12"),("Brazil vs Argentina","2026-11-20"),("Al Ahly vs Zamalek","2026-11-15"),("Al Hilal vs Al Nassr","2026-11-16")]:
            fail(f"FAKE still present: {m} {d}")
    ok("No manual fake in bulk")
    if "canonical_name" in bulk.read_text(encoding="utf-8"): fail("canonical leak")
    else: ok("No canonical leak")
    if not (DATA/"sigma_quarantine_fake_v54.json").exists(): fail("V54 quarantine missing")
    else:
        q=json.loads((DATA/"sigma_quarantine_fake_v54.json").read_text(encoding="utf-8"))
        ok(f"Quarantine V54 {q.get('count_v54',0)} + total 53+54 {q.get('count_total',0)}")
print("="*50)
if fails: print(f"BLOCKED {len(fails)}"); sys.exit(1)
print("PASS - V54 real complete, safe to push")
