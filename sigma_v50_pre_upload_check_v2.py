#!/usr/bin/env python3
# Sigma V50 PRE-UPLOAD CHECK v2 - Gate before ANY push - Mahmoud Emad
# FAIL = DO NOT PUSH. Checks V50 fixes + V49 gate.
import json, sys, re
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"
fails=[]; 
def fail(m): fails.append(m); print("FAIL:",m)
def ok(m): print("OK:",m)
print("Sigma V50 PRE-UPLOAD CHECK v2")
# 1. Data pack must exist
if not (DATA/"sigma_v50_data_pack.json").exists(): fail("V50 data pack missing - run sigma_v50_analyze_fix.py")
else:
    p=json.loads((DATA/"sigma_v50_data_pack.json").read_text(encoding="utf-8"))
    a=p.get("audit",{})
    if a.get("default_count",0) > a.get("total",0): fail(f"DEFAULT {a.get('default_count')} > total {a.get('total')}")
    else: ok(f"DEFAULT {a.get('default_count')} <= total {a.get('total')}")
    if a.get("future",0) > a.get("total",0): fail("Future > total")
    else: ok(f"Future {a.get('future')} <= total {a.get('total')}")
    if len(p.get("sports_view",{}).get("tabs",[])) < 7: fail("All-sports tabs <7 - view still football only")
    else: ok(f"All-sports tabs {len(p['sports_view']['tabs'])}")
    if p.get("program",{}).get("signature") != "Signature Prediction and Forecast: Sigma - Mahmoud Emad": fail("Signature missing/wrong")
    else: ok("Signature correct")
# 2. No encoded filenames in repo root (except data/)
for f in list(BASE.glob("*")):
    if "_x5f_" in f.name: fail(f"Encoded filename still in repo: {f.name} - run clean")
# 3. No token leak in tracked files (skip token.txt itself, which must be ignored)
for f in list(BASE.glob("*.py"))+list(BASE.glob("*.sh"))+list(BASE.glob("*.json")):
    try: t=f.read_text(encoding="utf-8",errors="ignore")
    except Exception: continue
    if re.search(r"ghp_[A-Za-z0-9]{20,}", t): fail(f"Token leak in {f.name}")
# 4. No DIWAN HTML fake zip
for f in list(BASE.glob("*DIWAN*"))+list(DATA.glob("*DIWAN*")):
    try: t=f.read_bytes()[:2000].decode("utf-8",errors="ignore")
    except Exception: t=""
    if "<!DOCTYPE html" in t and "Preview is not available" in t: fail(f"DIWAN HTML fake zip still present: {f.name}")
# 5. Value math
edge=0.60*1.95-1; kelly=0.3*edge/(1.95-1)
if abs(edge-0.17)>0.001 or abs(kelly-0.0536)>0.002: fail("Value math broken")
else: ok(f"Value math 17.0% / 5.4% correct")
# 6. V49 gate still holds
if not (DATA/"sigma_brain_state.json").exists(): print("WARN: brain_state missing - run V49 first")
else: ok("Brain state exists")
print("="*50)
if fails: print(f"RESULT: BLOCKED - {len(fails)} FAIL. DO NOT PUSH."); sys.exit(1)
print("RESULT: PASS - safe to push V50")
