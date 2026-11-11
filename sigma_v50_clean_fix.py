#!/usr/bin/env python3
# Sigma V50 CLEAN FIX - removes 5 encoded files that blocked V50 - Mahmoud Emad
# Decodes _x5f_ -> _ , if clean file exists keeps larger, deletes encoded, else renames.
# Never deletes a file without a clean replacement or an existing clean twin.
# Run: python3 sigma_v50_clean_fix.py
import re, json, os
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
def decode(n):
    t=n
    while "_x5f_" in t: t=t.replace("_x5f_","_")
    t=t.replace("_x5f","_")
    # remove (1) style copies: __1_ / _1 before ext, e.g. sigma_v46_final_py__1_ -> handled by caller
    return t
found=[]; cleaned=[]
for p in sorted(BASE.glob("*_x5f_*")):
    if p.is_dir(): continue
    dec=decode(p.name)
    found.append({"encoded":p.name,"decoded":dec,"size":p.stat().st_size})
    target=BASE/dec
    if target.exists() and target!=p:
        # twin exists: keep larger, delete encoded
        if target.stat().st_size >= p.stat().st_size:
            print(f"KEEP clean {dec} ({target.stat().st_size}B) - DELETE encoded {p.name} ({p.stat().st_size}B)")
            p.unlink(); cleaned.append({"action":"delete_duplicate","encoded":p.name,"kept":dec})
        else:
            print(f"REPLACE clean {dec} with larger encoded {p.name}")
            target.unlink(); p.rename(target); cleaned.append({"action":"replace_with_larger","encoded":p.name,"kept":dec})
    else:
        print(f"RENAME {p.name} -> {dec}")
        p.rename(target); cleaned.append({"action":"rename","encoded":p.name,"kept":dec})
print(f"Encoded found: {len(found)}  Cleaned: {len(cleaned)}")
(DATA/"sigma_v50_clean_report.json").write_text(json.dumps({"version":"V50-clean","found":found,"cleaned":cleaned},ensure_ascii=False,indent=1),encoding="utf-8")
print("Wrote data/sigma_v50_clean_report.json")
print("Next: python3 sigma_v50_analyze_fix_v2.py  then  python3 sigma_v50_pre_upload_check_v2.py")
