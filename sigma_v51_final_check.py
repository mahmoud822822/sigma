#!/usr/bin/env python3
# Sigma V51 FINAL CHECK v4 - Gate before push
import json, sys, re
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"
fails=[]
def fail(m): fails.append(m); print("FAIL:",m)
def ok(m): print("OK:",m)
print("Sigma V51 FINAL CHECK v4")
if not (DATA/"sigma_v51_data_pack.json").exists(): fail("V51 pack missing - run sigma_v51_final.py")
else:
    p=json.loads((DATA/"sigma_v51_data_pack.json").read_text(encoding="utf-8"))
    fb=p.get("football",{}); bb=p.get("basketball",{})
    if fb.get("total",0) < 842: fail(f"Football total {fb.get('total')} < 842 - match lost!")
    else: ok(f"Football preserved {fb['total']} shown {fb.get('shown')}")
    if fb.get("golden",0)==0: fail("Golden 0 again - fix logic, do not push")
    else: ok(f"Golden {fb['golden']}")
    if fb.get("default",0) < 0: fail("DEFAULT negative")
    else: ok(f"DEFAULT {fb.get('default')} (is_default=1 count)")
    if bb.get("fake_predictions",0)>0: fail("Basketball fake")
    else: ok(f"Basketball {bb.get('total')} {bb.get('status')}")
    if not (DATA/"sigma_delta_old_new.json").exists(): fail("Delta missing")
    else: ok("Delta old/new exists")
    if p.get("feed",{}).get("new_verified_added",-1)!=0: fail("Feed invented")
    else: ok("Feed 0 invented")
    if p.get("program",{}).get("signature")!="Signature Prediction and Forecast: Sigma - Mahmoud Emad": fail("Signature wrong")
    else: ok("Signature correct")
for f in list(BASE.glob("*")):
    if "_x5f_" in f.name: fail(f"Encoded {f.name}")
for f in list(BASE.glob("*.py"))+list(BASE.glob("*.sh")):
    try: t=f.read_text(encoding="utf-8",errors="ignore")
    except Exception: continue
    if re.search(r"ghp_[A-Za-z0-9]{20,}", t): fail(f"Token leak {f.name}")
print("="*50)
if fails: print(f"RESULT: BLOCKED - {len(fails)} FAIL. DO NOT PUSH."); sys.exit(1)
print("RESULT: PASS - safe to push V51 FINAL")
