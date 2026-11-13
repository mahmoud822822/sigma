#!/usr/bin/env python3
# Sigma V71 - HISTORY BACKTEST (real) - uses sigma_history.csv (100788) + sigma_real_verified.csv (14)
# V70 looked for sigma_history*.jsonl -> found only 2 rows. V71 fixes: reads .csv
# History has NO conf, so calibration vs conf is NOT possible - we report base rates instead, no invention.
import json, csv, pathlib, collections
from datetime import date
BASE=pathlib.Path(__file__).resolve().parent; DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
VERSION="V71"; TODAY=str(date(2026,11,13))
def load_bulk():
    p=DATA/"sigma_bulk_predictions.json"
    if not p.exists(): return []
    o=json.loads(p.read_text(encoding="utf-8")); return o if isinstance(o,list) else o.get("matches",[])
def main():
    print("="*62); print(f"Sigma {VERSION} - HISTORY BACKTEST (real) - 100788 + 14 verified"); print("="*62)
    bulk=load_bulk(); print(f"[BULK] rows={len(bulk)} (expect ~839)")
    if len(bulk)<500: print("[GATE] Bulk <500 -> BLOCKED"); return
    # --- HISTORY CSV ---
    hp=DATA/"sigma_history.csv"
    if not hp.exists():
        print("[HISTORY] NO CONFIRMED DATA - data/sigma_history.csv not found -> ABSTAIN"); return
    hist=list(csv.DictReader(open(hp,encoding="utf-8")))
    print(f"[HISTORY] rows={len(hist)} (wc -l should be {len(hist)+1})")
    # Base rates from REAL history, no conf invented
    hw=dr=aw=0; goals=0; btts=0; over25=0; valid=0
    leagues=collections.Counter()
    for r in hist:
        try:
            hg=int(float(r.get("home_goals") or r.get("homeGoals") or 0)); ag=int(float(r.get("away_goals") or r.get("awayGoals") or 0))
        except: continue
        valid+=1; goals+=hg+ag
        if hg>ag: hw+=1
        elif hg==ag: dr+=1
        else: aw+=1
        if hg>0 and ag>0: btts+=1
        if hg+ag>2: over25+=1
        leagues[r.get("league") or r.get("competition") or "Default"]+=1
    print(f"[HISTORY BASE RATES] valid={valid}")
    print(f"  Home win: {hw/valid*100:.1f}% ({hw}) | Draw: {dr/valid*100:.1f}% ({dr}) | Away win: {aw/valid*100:.1f}% ({aw})")
    print(f"  Avg goals: {goals/valid:.2f} | BTTS: {btts/valid*100:.1f}% | Over 2.5: {over25/valid*100:.1f}%")
    print(f"  Top leagues: {leagues.most_common(5)}")
    print("  Note: History has NO conf -> cannot do conf-vs-hit calibration. Base rates are the prior.")
    # --- REAL VERIFIED 14 ---
    vp=DATA/"sigma_real_verified.csv"
    vtot=vhit=0
    if vp.exists():
        for r in csv.DictReader(open(vp,encoding="utf-8")):
            res=str(r.get("bet_result") or "").lower()
            if res in ("correct","incorrect"):
                vtot+=1
                if res=="correct": vhit+=1
        print(f"\n[REAL VERIFIED] rows={vtot} hit={vhit} rate={vhit/vtot*100:.1f}% (if vtot>0)")
        print("  This is the only conf/bet history with result - 14 bets, not 100k.")
    else:
        print("\n[REAL VERIFIED] not found")
    # --- CALIBRATION CONCLUSION ---
    print("\n[CALIBRATION V71]")
    print("  V50 87.9 / Elo 1500 / base>=90 rules from V69 stay - History base rates do NOT justify 90%+.")
    print("  If Sigma says 70% but base home-win is ~45%, need Elo + form proof, not base rate alone.")
    print("  HYPE_TRAP rule V70 stays: HYPE alone -7 KEEP, HYPE+other -> NO SAFE BET.")
    out={"version":VERSION,"date":TODAY,"bulk_rows":len(bulk),"history_rows":len(hist),"history_valid":valid,"base_rates":{"home_win":round(hw/valid*100,1) if valid else None,"draw":round(dr/valid*100,1) if valid else None,"away_win":round(aw/valid*100,1) if valid else None,"avg_goals":round(goals/valid,2) if valid else None,"btts":round(btts/valid*100,1) if valid else None,"over25":round(over25/valid*100,1) if valid else None},"real_verified":{"n":vtot,"hits":vhit,"rate":round(vhit/vtot*100,1) if vtot else None},"note":"History has no conf - no conf-vs-hit calibration invented"}
    (DATA/"sigma_v71_report.json").write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding="utf-8")
    print("\nDONE. Report: data/sigma_v71_report.json")
if __name__=="__main__": main()
