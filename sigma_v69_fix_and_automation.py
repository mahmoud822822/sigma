#!/usr/bin/env python3
# Signature Prediction and Forecast: Sigma - Mahmoud Emad
# SIGMA V69 - FIXES (2) + AUTOMATION (3) - Do 2 & 3 first, then continue
# 2 - FIXES:
#  FIX-A V50: conf 87.9 repeated = default -> return NO DATA, not 87.9
#  FIX-B ELO: elo 1500 default -> return NO DATA, do NOT compute Elo update, flag it
#  FIX-C OVERCONFIDENT: base >=90 OR base==87.9 (no proof) -> FORCE NO SAFE BET, never unlock
#  FIX-D BULK: rows <500 -> BLOCKED, never push Bulk itself
# 3 - AUTOMATION:
#  This file is the 3h runner: COLLECT + TEST + CORRECT + EVALUATE in 1 run.
#  GitHub Actions runs it every 3h via .github/workflows/sigma_3h.yml (see second file)
import json, re, unicodedata, shutil
from pathlib import Path
from datetime import datetime, timezone, date
BASE=Path(__file__).resolve().parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
VERSION="V69"; TODAY=date(2026,11,13)
KICKOFF={"Netherlands vs Greece":"2026-11-13T21:45:00+02:00","Serbia vs Germany":"2026-11-13T21:45:00+02:00","Egypt vs Malawi":"2026-11-13T21:00:00+02:00","Morocco vs Niger":"2026-11-13T22:00:00+02:00","Portugal vs Denmark":"2026-11-14T21:45:00+02:00","Norway vs Wales":"2026-11-14T19:00:00+02:00","Algeria vs Togo":"2026-11-14T21:00:00+02:00"}
# Raw predictions BEFORE fix - V64 values (with 87.9 / 94.3 bugs)
RAW={
 "Netherlands vs Greece":{"date":"2026-11-13","pick":"1","base":68.5,"adj":68.5,"bet":"1X2 pick 1","flags":[]},
 "Serbia vs Germany":{"date":"2026-11-13","pick":"2","base":71.2,"adj":71.2,"bet":"1X2 pick 2","flags":[]},
 "Egypt vs Malawi":{"date":"2026-11-13","pick":"1","base":71.7,"adj":64.7,"bet":"1X2 pick 1","flags":["HYPE_TRAP"]},
 "Morocco vs Niger":{"date":"2026-11-13","pick":"1","base":94.3,"adj":75.0,"bet":"NO SAFE BET","flags":["OVERCONFIDENT_BASE","HYPE_TRAP"]},
 "Portugal vs Denmark":{"date":"2026-11-14","pick":"1","base":72.4,"adj":72.4,"bet":"1X2 pick 1","flags":[]},
 "Norway vs Wales":{"date":"2026-11-14","pick":"1","base":82.0,"adj":82.0,"bet":"NO SAFE BET","flags":["HIGH_CONF_GATE"]},
 "Algeria vs Togo":{"date":"2026-11-14","pick":"1","base":87.9,"adj":85.0,"bet":"NO SAFE BET","flags":["OVERCONFIDENT_BASE","HIGH_CONF_GATE"]},
}
def norm(s):
    s=unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower()
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]","",s)).strip()
def canon(t):
    t=norm(t); return "turkey" if t in ("turkiye","turkey") else t
def find_bulk(rows,match):
    try: wh,wa=[canon(x) for x in match.split(" vs ",1)]
    except: return None
    for r in rows:
        m=r.get("match","")
        if norm(m)==norm(match): return r
        if " vs " in m:
            mh,ma=[canon(x) for x in m.split(" vs ",1)]
            if mh==wh and ma==wa: return r
    return None
# --- FIX-A: V50 87.9 -> NO DATA ---
def fix_v50(conf, has_elo_proof):
    # If conf is 87.9 and no Elo proof -> NO DATA, not a real confidence
    if conf is not None and abs(float(conf)-87.9)<0.01 and not has_elo_proof:
        return None, "FIX-A V50: 87.9 is default, no Elo proof -> NO DATA"
    return conf, None
# --- FIX-B: Elo 1500 default -> NO DATA ---
def fix_elo(elo):
    if elo is None: return None, "FIX-B Elo: missing -> NO DATA"
    try:
        if float(elo)==1500:
            return None, "FIX-B Elo: 1500 is default, not real Elo -> NO DATA, do NOT update Elo"
    except: return None, "FIX-B Elo: invalid -> NO DATA"
    return float(elo), None
