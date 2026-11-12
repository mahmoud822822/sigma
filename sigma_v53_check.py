#!/usr/bin/env python3
# Sigma V53 CHECK - No fake manual allowed
import json, sys
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"
fails=[]
def fail(m): fails.append(m); print("FAIL:",m)
def ok(m): print("OK:",m)
print("Sigma V53 CHECK")
bulk=DATA/"sigma_bulk_predictions.json"
if not bulk.exists(): fail("Bulk missing")
else:
    obj=json.loads(bulk.read_text(encoding="utf-8")); rows=obj.get("matches", obj) if isinstance(obj, dict) else obj
    for r in rows:
        if str(r.get("match",""))=="Al Ahly vs Zamalek" and str(r.get("date",""))=="2026-11-15":
            fail("FAKE still present: Al Ahly vs Zamalek 15 Nov")
        if str(r.get("match","")) in ("Al Hilal vs Al Nassr","Al Nassr vs Al Hilal") and str(r.get("date","")) not in ("2026-12-10","2027-01-01"):
            fail(f"FAKE Hilal/Nassr date {r.get('date')}")
    ok(f"Rows after fake removal: {len(rows)} (was 842, fake removed = honest drop)")
    if not (DATA/"sigma_quarantine_fake_v53.json").exists(): fail("Quarantine file missing - fake must be audited, not silently deleted")
    else:
        q=json.loads((DATA/"sigma_quarantine_fake_v53.json").read_text(encoding="utf-8"))
        ok(f"Quarantine has {q.get('count',0)} fake with reasons")
    if "canonical_name" in bulk.read_text(encoding="utf-8"): fail("canonical_name leak back")
    else: ok("No canonical_name leak")
print("="*50)
if fails: print(f"RESULT: BLOCKED - {len(fails)} FAIL"); sys.exit(1)
print("RESULT: PASS - fake removed, safe to push V53")
