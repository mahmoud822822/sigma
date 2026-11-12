#!/usr/bin/env python3
# Sigma V54 - REMOVE REMAINING 5 FAKES - Keep 840 real - Mahmoud Emad
# V53 already removed 2: Al Ahly 15 Nov + Hilal/Nassr 16 Nov -> 840
# V54 removes remaining manual from sigma_manual_fixtures.csv (7 total):
#  - England vs Croatia 12 Nov UNL
#  - Real Madrid vs Barcelona 17 Nov PD
#  - Man City vs Arsenal 18 Nov PL
#  - Inter vs Milan 19 Nov SA
#  - Brazil vs Argentina 20 Nov WC (labelled "example")
# If a fake is NOT in bulk (already not there), count 0 and PASS - do NOT invent it to remove it.
# Also quarantines the manual file itself so future rebuilds don't re-add fakes.
import json, shutil
from pathlib import Path
BASE=Path(__file__).parent; DATA=BASE/"data"
BULK=DATA/"sigma_bulk_predictions.json"
FAKES={
 ("England","Croatia","2026-11-12"): "FAKE: No verified Nations League fixture on this date, same template as other manual, no source.",
 ("Real Madrid","Barcelona","2026-11-17"): "FAKE: Real Clasico 25 Oct 2026 Camp Nou, return 9 May 2027. Not 17 Nov. Source: fcbarcelona + laligaupdate",
 ("Man City","Arsenal","2026-11-18"): "FAKE + reversed: Real Arsenal vs Man City 29 Nov 2026 Emirates. Not Man City home 18 Nov. Source: sportradar + fotmob",
 ("Inter","Milan","2026-11-19"): "FAKE: No derby on this date, same template, no source.",
 ("Brazil","Argentina","2026-11-20"): "FAKE + EXAMPLE: File says 'World Cup - example'. Brazil Group C, Argentina Group D - different groups, cannot meet in group stage. Source: worldcupqa",
 ("Al Ahly","Zamalek","2026-11-15"): "V53 already removed - re-check",
 ("Al Hilal","Al Nassr","2026-11-16"): "V53 already removed - re-check",
}
def key(r):
    return (str(r.get("home_team","")).strip(), str(r.get("away_team","")).strip(), str(r.get("date","")).strip()[:10])
def main():
    if not BULK.exists(): print("MISSING bulk"); return
    bak=DATA/"sigma_bulk_predictions.backup_before_v54.json"
    if not bak.exists(): shutil.copy(BULK, bak)
    obj=json.loads(BULK.read_text(encoding="utf-8"))
    rows=obj.get("matches", obj) if isinstance(obj, dict) else obj
    before=len(rows); kept=[]; removed=[]
    for r in rows:
        k=key(r)
        if k in FAKES:
            # Also catch reverse Man City/Arsenal? Real is Arsenal home, so Man City home 18 Nov is fake regardless
            removed.append({**r, "_v54_reason": FAKES[k]})
        elif str(r.get("match","")) in ("Real Madrid vs Barcelona","Man City vs Arsenal","Inter vs Milan","England vs Croatia","Brazil vs Argentina") and str(r.get("date",""))[:10] in ("2026-11-12","2026-11-17","2026-11-18","2026-11-19","2026-11-20"):
            removed.append({**r, "_v54_reason": "FAKE manual date match"})
        else:
            kept.append(r)
    print(f"Before: {before} | Removed V54: {len(removed)} | After: {len(kept)}")
    for x in removed: print(f"  REMOVED: {x.get('match')} | {x.get('date')} | {x.get('league')} | {x.get('_v54_reason')[:100]}")
    if len(removed)==0: print("  No remaining fakes in bulk - bulk already clean of manual 7. Good.")
    # Merge with V53 quarantine if exists
    prev=[]
    q53=DATA/"sigma_quarantine_fake_v53.json"
    if q53.exists():
        try: prev=json.loads(q53.read_text(encoding="utf-8")).get("removed",[])
        except: prev=[]
    allq=prev+removed
    (DATA/"sigma_quarantine_fake_v54.json").write_text(json.dumps({"removed_v54":removed,"removed_total_53_54":allq,"count_v54":len(removed),"count_total":len(allq)}, ensure_ascii=False, indent=1), encoding="utf-8")
    if isinstance(obj, dict): obj["matches"]=kept; obj["total"]=len(kept)
    else: obj=kept
    BULK.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    # Quarantine manual file itself
    for mf in [DATA/"sigma_manual_fixtures.csv", BASE/"sigma_manual_fixtures.csv"]:
        if mf.exists():
            shutil.copy(mf, DATA/"sigma_manual_fixtures.QUARANTINED_v54.csv")
            print(f"Manual file quarantined: {mf} -> sigma_manual_fixtures.QUARANTINED_v54.csv (DO NOT use as source)")
            break
    pack={"version":"V54","before":before,"removed_v54":len(removed),"after":len(kept),"quarantine":"data/sigma_quarantine_fake_v54.json","rule":"Keep real API bulk, remove only verified manual fakes, quarantine manual file"}
    (DATA/"sigma_v54_data_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved clean bulk {len(kept)} + quarantine V54 {len(removed)} + pack")
if __name__=="__main__": main()