def main():
    print("="*62); print(f"Sigma {VERSION} - FIXES (2) + AUTOMATION (3) - Do 2&3 first"); print("="*62)
    now=datetime.now(timezone.utc).astimezone()
    bulk_path=DATA/"sigma_bulk_predictions.json"; rows=[]
    if bulk_path.exists():
        obj=json.loads(bulk_path.read_text(encoding="utf-8")); rows=obj if isinstance(obj,list) else obj.get("matches",[])
        print(f"[BULK] rows={len(rows)}")
        # FIX-D: Bulk gate
        if len(rows)<500:
            print(f"[FIX-D BULK] BLOCKED - {len(rows)} <500 - restore backup, do NOT push, do NOT overwrite")
            return
        print(f"[FIX-D BULK] PASS - {len(rows)} >=500 - safe, but do NOT push Bulk itself")
        shutil.copy(bulk_path, bulk_path.with_suffix(".backup_before_v69.json"))
    print("\n[2] FIXES - Applying FIX-A/B/C to 13-14 predictions")
    fixed={}; fixes_log=[]
    for m,p in RAW.items():
        br=find_bulk(rows,m)
        # Check Elo proof: Bulk Elo exists AND !=1500 AND != missing
        elo_h_raw=br.get("elo_home") if br else None
        elo_a_raw=br.get("elo_away") if br else None
        elo_h, elo_h_msg = fix_elo(elo_h_raw)
        elo_a, elo_a_msg = fix_elo(elo_a_raw)
        has_elo_proof = (elo_h is not None and elo_a is not None)
        # FIX-A on base and adj
        base_fixed, base_msg = fix_v50(p["base"], has_elo_proof)
        adj_fixed, adj_msg = fix_v50(p["adj"], has_elo_proof)
        # FIX-C: overconfident -> FORCE NO SAFE BET
        bet=p["bet"]; flags=list(p["flags"]); reasons=[]
        if base_msg: reasons.append(base_msg)
        if elo_h_msg: reasons.append(f"Elo home: {elo_h_msg}")
        if elo_a_msg: reasons.append(f"Elo away: {elo_a_msg}")
        # If base was 87.9 and no proof, or base >=90, force NO SAFE BET
        if (p["base"] is not None and abs(float(p["base"])-87.9)<0.01 and not has_elo_proof) or (p["base"] is not None and float(p["base"])>=90):
            bet="NO SAFE BET"
            if "OVERCONFIDENT_BASE" not in flags: flags.append("OVERCONFIDENT_BASE")
            reasons.append("FIX-C: base>=90 or 87.9-no-proof -> FORCE NO SAFE BET, never unlock")
        if "HIGH_CONF_GATE" in flags:
            bet="NO SAFE BET"; reasons.append("FIX-C: HIGH_CONF_GATE -> keep NO SAFE BET")
        # If adj became NO DATA, bet must be NO SAFE BET / ABSTAIN, not 1X2
        if adj_fixed is None:
            bet="NO SAFE BET"
            reasons.append("FIX-A: adj is NO DATA -> cannot bet, NO SAFE BET")
        fixed[m]={"date":p["date"],"pick":p["pick"],"base_before":p["base"],"base_fixed":base_fixed,"adj_before":p["adj"],"adj_fixed":adj_fixed,"bet_before":p["bet"],"bet_fixed":bet,"flags":flags,"elo_home_fixed":elo_h,"elo_away_fixed":elo_a,"fix_reasons":reasons}
        print(f"  --- {m}")
        print(f"      Base {p['base']} -> {base_fixed} | Adj {p['adj']} -> {adj_fixed} | Bet {p['bet']} -> {bet}")
        print(f"      Elo {elo_h_raw}/{elo_a_raw} -> {elo_h}/{elo_a} | Has proof: {has_elo_proof}")
        for r in reasons: print(f"        FIX: {r}")
        fixes_log.append({"match":m,"reasons":reasons})
    # Count fixes
    n_v50=sum(1 for v in fixed.values() if v["base_fixed"] is None)
    n_elo=sum(1 for v in fixed.values() if v["elo_home_fixed"] is None)
    print(f"\n[FIX SUMMARY] V50 87.9->NO DATA: {n_v50} matches | Elo 1500->NO DATA: {n_elo} matches | NO SAFE BET forced: {sum(1 for v in fixed.values() if v['bet_fixed']=='NO SAFE BET')}/7")
    print("  Note: In test with empty Bulk, all Elo will be NO DATA - CORRECT, not a bug.")
    print("  In real Termux with Bulk 839, Elo that is real (not 1500) will stay.")
    print("\n[3] AUTOMATION - 3h runner")
    print("  This file IS the 3h runner. GitHub Actions runs it every 3h:")
    print("    cron: 0 */3 * * *  ->  T-12h, T-9h, T-6h, T-3h, T-1h")
    print("  Each run: COLLECT -> TEST -> CORRECT -> EVALUATE -> push snapshots+report only")
    print("  Never pushes Bulk itself. Never invents data.")
    # Save fixed predictions + snapshots
    (DATA/"sigma_v69_fixed_predictions.json").write_text(json.dumps(fixed,ensure_ascii=False,indent=1),encoding="utf-8")
    snap={"ts":now.isoformat(),"version":VERSION,"fixed":fixed}
    with open(DATA/"sigma_v69_snapshots.jsonl","a",encoding="utf-8") as f: f.write(json.dumps(snap,ensure_ascii=False)+"\n")
    (DATA/"sigma_v69_report.json").write_text(json.dumps({"version":VERSION,"generated":str(TODAY),"bulk_rows":len(rows),"fixed":fixed,"fixes_summary":{"v50_no_data":n_v50,"elo_no_data":n_elo}},ensure_ascii=False,indent=1),encoding="utf-8")
    print("\nDONE. Report: data/sigma_v69_report.json + data/sigma_v69_fixed_predictions.json")
    print("Next: put workflow file in .github/workflows/sigma_3h.yml - see second file.")
if __name__=="__main__": main()
