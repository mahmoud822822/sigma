#!/usr/bin/env python3
# Sigma V52 - Fix entity-tag leak in team names - Mahmoud Emad
# BUG in screenshot: "Al Ahly¦canonical_name=Al Ahly" - V47 regex only handled | pipe, not ¦ broken-bar, and only with brackets.
# This fixes BOTH: with brackets 【entity-...¦...】 and bare "Name¦canonical_name=Name" and pipe version.
# NEVER deletes matches. Only cleans names. Backs up bulk first.
import json, re, shutil
from pathlib import Path
BASE = Path(__file__).parent; DATA = BASE / "data"
BULK = DATA / "sigma_bulk_predictions.json"
def clean_name(s):
    if not isinstance(s, str): return s
    # If it's a "A vs B" match, clean each side separately or we truncate at first leak
    if " vs " in s:
        parts = s.split(" vs ")
        return " vs ".join(clean_name(p) for p in parts)
    t = s
    # 1. Full bracket form with ¦ or | : 【entity-Al Ahly¦canonical_name=Al Ahly】 -> Al Ahly
    t = re.sub(r"【entity-[^】]*?[¦|]canonical_name=([^】]+)】", r"\1", t)
    # 2. Full bracket form without canonical: 【entity-Al Ahly】 -> Al Ahly
    t = re.sub(r"【entity-([^】¦|]+)(?:[¦|][^】]*)?】", r"\1", t)
    # 3. Bare form (screenshot): "Al Ahly¦canonical_name=Al Ahly" -> "Al Ahly"
    t = re.sub(r"^(.+?)[¦|]canonical_name=.+$", r"\1", t.strip())
    # 4. Any leftover ¦canonical_name=... or |canonical_name=...
    t = re.sub(r"[¦|]canonical_name=[^¦|】]*", "", t)
    # 5. Any leftover 【entity- / 】 markers
    t = re.sub(r"【entity-", "", t); t = t.replace("】","")
    return re.sub(r"\s+", " ", t).strip()
def main():
    if not BULK.exists():
        print("MISSING bulk - STOP"); return
    # Backup
    bak = DATA / "sigma_bulk_predictions.backup_before_v52.json"
    if not bak.exists(): shutil.copy(BULK, bak)
    obj = json.loads(BULK.read_text(encoding="utf-8"))
    rows = obj.get("matches", obj) if isinstance(obj, dict) else obj
    fixed = 0; examples = []
    for r in rows:
        for k in ["home_team","away_team","match","league","competition","country"]:
            if k in r and isinstance(r.get(k), str):
                c = clean_name(r[k])
                if c != r[k]:
                    if len(examples)<5: examples.append(f"{r[k]} -> {c}")
                    r[k]=c; fixed+=1
        # Rebuild match from cleaned home/away if match was polluted
        if r.get("home_team") and r.get("away_team"):
            want = f"{r['home_team']} vs {r['away_team']}"
            if r.get("match") != want and "vs" in str(r.get("match","")):
                # Only rebuild if old match contained canonical or ¦ - already cleaned, keep as is if equal after clean
                pass
    # Verify no leak left
    txt = json.dumps(obj, ensure_ascii=False)
    left = txt.count("canonical_name") + txt.count("【entity")
    print(f"Cleaned fields: {fixed}")
    for e in examples: print(f"  {e}")
    print(f"Remaining canonical_name/entity leaks: {left}")
    if left>0:
        print("BLOCKED - leak still present, NOT saving"); return
    BULK.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved clean bulk. Backup: {bak.name} | Total rows: {len(rows)} - no match deleted")
if __name__=="__main__": main()
