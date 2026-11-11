#!/usr/bin/env python3
# Sigma V52 CHECK - Gate before push
import json, sys
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"
fails=[]
def fail(m): fails.append(m); print("FAIL:",m)
def ok(m): print("OK:",m)
print("Sigma V52 CHECK")
bulk=DATA/"sigma_bulk_predictions.json"
if not bulk.exists(): fail("Bulk missing")
else:
    txt=bulk.read_text(encoding="utf-8")
    if "canonical_name" in txt: fail("canonical_name still in bulk")
    else: ok("No canonical_name leak")
    if "【entity" in txt: fail("entity bracket still in bulk")
    else: ok("No entity bracket leak")
    if "¦" in txt: fail("Broken-bar ¦ still in bulk")
    else: ok("No broken-bar ¦ leak")
    obj=json.loads(txt); rows=obj.get("matches", obj) if isinstance(obj, dict) else obj
    if len(rows) < 842: fail(f"Rows {len(rows)} < 842 - match lost!")
    else: ok(f"Rows preserved {len(rows)}")
    # EGY must be clean
    for r in rows:
        if str(r.get("league","")).upper()=="EGY" or "Ahly" in str(r.get("match","")):
            ok(f"EGY clean: {r.get('match')}")
            break
print("="*50)
if fails: print(f"RESULT: BLOCKED - {len(fails)} FAIL. DO NOT PUSH."); sys.exit(1)
print("RESULT: PASS - safe to push V52")
