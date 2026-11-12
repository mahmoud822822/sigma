#!/usr/bin/env python3
# Sigma V53 - REMOVE FAKE manual matches - Mahmoud Emad
# VERIFIED (web, Nov 2026):
# - Al Ahly vs Zamalek real derby: 11 Oct 2026 (MD6), Zamalek 0-2 Al Ahly. Next: Al Ahly vs Pyramids 23 Nov, Zamalek vs El Gouna 23 Nov. NO Al Ahly vs Zamalek 15 Nov.
# - Al Hilal vs Al Nassr real: 10 Dec 2026 (MD17) / Jan 1 2027 update. NOT Nov.
# Rule: Any EGY/SAU manual with unverified date -> QUARANTINE, not shown as real.
import json, shutil
from pathlib import Path
BASE = Path(__file__).parent; DATA = BASE / "data"
BULK = DATA / "sigma_bulk_predictions.json"
FAKE_REASONS = {
  "Al Ahly vs Zamalek|2026-11-15": "FAKE: Real derby 11 Oct 2026 (0-2), next fixtures 23 Nov vs Pyramids/Gouna. No derby 15 Nov. Source: english.ahram.org.eg + sportradar.com",
}
def is_fake(r):
    m = str(r.get("match","")).strip()
    d = str(r.get("date","")).strip()
    lg = str(r.get("league","")).upper()
    # 1. Exact fake EGY Nov 15
    if m=="Al Ahly vs Zamalek" and d in ("2026-11-15","Nov 15","15 Nov"):
        return FAKE_REASONS["Al Ahly vs Zamalek|2026-11-15"]
    # 2. Any Al Ahly vs Zamalek NOT on 11 Oct 2026 (only verified derby date in 2026-27)
    if m=="Al Ahly vs Zamalek" and d not in ("2026-10-11","2026-10-11T18:00:00"):
        return f"FAKE: Al Ahly vs Zamalek only verified 11 Oct 2026, got {d}. Source: ahram + sportradar"
    # 3. Al Hilal vs Al Nassr NOT on verified dates
    if set([str(r.get("home_team","")), str(r.get("away_team",""))])=={"Al Hilal","Al Nassr"} or m in ("Al Hilal vs Al Nassr","Al Nassr vs Al Hilal"):
        if d not in ("2026-12-10","2027-01-01","2026-12-09","2026-12-31","2027-01-02"):
            return f"FAKE: Hilal vs Nassr verified 10 Dec 2026 / 1 Jan 2027, got {d}. Source: sportradar + yardbarker"
    # 4. Any EGY/SAU manual with no source_detail URL and is_default=1 and Form unknown (synthetic)
    if lg in ("EGY","SAU") and str(r.get("source_detail",""))=="" and str(r.get("is_default",""))=="1" and "unknown" in str(r.get("form_trend","")).lower():
        # Only quarantine if it is also one of the known manual teams (avoid deleting real API rows that happen to have this)
        if any(t in m for t in ["Al Ahly","Zamalek","Al Hilal","Al Nassr"]):
            return "FAKE-UNVERIFIED: EGY/SAU manual, no source URL, is_default=1, Form unknown - no verified fixture"
    return None
def main():
    if not BULK.exists(): print("MISSING bulk"); return
    bak = DATA / "sigma_bulk_predictions.backup_before_v53.json"
    if not bak.exists(): shutil.copy(BULK, bak)
    obj = json.loads(BULK.read_text(encoding="utf-8"))
    rows = obj.get("matches", obj) if isinstance(obj, dict) else obj
    kept=[]; removed=[]
    for r in rows:
        reason = is_fake(r)
        if reason:
            removed.append({**r, "_v53_reason": reason, "_v53_sources": ["https://english.ahram.org.eg/NewsContentP/6/32/557833.aspx","https://www.sportradar.com/"]})
        else:
            kept.append(r)
    print(f"Before: {len(rows)} | Removed fake: {len(removed)} | After: {len(kept)}")
    for x in removed: print(f"  REMOVED: {x.get('match')} | {x.get('date')} | {x.get('league')} | {x.get('_v53_reason')[:110]}")
    # Save quarantine (not deleted forever - audit trail)
    (DATA/"sigma_quarantine_fake_v53.json").write_text(json.dumps({"removed":removed,"count":len(removed),"rule":"Manual without verified date/source -> quarantine"}, ensure_ascii=False, indent=1), encoding="utf-8")
    # Save clean bulk - keep same structure
    if isinstance(obj, dict): obj["matches"]=kept; obj["total"]=len(kept)
    else: obj=kept
    BULK.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    # Update V53 pack
    pack={"version":"V53","removed_fake":len(removed),"total_before":len(rows),"total_after":len(kept),"shown_after":len(kept)-13 if len(kept)>=842 else len(kept),"quarantine_file":"data/sigma_quarantine_fake_v53.json","rule":"No manual without source URL + verified date"}
    (DATA/"sigma_v53_data_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved clean bulk {len(kept)} + quarantine {len(removed)} + pack")
if __name__=="__main__": main()
